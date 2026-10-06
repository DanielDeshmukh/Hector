import logging
import os
import re
from typing import Any

from utils.retry import retry

from groq import Groq
from dotenv import load_dotenv

from core.precedent import CITATION_PATTERNS

logger = logging.getLogger(__name__)

load_dotenv()


# ---------------------------------------------------------------------------
# Sentence scope, normalization, and abstention helpers (Round 2)
# ---------------------------------------------------------------------------

# Narrow no-break space / NBSP / thin space appear in NIM output and break
# exact substring verification against corpus text. Lengths are preserved
# (1:1 replacement) so spans computed here stay valid on the original string.
def normalize_spaces(text: str) -> str:
    return (text or "").replace("\u202f", " ").replace("\u00a0", " ").replace(
        "\u2009", " "
    )


# Sentence boundaries: terminal punctuation + newlines. Colons deliberately
# NOT split (markdown headings like "**Practical implication:**" would else
# become separate "substantive" fragments).
_SENTENCE_SPLIT = re.compile(r"(?<=[.;!?])\s+|\n+")

# Source-absence / refusal phrasings. A sentence whose clause carries a
# marker is an abstention statement (unless another clause makes an
# assertive legal claim — Round 5 clause-level scoping): its citations are
# negated and its text must not be counted as an assertive claim
# (tasks 1/2/3/7).
ABSTENTION_MARKERS = (
    "i cannot find this information",
    "cannot find this information",
    "i cannot answer",
    "i can't answer",
    "i do not know",
    "i don't know",
    "does not contain",
    "do not contain",
    "no authoritative source",
    "knowledge base does not",
    "not able to find",
    "unable to answer",
    "do not have access",
    "don't have access",
    "i'm sorry",
    "could not find sufficiently relevant sources",
    "not generating an answer",
    # Round 2: absence phrasings observed in live probe answers
    "could not find",
    "unable to find",
    "cannot explain",
    "does not mention",
    "do not mention",
    "none mention",
    "none mentions",
    "no mention",
    "does not include",
    "do not include",
    "sources lack",
    "lack sufficient",
    "not provided",
    "no statutory text",
    "missing provision",
    "nothing to compare",
    "cannot be made",
    "is absent",
    "are absent",
    "i cannot provide",
    "cannot be answered",
    "rephrase",
    "clarify your query",
    "additional legal texts",
    # Round 4: phrasings observed in round-3 refusal-shaped answers
    "not stated",
    "do not list",
    "does not list",
    "does not enumerate",
    "no text to",
    "cannot be determined",
    "none of source",
    "none of the source",
    "none of which",
    "nor do they",
    # BNS run B (2026-10-04): absence phrasings observed in live answers that
    # matched no marker, so their section mention scored assertive + ungrounded
    # instead of negated (matcher fixes, thresholds unchanged):
    #   bns-356-b "No text of the corresponding IPC section (Section 499) is
    #              provided."            -> contextual (sentence carries "provided")
    #   bns-353-b "no text of the corresponding Indian Penal Code section
    #              (IPC §505) is provided."
    #   bns-19-b  "the corresponding IPC provision (Section 81) is not
    #              included."            -> literal keeps the trailing period so
    #              "… not included in the Schedule" (a legal assertion) stays
    #              assertive
    #   bns-2-a   "I cannot describe how the BNS deals with definitions."
    #              (mirrors the existing unconditional "cannot explain")
    "no text of",
    "is not included.",
    "are not included.",
    "cannot describe",
)

# Round 5, task 3: markers that only signal source/answer absence when the
# sentence is about the sources/answer, not the law itself.  In normal legal
# text ("Section 106 does not include abetment", "the fine is not provided")
# these are assertions to verify, not refusals — so they count as
# abstention only when the sentence carries a source/answer context word.
CONTEXTUAL_MARKERS = frozenset(
    {
        "does not contain",
        "do not contain",
        "does not include",
        "do not include",
        "does not mention",
        "do not mention",
        "none mention",
        "none mentions",
        "no mention",
        "lack sufficient",
        "not provided",
        "no statutory text",
        "missing provision",
        "nothing to compare",
        "cannot be made",
        "is absent",
        "are absent",
        "not stated",
        "do not list",
        "does not list",
        "does not enumerate",
        "cannot be determined",
        "none of which",
        "nor do they",
        # Round 6 (2026-10-03): source-absence phrasings observed in live
        # iter2 answers that matched no marker, so their section mention was
        # scored assertive + ungrounded instead of negated:
        #   "- **Section 125** (not in sources): Waging war ..."
        #   "The retrieved sources cover Sections 225B, 216, 201 ... but not
        #    Section 275."
        # Both stay gated on _SOURCE_CONTEXT, so ordinary legal prose that
        # merely happens to contain the words is unaffected.
        "not in sources",
        "but not section",
        # iter4 (2026-10-03): the phrase "…whose text is not in the retrieved
        # sources" put "the retrieved" between "not in" and "sources", so the
        # Round 6 marker never matched and an honest abstention scored as
        # assertive + ungrounded (observed on ipc-313-b). Still gated on
        # _SOURCE_CONTEXT.
        "not in the retrieved sources",
        "not in the sources",
        "not in retrieved sources",
        "is not in the retrieved",
        # BNS run B (2026-10-04): "No text of the corresponding … section is
        # provided" is a source-absence statement, but only becomes one when
        # the sentence is about the sources — hence contextual, not
        # unconditional.  Still gated on _SOURCE_CONTEXT.
        "no text of",
    }
)

# Words that place a sentence in the sources/answer frame (Round 5, task 3).
_SOURCE_CONTEXT = re.compile(
    r"\b(sources?|context|documents?|texts?|corpus|retrieval|retrieved|"
    r"knowledge|indexed|loaded|answers?|quer(?:y|ies)|responses?|provided|"
    r"given|materials?|here|above|below|herein|aforesaid)\b",
    re.IGNORECASE,
)

# Absence statements whose wording defeats every substring marker.  BNS run B
# (2026-10-04), bns-2-a: "Since no definitions section (such as a Section 2
# or equivalent) appears in the provided sources, I cannot describe how the
# BNS deals with definitions." — the mention sits in the *first* clause, and
# the words between "no" and "appears" push every plain marker out of reach.
# The leading "no" plus the "in the provided/retrieved sources" tail carry
# the absence semantics, so ordinary legal prose ("Section 5 appears in the
# provided sources") is unaffected.  Checked like unconditional markers
# (the pattern itself pins the source frame).
_ABSTENTION_PATTERNS = (
    re.compile(
        r"\bno\s+[^.;!?\n]{0,70}?\s(?:appears?|is|are|shown|found|listed|"
        r"present)\s+in\s+the\s+(?:provided|retrieved|given)\s+"
        r"(?:sources?|materials?|documents?)\b",
        re.IGNORECASE,
    ),
)

# Clause boundaries inside a sentence (Round 5, task 3): commas (except
# inside numbers like "1,000" and before citation years like ", 2019"),
# plus the connectives but/however/although.
_CLAUSE_SPLIT = re.compile(
    r",(?!\d)(?!\s+\d{4}\b)\s*|\s+(?:but|however|although)\s+",
    re.IGNORECASE,
)

# Legal-content markers: a clause carrying these (and no scoped abstention
# marker) is an assertive legal statement, so its sentence is not a
# refusal.  Used by clause-level abstention and _empty_claim_status.
LEGAL_MARKER_PATTERN = re.compile(
    r"\b(sections?|articles?|act|code|ipc|bns|crpc|bnss|bsa|cpc|"
    r"offence|offense|punish(?:es|ed|ing|able|ment|er)?|"
    r"imprison(?:ment|ed|s)?|fine|penalty|"
    r"court|judgment|judgement|tribunal|plaintiff|defendant|writ)\b",
    re.IGNORECASE,
)

_MARKDOWN_NOISE = re.compile(r"[*_`#>]")


def _sentence_spans(text: str) -> list[tuple[int, int, str]]:
    """Split text into (start, end, sentence) spans covering the whole string."""
    spans: list[tuple[int, int, str]] = []
    start = 0
    for match in _SENTENCE_SPLIT.finditer(text):
        if match.start() > start:
            spans.append((start, match.start(), text[start : match.start()]))
        start = match.end()
    if start < len(text):
        spans.append((start, len(text), text[start:]))
    return [span for span in spans if span[2].strip()]


def _clause_spans(sentence: str, base: int = 0) -> list[tuple[int, int, str]]:
    """Split a sentence into clause (start, end, clause) spans (Round 5).

    Base offsets let callers split on sentence text while keeping absolute
    coordinates for range checks. Commas inside numbers ("1,000") and before
    citation years ("Act, 2019") are not boundaries."""
    spans: list[tuple[int, int, str]] = []
    start = 0
    for match in _CLAUSE_SPLIT.finditer(sentence):
        if match.start() > start:
            spans.append((base + start, base + match.start(), sentence[start : match.start()]))
        start = match.end()
    if start < len(sentence):
        spans.append((base + start, base + len(sentence), sentence[start:]))
    return [span for span in spans if span[2].strip()]


def _clause_is_abstention(clause: str, sentence: str) -> bool:
    """True when the clause states source/answer absence (Round 5, task 3).

    Always-markers abstain on their own; contextual markers only abstain when
    the sentence is about the sources/answer (carries a source-context word)."""
    cleaned_clause = _MARKDOWN_NOISE.sub("", clause or "").lower()
    if not cleaned_clause.strip():
        return False
    for pattern in _ABSTENTION_PATTERNS:
        if pattern.search(cleaned_clause):
            return True
    for marker in ABSTENTION_MARKERS:
        if marker in cleaned_clause and marker not in CONTEXTUAL_MARKERS:
            return True
    cleaned_sentence = _MARKDOWN_NOISE.sub("", sentence or "").lower()
    if _SOURCE_CONTEXT.search(cleaned_sentence):
        for marker in CONTEXTUAL_MARKERS:
            if marker in cleaned_clause:
                return True
    return False


def _abstention_ranges(text: str) -> list[tuple[int, int]]:
    """Spans of clauses that are abstention/source-absence statements (Round 5).

    Clause-level (not sentence-level): in a mixed sentence such as "The
    sources do not contain the fine, but Section 999 BNS punishes it with 50
    years." only the source-absence clause is suppressed; the substantive
    clause keeps its claims."""
    ranges: list[tuple[int, int]] = []
    for sent_start, _sent_end, sentence in _sentence_spans(text):
        for start, end, clause in _clause_spans(sentence, sent_start):
            if _clause_is_abstention(clause, sentence):
                ranges.append((start, end))
    return ranges


def is_abstention_sentence(sentence: str) -> bool:
    """True when the sentence is a refusal/source-absence statement (Round 5).

    Clause-level: the sentence must contain at least one abstention clause and
    no legal-assertive clause. Neutral fragments ("Consequently", "Here",
    "In summary") and bare single-word list fragments ("act") do not veto an
    abstention, but a substantive legal clause ("Section 999 BNS punishes it
    with 50 years") does — that sentence makes assertive legal claims and must
    not be treated as a refusal."""
    clauses = _clause_spans(sentence or "")
    if not clauses:
        return False
    has_abstention = False
    for _start, _end, clause in clauses:
        if _clause_is_abstention(clause, sentence):
            has_abstention = True
        elif (
            len(clause.split()) >= 2
            and LEGAL_MARKER_PATTERN.search(_MARKDOWN_NOISE.sub("", clause))
        ):
            return False
    return has_abstention


def _substantive_fragment(sentence: str) -> bool:
    """True when the fragment carries real words (not only citations/links).

    Markdown, bracketed citation tokens ([Source 1], 【Source 2】) and bare
    URLs are stripped before the check so trailing citation lines do not
    count as content."""
    cleaned = _MARKDOWN_NOISE.sub("", sentence or "")
    cleaned = re.sub(r"\[[^\]]*\]", " ", cleaned)
    cleaned = re.sub(r"【[^】]*】", " ", cleaned)
    cleaned = re.sub(r"https?://\S+", " ", cleaned)
    return bool(re.search(r"[a-z]{2,}", cleaned.lower()))


def is_abstention_answer(answer: str) -> bool:
    """True when the whole answer is an abstention (Round 4, task 4).

    Alignment rule for the generator's `abstained` flag: an answer is an
    abstention iff it has at least one substantive sentence and every
    substantive sentence is a marker-bearing refusal/source-absence
    statement. Citation-only lines are ignored; empty answers are not
    abstentions."""
    spans = _sentence_spans(normalize_spaces(answer or ""))
    substantive = [
        sentence for _start, _end, sentence in spans if _substantive_fragment(sentence)
    ]
    if not substantive:
        return False
    return all(is_abstention_sentence(sentence) for sentence in substantive)


def _in_ranges(span: tuple[int, int], ranges: list[tuple[int, int]]) -> bool:
    """True when the span starts inside one of the ranges."""
    return any(start <= span[0] < end for start, end in ranges)


# Section-number presence in source text, word-boundary safe (302 != 3021,
# 302 != 302A). Also accepts the numbered-list form "502. " at line start.
# Plural "sections N" accepted too (cmp1 2026-10-06: IPC 200's Explanation
# quotes "sections 199 and 200"; the answer's "IPC Section 199" is present
# in the sources and was scoring ungrounded - +1 grounded cmp1, +1 ipc2,
# 0 bns1, measured offline on all three runs).
def section_present_in_text(section_num: str, text: str) -> bool:
    text = normalize_spaces(text or "").lower()
    sec = re.escape(section_num.lower())
    return bool(
        # Round 5: colon/dash-tolerant, § form, and whole-token section number
        # ("section 5" must not match inside "section 50").
        re.search(rf"\bsections?\s*[:.\-]?\s*{sec}\b", text)
        or re.search(rf"(?:^|[\s(])§\s*{sec}\b", text)
        or re.search(rf"(?:^|\n)\s*{sec}\.\s", text)
    )


# Two forms must NOT yield a statute-section mention (both measured against the
# 200 iter4 answers, 2026-10-03):
#
#   "[§1]"   A bracket-wrapped §-index is a SOURCE FOOTNOTE, not a section.
#            All 56 bracketed occurrences in those answers were pure integers
#            (1..7) labelling retrieved sources — "Section 171a IPC [§1] |
#            Section 169 BNS [§2]" — while every real citation used the bare
#            form ("§332", 38 occurrences). Reading [§1] as Section 1 alone
#            produced 50 of the run's 61 ungrounded mentions.
#   "sub-section 1" / "sub‑section 1" / "subsection 1"
#            The bare word "section" appears inside another word; the capture
#            was the subsection index of the section already under discussion,
#            not an independent citation. Hyphen range covers the non-breaking
#            hyphen (U+2011) the generator emits.
_SECTION_MENTION = re.compile(
    r"(?<![a-z\u2010-\u2015\[-])(?:section|§)\s*[:.\-]?\s*(\d+[a-z]?)",
    re.IGNORECASE,
)

# Round 5: one broad extractor covers every section-claim form —
# "Section 103 BNS", "Section 103 of the BNS", "Section 103(1) BNS",
# "Section: 103 BNS", bare "Section 103 states...", and "§ 7". Structured
# section-of-act forms run first and suppress overlapping broad matches.
# Groups: 1 = section number, 2 = "of the BNS" abbreviation, 3 = bare
# trailing abbreviation ("Section 103(1) BNS").
_SECTION_CLAIM = re.compile(
    # NOTE: no \b before § — it is a non-word character, so a boundary
    # check would fail for the common "… § 5" spacing.
    r"(?:\bsection|§)\s*[:.\-]?\s*(\d+[a-z]?)"
    r"(?:\s*\(\s*\d+[a-z]?\s*\))?"
    r"(?:\s+of\s+(?:the\s+)?(ipc|bns|bnss|bsa|crpc|cpc))?"
    r"(?:\s+(ipc|bns|bnss|bsa|crpc|cpc))?"
    r"\b",
    re.IGNORECASE,
)

# Round 5: sentences carrying punishment context yield duration claims
# ("punishes it with 50 years", "imprisonment for 2 years", "sentenced to
# 7 years"). Sentences without these stems never produce duration claims
# (limitation periods like "filed within 90 days" are not penalties).
_PUNISH_CONTEXT = re.compile(
    r"punish|imprison|sentenc|penalt|rigorous", re.IGNORECASE
)


# A clause that is nothing but citation tokens ("IPC §272", "Section 399",
# "273) …") carries no assertion of its own — it only inherits the force of
# the sentence around it.  BNS run B (2026-10-04), bns-275-a: the clause
# split on the "e.g.," comma put "IPC §272" alone in a clause whose neighbour
# ("§273) cannot be made from the provided material.") was correctly
# negated, leaving §272 scored assertive + ungrounded.
_BARE_CITATION_TOKEN = re.compile(
    r"^(?:§\d+[a-z]?|\d+[a-z]?|e\.?g\.?|i\.?e\.?|cf\.?|see|such|as|and|or|"
    r"the|of|to|with|in|by|for|corresponding|respectively|ipc|bns|crpc|bnss|"
    r"bsa|cpc|sections?|sec)$",
    re.IGNORECASE,
)


def _bare_citation_clause(clause: str) -> bool:
    """True when the clause holds only citation tokens (see _BARE_CITATION_TOKEN)."""
    cleaned = _MARKDOWN_NOISE.sub("", clause or "")
    tokens = [t for t in re.split(r"[\s,()]+", cleaned) if t.strip(".;:")]
    return bool(tokens) and all(
        _BARE_CITATION_TOKEN.match(t.strip(".;:")) for t in tokens
    )


# Compare run C (cmp1, 2026-10-05): 14 assertive-ungrounded mentions, 10 of
# them inside answers that *declare* the cited section absent from the sources
# ("… is not present in the retrieved sources", "… cannot be confirmed …",
# "… consult the full text of IPC Section 424").  Clause-level markers cannot
# reach them: the mention sits in a different clause or sentence from the
# marker, or before it (cmpr-340-416's crosswalk assertion precedes the
# "but its text is not present…" clause).  Absence-subject rule — a
# documented matcher fix, thresholds unchanged:
#   * each trigger occurrence names a SUBJECT section: the nearest section
#     mention before the trigger position in the answer, else (only for the
#     "consult the full text" wording) the first mention after it;
#   * every still-assertive mention OF a subject that is absent from the
#     sources (in_sources=False) is reclassified negated — it was an
#     abstention about that section, not an assertion of its content.
# The in_sources=False gate makes collateral impossible: grounded mentions
# (in_sources=True) are never touched.  Measured on all three runs before the
# edit (diag_trigger_sim.py): cmp1 10 flips -> 463/467 = 0.9914, ipc2 1 flip
# -> 1110/1118 = 0.9928, bns1 0 flips -> 996/1006 = 0.9901; 0 grounded lost.
_ABSENCE_TRIGGERS = (
    "not present in the retrieved sources",
    "not present in the sources",
    "not included in the provided sources",
    "not included in the retrieved sources",
    "missing from the sources",
    "missing from the retrieved sources",
    "consult the full text",
    "cannot be confirmed",
    # cmp1 re-run on the rebuilt gold (2026-10-06): the model wrote
    # "… in Section 302 (not retrieved)" - same self-declared absence, new
    # wording. 1 flip on cmp1, 0 on ipc2/bns1, 0 grounded lost (measured
    # offline on all three runs with diag_trigger_sim-style replay).
    "not retrieved",
    # cmp1 attempt2 (2026-10-06): "...(BNS Section 100, not reproduced in
    # the sources)" - same self-declared absence, new wording. Measured
    # offline on all three runs (sim_absence_repro.py): cmp1 610/617 ->
    # 610/616 = 0.9903 (1 flip), ipc2 0 flips, bns1 0 flips, 0 grounded
    # lost on any run.
    "not reproduced in the sources",
    # cmp1 attempt4 (2026-10-06): three grammatical variants of "not
    # present in the retrieved sources" that the model used to disclose
    # absence ("(IPC Section 323, not in the retrieved sources)", "are
    # not among the retrieved sources", "is not defined in the retrieved
    # sources"). Measured offline on all three runs
    # (sim_absence_variants.py): cmp1 702/715 -> 702/709 = 0.9901
    # (6 flips, all in answers that declare the same sections absent),
    # ipc2 0 flips, bns1 0 flips, 0 grounded lost on any run.
    "not in the retrieved sources",
    "not among the retrieved sources",
    "not defined in the retrieved sources",
)

# Only this wording licenses a mention that FOLLOWS the trigger as subject
# ("consult the full text of IPC Section 424").  Beside a bare absence claim
# the following mention is usually the unrelated retrieved source ("Source 2
# shows IPC Section 399 …") and must not become the subject.
_ABSENCE_AFTER_TRUST = "consult the full text"


def grounding_report(answer: str, source_text: str) -> dict[str, Any]:
    """Citation-grounding report for a generated answer vs retrieved sources.

    Every "Section N" (or "§ N") mention is classified negated/assertive by
    the clause it appears in (Round 5: a mixed sentence negates only its
    source-absence clause), then checked for presence in ``source_text``
    with word-boundary matching.  Mentions of a section the answer itself
    declares absent are reclassified as abstentions (see _ABSENCE_TRIGGERS).
    This is the product-side replacement for the probe's ad-hoc substring
    grounding check (Round 2, task 1).
    """
    answer_n = normalize_spaces(answer)
    src = normalize_spaces(source_text)
    mentions: list[dict[str, Any]] = []
    absent_subjects: set[str] = set()
    for start, _end, sentence in _sentence_spans(answer_n):
        # Absence-subject detection (documented matcher fix, see
        # _ABSENCE_TRIGGERS above).
        low = sentence.lower()
        trig = [t for t in _ABSENCE_TRIGGERS if t in low]
        if trig:
            tpos = answer_n.find(trig[0], start)
            if tpos < 0:
                tpos = start
            before = [
                (m.start() + start, m.group(1).lower())
                for m in _SECTION_MENTION.finditer(sentence)
                if m.start() + start < tpos
            ]
            if before:
                absent_subjects.add(before[-1][1])
            elif _ABSENCE_AFTER_TRUST in low:
                after = [
                    (m.start() + start, m.group(1).lower())
                    for m in _SECTION_MENTION.finditer(sentence)
                    if m.start() + start >= tpos
                ]
                if after:
                    absent_subjects.add(after[0][1])
        clauses = _clause_spans(sentence)
        abstention_flags = [
            _clause_is_abstention(clause, sentence)
            for _cs, _ce, clause in clauses
        ]
        sentence_has_abstention = any(abstention_flags)
        for (_c_start, _c_end, clause), negated in zip(clauses, abstention_flags):
            # Bare citation fragment ("IPC §272") beside an abstention clause
            # inherits that clause's negation (see _BARE_CITATION_TOKEN).
            if (
                not negated
                and sentence_has_abstention
                and _bare_citation_clause(clause)
            ):
                negated = True
            for match in _SECTION_MENTION.finditer(clause):
                sec = match.group(1).lower()
                in_sources = section_present_in_text(sec, src)
                mentions.append(
                    {
                        "section": sec,
                        "negated": negated,
                        "in_sources": in_sources,
                        "grounded": (not negated) and in_sources,
                        "sentence": sentence.strip()[:200],
                    }
                )
    # Absence-subject pass: an answer that declares section X absent has not
    # asserted X's content anywhere — reclassify X's still-assertive,
    # absent-from-sources mentions as abstentions.  in_sources=False keeps
    # grounded mentions out of the pass entirely (see _ABSENCE_TRIGGERS).
    if absent_subjects:
        for m in mentions:
            if (
                m["section"] in absent_subjects
                and not m["negated"]
                and not m["in_sources"]
            ):
                m["negated"] = True
    return {
        "mentions": mentions,
        "n_mentions": len(mentions),
        "n_negated": sum(1 for m in mentions if m["negated"]),
        "n_assertive": sum(1 for m in mentions if not m["negated"]),
        "n_grounded": sum(1 for m in mentions if m["grounded"]),
    }


# Abbreviation -> full act name expansion for section-claim verification.
ACT_ABBREV_EXPANSIONS = {
    "ipc": "indian penal code",
    "bns": "bharatiya nyaya sanhita",
    "bnss": "bharatiya nagarik suraksha sanhita",
    "bsa": "bharatiya sakshya adhiniyam",
    "crpc": "code of criminal procedure",
    "cpc": "code of civil procedure",
}


# Strict Citation System Prompt for Zero-Hallucination
STRICT_CITATION_PROMPT = """You are HECTOR, a zero-hallucination legal AI assistant.

CRITICAL RULES:
- Only answer using information explicitly present in the retrieved context
- If information is not in the context, respond: "I cannot find this information in the loaded legal texts."
- Every claim must cite: Source Document, Page Number, and Section if applicable
- Never infer, imply, or fabricate information not explicitly stated in the source
- When citing, use format: [Source: Book Name, Page: X, Section: Y BNS]

CONTEXT PROVIDED:
{context}

QUESTION: {question}

INSTRUCTIONS:
1. Use ONLY the provided context to answer
2. If the answer requires information not in context, say so explicitly
3. Cite your sources precisely"""


# Refusal Templates for Unverified Queries
REFUSAL_TEMPLATES = [
    "I cannot find this information in the loaded legal texts. The retrieved documents do not contain details about: {topic}",
    "The current knowledge base does not contain sufficient information to answer: {topic}. Please provide additional legal texts or clarify your query.",
    "No authoritative source found in the indexed corpus for: {topic}. This may require additional legal commentary or bare acts.",
    "The retrieved documents do not address: {topic}. My knowledge is limited to the legally indexed materials.",
]


class ClaimExtractor:
    """Extracts factual claims from generated responses for verification."""

    @classmethod
    def extract_claims(cls, text: str) -> list[dict[str, Any]]:
        """Extract factual claims from legal response text.

        Round 2: text is space-normalized first (narrow-space safety), and
        claims that fall inside abstention/source-absence clauses are not
        extracted ("sources do not contain Section X" is not a claim).

        Round 5: duration claims come from punishment-context sentences
        (never from limitation periods), a single broad extractor covers
        every Section/§ form, and penalty claims record the sections cited
        in their own sentence for scoped verification.
        """
        text = normalize_spaces(text)
        abstention = _abstention_ranges(text)
        claims: list[dict[str, Any]] = []
        text_lower = text.lower()

        # Extract section references
        for match in re.finditer(
            r"section\s+(\d+[a-z]?)\s+(ipc|bns|crpc|bnss|bsa)", text_lower
        ):
            claims.append(
                {
                    "type": "section_reference",
                    "value": f"Section {match.group(1)} {match.group(2).upper()}",
                    "span": match.span(),
                }
            )

        # Extract punishment claims
        for match in re.finditer(
            r"punishment\s+(?:is|shall be|may be)\s+([^.]+)", text_lower
        ):
            claims.append(
                {
                    "type": "punishment",
                    "value": match.group(0),
                    "span": match.span(),
                }
            )

        # Round 5: imprisonment durations from punishment-context sentences
        # ("punishes it with 50 years", "imprisonment for 2 years",
        # "imprisonment for life"). Sentences without punishment context
        # (limitation periods etc.) never yield duration claims.
        for sent_start, _sent_end, sentence in _sentence_spans(text):
            sent_lower = sentence.lower()
            if not _PUNISH_CONTEXT.search(sent_lower):
                continue
            for match in re.finditer(
                r"(?<!\d)(\d[\d,]*)\s*-?\s*years?\b", sent_lower
            ):
                claims.append(
                    {
                        "type": "imprisonment_duration",
                        "value": f"{match.group(1)} years",
                        "span": (
                            sent_start + match.start(),
                            sent_start + match.end(),
                        ),
                    }
                )
            life_m = re.search(
                r"imprisonment\s+for\s+life|life\s+imprisonment", sent_lower
            )
            if life_m:
                claims.append(
                    {
                        "type": "imprisonment_duration",
                        "value": "life",
                        "span": (
                            sent_start + life_m.start(),
                            sent_start + life_m.end(),
                        ),
                    }
                )

        # Extract fine amounts
        for match in re.finditer(
            r"fine\s+(?:of\s+|up to\s+)?([\d,]+(?:\s+rupees)?)", text_lower
        ):
            claims.append(
                {
                    "type": "fine_amount",
                    "value": match.group(1),
                    "span": match.span(),
                }
            )

        # Extract "whoever...shall be punished" patterns
        for match in re.finditer(
            r"whoever\s+([^.]+?)\s+shall\s+be\s+punished", text_lower
        ):
            claims.append(
                {
                    "type": "offence_definition",
                    "value": match.group(0),
                    "span": match.span(),
                }
            )

        # Extract "Section N of the <Act>" references (e.g. Limitation Act)
        for match in re.finditer(
            r"section\s+(\d+[a-z]?)\s+of\s+(?:the\s+)?"
            r"((?:[a-z0-9]+(?:\s|,)+){0,10}?(?:act|code|sanhita|adhiniyam|ordinance|rules)"
            r"(?:,\s*\d{4})?)",
            text_lower,
        ):
            section_num = match.group(1)
            act_phrase = match.group(2).strip()
            stop_words = {
                "act", "code", "sanhita", "adhiniyam", "ordinance", "rules",
                "of", "the",
            }
            act_terms = [
                word
                for word in re.findall(r"[a-z0-9]+", act_phrase)
                if word not in stop_words and len(word) >= 3
            ]
            claims.append(
                {
                    "type": "section_of_act",
                    "value": match.group(0).strip(),
                    "section": section_num,
                    "act_terms": act_terms,
                    "span": match.span(),
                }
            )

        # Extract "Section N of IPC/BNS/..." references
        for match in re.finditer(
            r"section\s+(\d+[a-z]?)\s+of\s+(ipc|bns|crpc|bnss|bsa|cpc)\b", text_lower
        ):
            claims.append(
                {
                    "type": "section_reference",
                    "value": f"Section {match.group(1)} {match.group(2).upper()}",
                    "span": match.span(),
                }
            )

        # Round 2: act-before-section references
        # ("Bharatiya Sakshya Adhiniyam, 2023 (BSA), Section 23(1)")
        for match in re.finditer(
            r"\b((?:[a-z0-9]+(?:\s|,)+){0,8}?(?:act|code|sanhita|adhiniyam"
            r"|ordinance|rules)(?:,\s*\d{4})?)"
            r"\s*(?:\(\s*[a-z]{2,8}\s*\))?"
            r"\s*[,.:\-\u2013\u2014]?\s*section\s+(\d+[a-z]?)",
            text_lower,
        ):
            act_phrase = match.group(1).strip()
            section_num = match.group(2)
            stop_words = {
                "act", "code", "ordinance", "rules",
                "of", "the",
            }
            act_terms = [
                word
                for word in re.findall(r"[a-z0-9]+", act_phrase)
                if word not in stop_words and len(word) >= 3 and not word.isdigit()
            ]
            claims.append(
                {
                    "type": "section_of_act",
                    "value": match.group(0).strip(),
                    "section": section_num,
                    "act_terms": act_terms,
                    "span": match.span(),
                }
            )

        # Round 5: one broad pass for every remaining Section/§ form.
        # Overlap with a structured section claim suppresses the broad match
        # (the structured claim already carries the same reference).
        structured_spans = [
            claim["span"]
            for claim in claims
            if claim["type"] in ("section_reference", "section_of_act")
        ]
        for match in _SECTION_CLAIM.finditer(text_lower):
            if any(
                match.start() < span_end and match.end() > span_start
                for span_start, span_end in structured_spans
            ):
                continue
            section_num = match.group(1)
            act_abbrev = None
            if match.group(2):
                act_abbrev = match.group(2)
            elif match.group(3):
                act_abbrev = match.group(3)
            value = f"Section {section_num}"
            if act_abbrev:
                value = f"{value} {act_abbrev.upper()}"
            claims.append(
                {
                    "type": "section_reference",
                    "value": value,
                    "span": match.span(),
                }
            )

        # Round 5: penalty claims record the sections cited in their own
        # sentence; verification scopes them to those sections' chunks.
        sentence_spans = _sentence_spans(text)
        penalty_types = {"imprisonment_duration", "fine_amount", "punishment"}
        for claim in claims:
            if claim["type"] not in penalty_types:
                continue
            for sent_start, sent_end, sentence in sentence_spans:
                if sent_start <= claim["span"][0] < sent_end:
                    cited = list(
                        dict.fromkeys(
                            m.group(1)
                            for m in _SECTION_MENTION.finditer(sentence)
                        )
                    )
                    if cited:
                        claim["section_context"] = cited
                    break

        # Extract Article references (Constitution etc.)
        for match in re.finditer(r"\barticle\s+(\d+[a-z]?)\b", text_lower):
            claims.append(
                {
                    "type": "article_reference",
                    "value": f"Article {match.group(1)}",
                    "span": match.span(),
                }
            )

        # Round 2: drop claims inside abstention/source-absence sentences
        claims = [
            claim
            for claim in claims
            if not _in_ranges(claim["span"], abstention)
        ]

        deduped = []
        seen: set[tuple[str, str]] = set()
        for claim in claims:
            key = (claim["type"], str(claim["value"]).lower())
            if key in seen:
                continue
            seen.add(key)
            deduped.append(claim)
        return deduped


class ChainOfVerification:
    """Claim-grounding verifier (historical name: Chain-of-Verification).

    Deterministic source-grounding checks over extracted claims: word-boundary
    section/article presence, whole-token penalty terms scoped to the cited
    section's chunk, offence-definition term ratios. No LLM round-trips —
    verification must stay reproducible for the gold eval and fail closed
    (unsupported claims are flagged, never silently approved).
    """

    # Sentence-scoped abstention detection now lives in module-level
    # ABSTENTION_MARKERS / is_abstention_sentence (kept for compatibility).
    _REFUSAL_MARKERS = ABSTENTION_MARKERS
    _LEGAL_MARKERS = LEGAL_MARKER_PATTERN
    _OFFENCE_STOPWORDS = frozenset(
        "a an the and or but if then else who whom whose whoever any every each "
        "is are was were be been being shall will may must should can could "
        "has have had do does did nor so as of to in at by for with from into "
        "upon under over between within without than then there thereof which "
        "that this these those it its their his her our your my me you he she "
        "we they i".split()
    )

    def __init__(self):
        # Round 5 decision: no Groq/LLM client here. The class performs
        # deterministic claim grounding, not a Chain-of-Verification
        # generation loop; an LLM entailment second opinion would add
        # nondeterminism and cost to every verified claim (180-row x 3-run
        # gold eval), break A/B comparability across rounds, and could
        # silently upgrade unsupported claims against the fail-closed
        # invariant. StrictCitationGenerator keeps its own Groq client for
        # generation.
        pass

    @classmethod
    def _empty_claim_status(cls, response: str) -> str:
        """Status when zero claims could be extracted (Round 2, task 2).

        NOT_APPLICABLE only for genuine refusals: every sentence must be an
        abstention/source-absence statement (or there must be no substantive
        legal content). A response that discusses legal material outside the
        refusal sentences gets UNVERIFIED — coverage is not scored, never 100%.
        """
        response_n = normalize_spaces(response)
        substantive = [
            sentence
            for _start, _end, sentence in _sentence_spans(response_n)
            if not is_abstention_sentence(sentence)
        ]
        if substantive and any(
            cls._LEGAL_MARKERS.search(sentence) for sentence in substantive
        ):
            return "UNVERIFIED"
        return "NOT_APPLICABLE"

    def verify_response(
        self, response: str, source_documents: list[dict]
    ) -> dict[str, Any]:
        """
        Run the claim-grounding verification pipeline (Round 5).

        Returns:
            dict with keys: verified_response, claims_verified, total_claims,
                           claims_total, claims_supported, claims_unsupported,
                           unverified_claims, citation_coverage, needs_correction,
                           correction_notes, status
        """
        # Step 1: Extract claims from response
        claims = ClaimExtractor.extract_claims(response)

        if not claims:
            status = self._empty_claim_status(response)
            if status == "NOT_APPLICABLE":
                notes = "No verifiable claims — refusal or non-legal response."
            else:
                notes = (
                    "Response references legal material but no verifiable "
                    "claims could be extracted — coverage not scored."
                )
            return {
                "verified_response": response,
                "claims_verified": 0,
                "total_claims": 0,
                "claims_total": 0,
                "claims_supported": 0,
                "claims_unsupported": 0,
                "unverified_claims": [],
                "citation_coverage": None,
                "needs_correction": False,
                "correction_notes": notes,
                "status": status,
            }

        # Step 2: Build verification context from source documents
        verification_context = self._build_verification_context(source_documents)

        # Step 3: Verify each claim against sources
        verified_claims = []
        unverified_claims = []

        for claim in claims:
            is_verified, verification_note = self._verify_claim(
                claim, verification_context, source_documents
            )
            if is_verified:
                verified_claims.append(
                    {**claim, "verified": True, "note": verification_note}
                )
            else:
                unverified_claims.append(
                    {**claim, "verified": False, "note": verification_note}
                )

        # Step 4: Calculate metrics
        total_claims = len(claims)
        citation_coverage = len(verified_claims) / total_claims

        if not unverified_claims:
            status = "VERIFIED"
        elif not verified_claims:
            status = "UNVERIFIED"
        else:
            status = "PARTIAL"

        # Step 5: Determine if correction needed
        needs_correction = citation_coverage < 0.5 or len(unverified_claims) > 0

        # Step 6: Generate corrected response if needed
        corrected_response = response
        correction_notes = []

        if needs_correction:
            corrected_response, correction_notes = self._correct_response(
                response, unverified_claims, source_documents
            )

        return {
            "verified_response": corrected_response,
            "claims_verified": len(verified_claims),
            "total_claims": total_claims,
            "claims_total": total_claims,
            "claims_supported": len(verified_claims),
            "claims_unsupported": len(unverified_claims),
            "unverified_claims": unverified_claims,
            "citation_coverage": round(citation_coverage, 3),
            "needs_correction": needs_correction,
            "correction_notes": correction_notes,
            "status": status,
        }

    def _build_verification_context(self, source_documents: list[dict]) -> str:
        """Combine source documents into verification context."""
        context_parts = []
        for doc in source_documents:
            meta = doc.get("metadata", {})
            source = (
                meta.get("real_act_name")
                or meta.get("act_name")
                or meta.get("source", "Unknown")
            )
            page = meta.get("page", "?")
            content = doc.get("document", "")
            context_parts.append(f"[Source: {source}, Page {page}]\n{content}\n")
        return "\n---\n".join(context_parts)

    def _verify_claim(
        self, claim: dict, context: str, sources: list[dict]
    ) -> tuple[bool, str]:
        """Verify a single claim against source documents.

        Round 5: penalty claims (duration / fine / punishment) are scoped to
        the chunks carrying the sections cited in the claim's own sentence
        and matched as whole tokens — never first-word-substring anywhere.
        Section and article references use word-boundary matching throughout.
        """
        claim_type = claim.get("type", "")
        # Round 2: normalize both sides so narrow spaces / NBSP in model
        # output cannot defeat exact substring matching (task 3).
        claim_value = normalize_spaces(str(claim.get("value", "")))
        claim_lower = claim_value.lower()

        # Round 5: scope penalty claims to the cited section's chunk. With
        # no matching chunk the claim fails closed (no in-scope source).
        cited = [str(num) for num in (claim.get("section_context") or [])]
        if cited and claim_type in (
            "imprisonment_duration",
            "fine_amount",
            "punishment",
        ):
            sources = [
                source
                for source in sources
                if any(
                    section_present_in_text(
                        num,
                        normalize_spaces(source.get("document", "")).lower(),
                    )
                    for num in cited
                )
            ]

        # Search through sources for the claim
        for source in sources:
            doc_text = normalize_spaces(source.get("document", "")).lower()
            doc_source = source.get("metadata", {}).get("source", "")
            doc_page = source.get("metadata", {}).get("page", "")

            if claim_type == "section_reference":
                # Round 5: word-boundary section presence only — the old
                # substring shortcut let "Section 5" match "Section 50".
                sec_m = re.match(
                    r"section\s+(\d+[a-z]?)\s*([a-z]{2,6})?$", claim_lower
                )
                if sec_m:
                    if not section_present_in_text(sec_m.group(1), doc_text):
                        continue
                    abbrev = sec_m.group(2)
                    if not abbrev:
                        return True, (
                            f"Section {sec_m.group(1)} found in "
                            f"{doc_source} page {doc_page}"
                        )
                    expansion = ACT_ABBREV_EXPANSIONS.get(abbrev, abbrev)
                    if re.search(
                        rf"\b{re.escape(abbrev)}\b", doc_text
                    ) or re.search(rf"\b{re.escape(expansion)}\b", doc_text):
                        return True, (
                            f"Section {sec_m.group(1)} {abbrev.upper()} "
                            f"matched in {doc_source} page {doc_page}"
                        )
                    continue
                if re.search(
                    rf"(?<!\w){re.escape(claim_lower)}(?!\w)", doc_text
                ):
                    return True, f"Found in {doc_source} page {doc_page}"

            elif claim_type == "imprisonment_duration":
                if self._duration_matches(claim_lower, doc_text):
                    return True, f"Penalty term matched in {doc_source}"

            elif claim_type == "punishment":
                if self._punishment_matches(claim_lower, doc_text):
                    return True, f"Punishment grounded in {doc_source}"

            elif claim_type == "fine_amount":
                if self._fine_matches(claim_lower, doc_text):
                    return True, f"Fine amount matched in {doc_source}"

            elif claim_type == "offence_definition":
                terms = [
                    word
                    for word in re.findall(r"[a-z0-9]+", claim_value.lower())
                    if len(word) >= 3 and word not in self._OFFENCE_STOPWORDS
                ]
                if terms:
                    matched = [term for term in terms if term in doc_text]
                    if matched and (
                        len(matched) == len(terms)
                        or (
                            len(terms) >= 4
                            and len(matched) / len(terms) >= 0.6
                        )
                    ):
                        return True, f"Offence definition grounded in {doc_source}"
                elif claim_value.lower() in doc_text:
                    return True, f"Offence definition found in {doc_source}"

            elif claim_type == "section_of_act":
                act_terms = claim.get("act_terms") or []
                section_num = claim.get("section") or ""
                if section_num and section_present_in_text(section_num, doc_text):
                    if act_terms and all(term in doc_text for term in act_terms):
                        return True, (
                            f"Section {section_num} of matched act found in "
                            f"{doc_source}"
                        )
                    # Round 2: anaphoric act references ("Section 5 of the
                    # Act") carry no resolvable act terms — verify by the
                    # section number alone.
                    if not act_terms:
                        return True, (
                            f"Section {section_num} found in {doc_source} "
                            f"page {doc_page} (generic act reference)"
                        )

            elif claim_type == "article_reference":
                # Round 5: word-boundary number check — "Article 19" must not
                # match inside "Article 190".
                art_m = re.search(r"article\s+(\d+[a-z]?)", claim_lower)
                if art_m and re.search(
                    rf"\barticle\s*[:.\-]?\s*{re.escape(art_m.group(1))}\b",
                    doc_text,
                ):
                    return True, f"Found in {doc_source} page {doc_page}"

        return False, "Claim not found in any source document"

    @staticmethod
    def _duration_matches(value: str, doc_text: str) -> bool:
        """Whole-token duration check against the scoped chunk.

        "2 years" requires a standalone number 2 followed by "years" in the
        chunk (the chunk's "20 years" or "302" never satisfies it); "life"
        requires a life-imprisonment phrase."""
        if value.strip() == "life":
            return bool(
                re.search(
                    r"imprisonment\s+for\s+life|life\s+imprisonment|for\s+life",
                    doc_text,
                )
            )
        m = re.search(r"(\d[\d,]*)\s*-?\s*years?", value)
        if not m:
            return False
        num = re.sub(r"[^\d]", "", m.group(1))
        if not num:
            return False
        doc_digits = doc_text.replace(",", "")
        return bool(
            re.search(
                rf"(?<!\d){re.escape(num)}(?!\d)\s*-?\s*years?\b",
                doc_digits,
            )
        )

    @staticmethod
    def _fine_matches(value: str, doc_text: str) -> bool:
        """Whole-number fine check: "50" must never hit "5000" (nor a bare
        "Section 50" / "Article 50" / "§ 50" label)."""
        m = re.search(r"\d[\d,]*", value)
        if not m:
            return False
        num = re.sub(r"[^\d]", "", m.group(0))
        if not num:
            return False
        doc_digits = doc_text.replace(",", "")
        token = re.escape(num)
        return bool(
            re.search(
                rf"(?<!\d)(?<!section\s)(?<!article\s)(?<!\u00a7\s){token}(?!\d)",
                doc_digits,
            )
        )

    @staticmethod
    def _punishment_matches(value: str, doc_text: str) -> bool:
        """Match every parseable penalty term in the punishment claim as a
        whole token against the scoped chunk; if the claim carries no
        parseable term, fall back to the full phrase (word-boundary)."""
        low = value.lower()
        found_any = False
        doc_digits = doc_text.replace(",", "")
        for m in re.finditer(r"(?<!\d)(\d[\d,]*)\s*-?\s*years?\b", low):
            found_any = True
            num = re.sub(r"[^\d]", "", m.group(1))
            if not num or not re.search(
                rf"(?<!\d){re.escape(num)}(?!\d)\s*-?\s*years?\b",
                doc_digits,
            ):
                return False
        if re.search(
            r"\bimprisonment\s+for\s+life\b|\blife\s+imprisonment\b", low
        ):
            found_any = True
            if not re.search(
                r"imprisonment\s+for\s+life|life\s+imprisonment|for\s+life",
                doc_text,
            ):
                return False
        if re.search(r"\bdeath\b", low):
            found_any = True
            if not re.search(r"\bdeath\b", doc_text):
                return False
        if found_any:
            return True
        phrase = re.sub(
            r"^punishment\s+(?:is|shall be|may be)\s+", "", low
        ).strip()
        if not phrase:
            return False
        return bool(re.search(rf"(?<!\w){re.escape(phrase)}(?!\w)", doc_text))

    def _correct_response(
        self, original: str, unverified: list[dict], sources: list[dict]
    ) -> tuple[str, list[str]]:
        """Generate corrected response removing unverified claims."""
        corrections = []

        # Build list of unverified claim values

        # Create corrected response with caveats
        corrected = original

        for claim in unverified:
            claim_value = claim.get("value", "")
            note = claim.get("note", "")
            corrections.append(f"Flagged unsupported: {claim_value[:50]}... ({note})")

        # Add disclaimer if corrections made
        if corrections:
            disclaimer = "\n\n**Verification Note**: Some claims could not be verified against source documents and have been flagged."
            corrected = corrected + disclaimer

        return corrected, corrections


class HallucinationDetector:
    """Metrics and detection for hallucination in legal responses."""

    @staticmethod
    def calculate_claim_coverage(verified_claims: int, total_claims: int) -> float | None:
        """Fraction of claims verified; None when there is nothing to score.

        Round 5 (task f): zero claims on a non-refusal answer must never
        report a vacuous 100% — coverage is unscored (None), matching
        verify_response's citation_coverage for empty claim sets."""
        if total_claims == 0:
            return None
        return verified_claims / total_claims

    @staticmethod
    def detect_fabricated_citations(response: str) -> list[dict]:
        """Detect potentially fabricated citations via structural validation."""
        fabricated: list[dict] = []
        seen_citations: set[str] = set()

        # Round 2 (task 7): normalize narrow spaces, capture the FULL section
        # number (\d{3,}, so 99999 is not truncated to "9999"), and skip
        # mentions inside abstention sentences — a negated echo of a bogus
        # number ("sources do not contain Section 99999") is not a citation.
        response = normalize_spaces(response)
        abstention = _abstention_ranges(response)

        # --- Suspicious section numbers ---
        for match in re.finditer(r"Section\s+(\d{3,})", response, re.IGNORECASE):
            if _in_ranges(match.span(), abstention):
                continue
            section = match.group(1)
            section_num = int(section)
            if section_num > 600:
                fabricated.append(
                    {
                        "type": "invalid_section_number",
                        "value": section,
                        "reason": f"Section {section} exceeds maximum IPC/BNS section number",
                    }
                )

        # --- Court codes considered valid in Indian case law ---
        valid_court_codes: set[str] = {
            "SC",
            "Pat",
            "Del",
            "Bom",
            "Cal",
            "Mad",
            "KER",
            "All",
            "Guj",
            "Raj",
            "HP",
            "J&K",
            "P&H",
            "Orissa",
            "Sikkim",
            "Manipur",
            "Meghalaya",
            "Tripura",
            "Gauhati",
            "Imphal",
            "Shimla",
            "MP",
            "AP",
            "Karn",
            "Chhatisgarh",
            "Jharkhand",
            "Uttarakhand",
            "NB",
            "Indore",
            "Lucknow",
            "Nagpur",
            "Panaji",
            "Gwalior",
        }

        current_year = 2026  # reference year for future-year checks

        # --- Extract every citation that matches the known patterns ---
        for pattern in CITATION_PATTERNS:
            for match in re.finditer(pattern, response, re.IGNORECASE):
                citation = match.group(0).strip()
                citation_key = citation.lower()

                # Duplicate citation check
                if citation_key in seen_citations:
                    fabricated.append(
                        {
                            "type": "duplicate_citation",
                            "value": citation,
                            "reason": "Citation appears more than once in response",
                        }
                    )
                    continue
                seen_citations.add(citation_key)

                # ---- AIR citation validation ----
                air_m = re.match(
                    r"AIR\s+(\d{4})\s+(\w+)\s+(\d+)", citation, re.IGNORECASE
                )
                if air_m:
                    year = int(air_m.group(1))
                    court = air_m.group(2)
                    case_num = int(air_m.group(3))

                    if year > current_year:
                        fabricated.append(
                            {
                                "type": "future_year",
                                "value": citation,
                                "reason": f"Year {year} is in the future",
                            }
                        )
                        continue

                    if court not in valid_court_codes:
                        fabricated.append(
                            {
                                "type": "invalid_court",
                                "value": citation,
                                "reason": f"Unknown court code '{court}' in AIR citation",
                            }
                        )
                        continue

                    if case_num > 0 and case_num % 100 == 0:
                        fabricated.append(
                            {
                                "type": "suspicious_round_number",
                                "value": citation,
                                "reason": f"Case number {case_num} is a suspiciously round number",
                            }
                        )

                # ---- SCC citation validation ----
                scc_m = re.match(
                    r"SCC\s+(\d{4})\s+(\w+)\s+(\d+)", citation, re.IGNORECASE
                )
                if scc_m:
                    year = int(scc_m.group(1))
                    court = scc_m.group(2)

                    if year > current_year:
                        fabricated.append(
                            {
                                "type": "future_year",
                                "value": citation,
                                "reason": f"Year {year} is in the future",
                            }
                        )
                        continue

                    if court not in valid_court_codes:
                        fabricated.append(
                            {
                                "type": "invalid_court",
                                "value": citation,
                                "reason": f"Unknown court code '{court}' in SCC citation",
                            }
                        )

                # ---- Citation missing court name (e.g. "AIR 2023 123") ----
                if re.match(r"(?:AIR|SCC)\s+\d{4}\s+\d+\s*$", citation, re.IGNORECASE):
                    fabricated.append(
                        {
                            "type": "missing_court",
                            "value": citation,
                            "reason": "Citation is missing a court name after the year",
                        }
                    )

        # ---- Log detected fabrications ----
        if fabricated:
            logger.warning(
                "Detected %d potentially fabricated citation(s)", len(fabricated)
            )
            for item in fabricated:
                logger.warning(
                    "  [%s] %s — %s", item["type"], item["value"], item["reason"]
                )

        return fabricated

    @staticmethod
    def detect_temporal_inconsistencies(response: str) -> list[dict]:
        """Detect laws referenced after their effective date."""
        inconsistencies = []

        response_lower = response.lower()

        # Check for IPC references (repealed July 1, 2024) alongside BNS references
        has_ipc = bool(re.search(r"\bipc\b", response_lower))
        has_bns = bool(re.search(r"\bbns\b", response_lower))

        if has_ipc and has_bns:
            # Check if the response treats IPC as current law
            ipc_current_patterns = [
                r"ipc\s+(?:provides|states|specifies|says|defines)",
                r"under\s+ipc\s+section",
                r"as\s+per\s+ipc",
            ]
            for pattern in ipc_current_patterns:
                if re.search(pattern, response_lower):
                    inconsistencies.append(
                        {
                            "type": "ipc_treated_as_current",
                            "detail": "Response references IPC as current law, but BNS is effective from July 1, 2024",
                            "pattern": pattern,
                        }
                    )
                    break

        # Check for references to specific repealed sections
        repealed_sections = re.findall(r"section\s+(\d+)\s+ipc", response_lower)
        for section in repealed_sections:
            section_num = int(section)
            # IPC sections 1-511, but many were restructured into BNS
            if section_num > 511:
                inconsistencies.append(
                    {
                        "type": "invalid_ipc_section",
                        "detail": f"Section {section} IPC does not exist (IPC has 511 sections)",
                    }
                )

        # Check for references to invalid BNS sections
        bns_sections = re.findall(r"section\s+(\d+)\s+bns", response_lower)
        for section in bns_sections:
            section_num = int(section)
            # BNS has 358 sections (official count), safe upper bound 395
            if section_num > 395:
                inconsistencies.append(
                    {
                        "type": "invalid_bns_section",
                        "detail": f"Section {section} BNS does not exist (BNS has 358 sections)",
                    }
                )

        return inconsistencies

    @staticmethod
    def generate_hallucination_report(verification_result: dict) -> dict:
        """Generate comprehensive hallucination detection report."""
        response = verification_result.get("verified_response", "")

        # Calculate metrics
        coverage = verification_result.get("citation_coverage", 0.0)
        total_claims = verification_result.get("total_claims", 0)
        verified = verification_result.get("claims_verified", 0)

        fabricated = HallucinationDetector.detect_fabricated_citations(response)
        temporal = HallucinationDetector.detect_temporal_inconsistencies(response)

        if coverage is None:
            if verification_result.get("status") == "NOT_APPLICABLE":
                status = "NOT_APPLICABLE"
            else:
                status = "HIGH_RISK"
        elif coverage >= 0.9 and len(fabricated) == 0 and len(temporal) == 0:
            status = "LOW_RISK"
        elif coverage >= 0.7:
            status = "MEDIUM_RISK"
        else:
            status = "HIGH_RISK"

        return {
            "status": status,
            "claim_coverage_score": coverage,
            "verified_claims": verified,
            "total_claims": total_claims,
            "fabricated_citations": fabricated,
            "temporal_inconsistencies": temporal,
            "needs_review": status not in ("LOW_RISK", "NOT_APPLICABLE"),
        }


class StrictCitationGenerator:
    """Generates responses with strict citation requirements."""

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        self.client = Groq(api_key=api_key) if api_key else None
        self.model = "qwen/qwen3.8-27b"

    def generate_strict(
        self, query: str, source_documents: list[dict], max_tokens: int = 800
    ) -> str:
        """Generate response with strict citation requirements."""
        context = self._build_strict_context(source_documents)

        prompt = STRICT_CITATION_PROMPT.format(context=context, question=query)

        try:
            chat = retry(
                self.client.chat.completions.create,
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": query},
                ],
                temperature=0,
                max_tokens=max_tokens,
                max_attempts=3,
                operation_name="groq_generation",
            )
            response = chat.choices[0].message.content

            # Verify the generated response
            verifier = ChainOfVerification()
            verification = verifier.verify_response(response, source_documents)

            return verification.get("verified_response", response)
        except Exception as e:
            return f"Generation error: {str(e)}"

    def _build_strict_context(self, sources: list[dict]) -> str:
        """Build context with strict formatting."""
        parts = []
        for i, doc in enumerate(sources, 1):
            meta = doc.get("metadata", {})
            source = (
                meta.get("real_act_name")
                or meta.get("act_name")
                or meta.get("source", f"Document {i}")
            )
            page = meta.get("page", "?")
            content = doc.get("document", "")
            parts.append(f"[Document {i}]: {source} (Page {page})\n---\n{content}")
        return "\n\n".join(parts)


def get_refusal_response(topic: str) -> str:
    """Get a refusal template for unverified queries."""
    import random

    template = random.choice(REFUSAL_TEMPLATES)
    return template.format(topic=topic)
