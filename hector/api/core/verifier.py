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

# Source-absence / refusal phrasings. A sentence containing any marker is an
# abstention statement: its citations are negated and its text must not be
# counted as an assertive claim (tasks 1/2/3/7).
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


def _abstention_ranges(text: str) -> list[tuple[int, int]]:
    """Spans of sentences that are abstention/source-absence statements."""
    return [
        (start, end)
        for start, end, sentence in _sentence_spans(text)
        if is_abstention_sentence(sentence)
    ]


def is_abstention_sentence(sentence: str) -> bool:
    """True when the sentence is a refusal/source-absence statement."""
    cleaned = _MARKDOWN_NOISE.sub("", sentence or "").lower()
    return any(marker in cleaned for marker in ABSTENTION_MARKERS)


def _in_ranges(span: tuple[int, int], ranges: list[tuple[int, int]]) -> bool:
    """True when the span starts inside one of the ranges."""
    return any(start <= span[0] < end for start, end in ranges)


# Section-number presence in source text, word-boundary safe (302 != 3021,
# 302 != 302A). Also accepts the numbered-list form "502. " at line start.
def section_present_in_text(section_num: str, text: str) -> bool:
    text = normalize_spaces(text or "").lower()
    sec = re.escape(section_num.lower())
    return bool(
        re.search(rf"\bsection\s+{sec}\b", text)
        or re.search(rf"(?:^|\n)\s*{sec}\.\s", text)
    )


_SECTION_MENTION = re.compile(r"(?:section|§)\s+(\d+[a-z]?)", re.IGNORECASE)


def grounding_report(answer: str, source_text: str) -> dict[str, Any]:
    """Citation-grounding report for a generated answer vs retrieved sources.

    Every "Section N" (or "§ N") mention is classified negated/assertive by
    the sentence it appears in, then checked for presence in ``source_text``
    with word-boundary matching. This is the product-side replacement for the
    probe's ad-hoc substring grounding check (Round 2, task 1).
    """
    answer_n = normalize_spaces(answer)
    src = normalize_spaces(source_text)
    mentions: list[dict[str, Any]] = []
    for _start, _end, sentence in _sentence_spans(answer_n):
        negated = is_abstention_sentence(sentence)
        for match in _SECTION_MENTION.finditer(sentence):
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

    # Patterns that indicate factual claims in legal text
    CLAIM_PATTERNS = [
        re.compile(r"Section\s+(\d+)\s+(?:IPC|BNS|CRPC|BNSS|BSA)", re.IGNORECASE),
        re.compile(r"under\s+(?:section|article)\s+(\d+)", re.IGNORECASE),
        re.compile(r"punishment\s+(?:is|shall be|may be)\s+([^.]+)", re.IGNORECASE),
        re.compile(
            r"imprisonment\s+for\s+(?:up to |upto |of )?(\d+)\s+years?", re.IGNORECASE
        ),
        re.compile(r"fine\s+(?:of |up to )?([^.]+)", re.IGNORECASE),
        re.compile(r"Whoever\s+([^.]+)\s+shall\s+be\s+punished", re.IGNORECASE),
        re.compile(r"is\s+(?:punishable|offence|offense)\s+with", re.IGNORECASE),
    ]

    @classmethod
    def extract_claims(cls, text: str) -> list[dict[str, Any]]:
        """Extract factual claims from legal response text.

        Round 2: text is space-normalized first (narrow-space safety), and
        claims that fall inside abstention/source-absence sentences are not
        extracted ("sources do not contain Section X" is not a claim).
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

        # Extract imprisonment durations
        for match in re.finditer(
            r"imprisonment\s+(?:for\s+)?(?:up to\s+)?(\d+)\s+years?", text_lower
        ):
            claims.append(
                {
                    "type": "imprisonment_duration",
                    "value": f"{match.group(1)} years",
                    "span": match.span(),
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

        # Round 2: section-symbol references ("BSA § 23(1)", "§ 5")
        for match in re.finditer(r"§\s*(\d+[a-z]?)\s*(?:\(\s*\d+\s*\))?", text_lower):
            claims.append(
                {
                    "type": "section_reference",
                    "value": f"Section {match.group(1)}",
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
    """Implements the CoVe workflow for hallucination prevention."""

    # Sentence-scoped abstention detection now lives in module-level
    # ABSTENTION_MARKERS / is_abstention_sentence (kept for compatibility).
    _REFUSAL_MARKERS = ABSTENTION_MARKERS
    _LEGAL_MARKERS = re.compile(
        r"\b(sections?|articles?|act|code|ipc|bns|crpc|bnss|bsa|cpc|"
        r"offence|offense|punish(?:ed|ment|able)|imprisonment|fine|"
        r"court|judgment|judgement|tribunal|plaintiff|defendant|writ)\b",
        re.IGNORECASE,
    )
    _OFFENCE_STOPWORDS = frozenset(
        "a an the and or but if then else who whom whose whoever any every each "
        "is are was were be been being shall will may must should can could "
        "has have had do does did nor so as of to in at by for with from into "
        "upon under over between within without than then there thereof which "
        "that this these those it its their his her our your my me you he she "
        "we they i".split()
    )

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        self.client = Groq(api_key=api_key) if api_key else None
        self.model = "llama-3.3-70b-versatile"

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
        Run full Chain-of-Verification pipeline.

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
        """Verify a single claim against source documents."""
        claim_type = claim.get("type", "")
        # Round 2: normalize both sides so narrow spaces / NBSP in model
        # output cannot defeat exact substring matching (task 3).
        claim_value = normalize_spaces(str(claim.get("value", "")))

        # Search through sources for the claim
        for source in sources:
            doc_text = normalize_spaces(source.get("document", "")).lower()
            doc_source = source.get("metadata", {}).get("source", "")
            doc_page = source.get("metadata", {}).get("page", "")

            if claim_type == "section_reference":
                # Check if section exists in document
                if claim_value.lower() in doc_text:
                    return True, f"Found in {doc_source} page {doc_page}"
                # Round 2: word-boundary section presence + optional act
                # abbreviation expansion ("Section 103 BNS" vs a chunk that
                # spells out "Bharatiya Nyaya Sanhita").
                sec_m = re.match(
                    r"section\s+(\d+[a-z]?)\s*([a-z]{2,6})?$", claim_value.lower()
                )
                if sec_m and section_present_in_text(sec_m.group(1), doc_text):
                    abbrev = sec_m.group(2)
                    if not abbrev:
                        return True, (
                            f"Section {sec_m.group(1)} found in "
                            f"{doc_source} page {doc_page}"
                        )
                    expansion = ACT_ABBREV_EXPANSIONS.get(abbrev, abbrev)
                    if abbrev in doc_text or expansion in doc_text:
                        return True, (
                            f"Section {sec_m.group(1)} {abbrev.upper()} matched "
                            f"in {doc_source} page {doc_page}"
                        )

            elif claim_type == "imprisonment_duration":
                # Check if imprisonment duration matches
                if claim_value.split()[0] in doc_text:
                    return True, f"Found duration reference in {doc_source}"

            elif claim_type == "punishment":
                # Check if punishment is mentioned
                if any(word in doc_text for word in claim_value.split()[:3]):
                    return True, f"Punishment context found in {doc_source}"

            elif claim_type == "fine_amount":
                # Check if fine is mentioned
                if claim_value.replace(",", "") in doc_text.replace(",", ""):
                    return True, f"Fine amount found in {doc_source}"

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
                if claim_value.lower() in doc_text:
                    return True, f"Found in {doc_source} page {doc_page}"
                act_terms = claim.get("act_terms") or []
                section_num = claim.get("section") or ""
                if section_num:
                    section_hit = re.search(
                        rf"\bsection\s+{re.escape(section_num)}\b", doc_text
                    ) or re.search(
                        rf"(?:^|\n)\s*{re.escape(section_num)}\.\s", doc_text
                    )
                    if section_hit and act_terms and all(
                        term in doc_text for term in act_terms
                    ):
                        return True, (
                            f"Section {section_num} of matched act found in "
                            f"{doc_source}"
                        )
                    # Round 2: anaphoric act references ("Section 5 of the
                    # Act") carry no resolvable act terms — verify by the
                    # section number alone.
                    if section_hit and not act_terms:
                        return True, (
                            f"Section {section_num} found in {doc_source} "
                            f"page {doc_page} (generic act reference)"
                        )

            elif claim_type == "article_reference":
                if claim_value.lower() in doc_text:
                    return True, f"Found in {doc_source} page {doc_page}"

        return False, "Claim not found in any source document"

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
    def calculate_claim_coverage(verified_claims: int, total_claims: int) -> float:
        """Calculate percentage of claims that are verified."""
        if total_claims == 0:
            return 1.0
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
        self.model = "llama-3.3-70b-versatile"

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
