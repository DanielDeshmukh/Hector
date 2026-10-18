/* eslint-disable no-useless-escape */
/**
 * The real boundary grammar, quoted verbatim from the ingest pipeline.
 *
 * Nothing here is stylised for display. Every pattern below is copied from the
 * Python that actually produces the index, with its file and line so it can be
 * checked against source. The `js` field is the same pattern compiled as a
 * JavaScript RegExp (the only change is `re.I` -> the `i` flag, since JS has no
 * inline `(?i:...)` group).
 *
 * Sources:
 *   backend/ingest_v2/v2_scanner.py    — section-head recognition
 *   backend/ingest_v2/step4_segment.py — where a part may be cut
 *   backend/ingest_v2/step6_validate.py— what must never be treated as text
 */

const ORD_WORDS =
  "First|Second|Third|Fourth|Fifth|Sixth|Seventh|Eighth|Ninth|" +
  "Tenth|Eleventh|Twelfth|Thirteenth|Fourteenth|Fifteenth|" +
  "Sixteenth|Seventeenth|Eighteenth|Nineteenth|Twentieth";

/** Section-head recognition. v2_scanner.py */
export const SECTION_HEAD = [
  {
    name: "RESTATED_RE",
    file: "backend/ingest_v2/v2_scanner.py",
    line: 27,
    role: "A restated section head: number, then a full stop, then a break or a dash pair. This is the primary signature.",
    python: String.raw`re.compile(r"^\s*(\d{1,4}[A-Za-z]{0,2})\.(?:\s+|--\s*|$)")`,
    js: new RegExp(String.raw`^\s*(\d{1,4}[A-Za-z]{0,2})\.(?:\s+|--\s*|$)`),
    key: "restated",
  },
  {
    name: "QUOTE_NUM_RE",
    file: "backend/ingest_v2/v2_scanner.py",
    line: 28,
    role: "Number followed by whitespace and an opening quote or bracket — editions that print `17 \"Government\"...` with no full stop.",
    python: String.raw`re.compile(r"^\s*(\d{1,4}[A-Za-z]{0,2})\s+(?=[\"'\u2018\u2019\u201c\u201d\[(])")`,
    js: new RegExp(String.raw`^\s*(\d{1,4}[A-Za-z]{0,2})\s+(?=["'“”‘’\[(])`),
    key: "quoted",
  },
  {
    name: "NUMHEAD_RE",
    file: "backend/ingest_v2/v2_scanner.py",
    line: 24,
    role: "A head number alone on its line; the marginal note continues on the next.",
    python: String.raw`re.compile(r"^\s*(\d{1,4}[A-Za-z]{0,2})\.\s*$")`,
    js: new RegExp(String.raw`^\s*(\d{1,4}[A-Za-z]{0,2})\.\s*$`),
    key: "numhead",
  },
  {
    name: "DIRECT_RE",
    file: "backend/ingest_v2/v2_scanner.py",
    line: 26,
    role: "Number, full stop, and the body already on the same line.",
    python: String.raw`re.compile(r"^\s*(\d{1,4}[A-Za-z]{0,2})\.\s+\S")`,
    js: new RegExp(String.raw`^\s*(\d{1,4}[A-Za-z]{0,2})\.\s+\S`),
    key: "direct",
  },
];

/** Lines that belong to the section they sit in, and may never open a new one. */
export const ANCHOR_KINDS = [
  {
    name: "PROTECTED_RE",
    file: "backend/ingest_v2/v2_scanner.py",
    line: 36,
    role: "A carve-out. Explanation, Exception, Provided that, Illustration — the condition travels with the rule it qualifies.",
    python: String.raw`re.compile(r"^\s*(?:Explanation|Exception|Provided\b|Illustration)", re.I)`,
    js: new RegExp(String.raw`^\s*(?:Explanation|Exception|Provided\b|Illustration)`, "i"),
    key: "protected",
  },
  {
    name: "SPLIT_LINE_RE",
    file: "backend/ingest_v2/v2_scanner.py",
    line: 37,
    role: "A top-level sub-section line `(1)`, `(2)`, `(a)` — the only place a part may be cut.",
    python: String.raw`re.compile(r"^\(\d+[a-z]?\)")`,
    js: new RegExp(String.raw`^\(\d+[a-z]?\)`),
    key: "subline",
  },
  {
    name: "SCHEDULE_HDR_RE",
    file: "backend/ingest_v2/v2_scanner.py",
    line: 64,
    role: "A schedule heading. Schedules sit after the last section; their numbered table rows must not leak out as sections.",
    python: String.raw`re.compile(r"^\s*(?:THE\s+)?(?:FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH|SEVENTH|EIGHTH|NINTH|TENTH|ELEVENTH|TWELFTH)?\s*SCHEDULES?\s*$")`,
    js: new RegExp(
      String.raw`^\s*(?:THE\s+)?(?:FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH|SEVENTH|EIGHTH|NINTH|TENTH|ELEVENTH|TWELFTH)?\s*SCHEDULES?\s*$`,
    ),
    key: "schedule",
  },
  {
    name: "FOOTNOTE_CITE_RE",
    file: "backend/ingest_v2/v2_scanner.py",
    line: 49,
    role: "Page-bottom amendment footnotes that cite another provision. By shape they are indistinguishable from a head, so they are rejected on their citation verb.",
    python: String.raw`re.compile(r"^\s*\d{1,4}[A-Za-z]{0,2}\.\s+(?:Cf\.|See\s|The\s+Act\s+has\s+been|Extended\s+to|The\s+words\b)", re.I)`,
    js: new RegExp(
      String.raw`^\s*\d{1,4}[A-Za-z]{0,2}\.\s+(?:Cf\.|See\s|The\s+Act\s+has\s+been|Extended\s+to|The\s+words\b)`,
      "i",
    ),
    key: "footnote",
  },
  {
    name: "AMEND_CITE_RE",
    file: "backend/ingest_v2/v2_scanner.py",
    line: 56,
    role: "`by Act N of YYYY` is the hallmark of an amendment footnote and never appears in a real section title.",
    python: String.raw`re.compile(r"^\s*\d{1,4}[A-Za-z]{0,2}\.\s+.*\bby\s+Act\s+\d+\s+of\s+(?:18|19|20)\d{2}", re.I)`,
    js: new RegExp(
      String.raw`^\s*\d{1,4}[A-Za-z]{0,2}\.\s+.*\bby\s+Act\s+\d+\s+of\s+(?:18|19|20)\d{2}`,
      "i",
    ),
    key: "amend",
  },
  {
    name: "SELF_BODY_RE",
    file: "backend/ingest_v2/v2_scanner.py",
    line: 70,
    role: "Title period, then two or more spaces, then a capital: the body starts on the same line with no dash.",
    python: String.raw`re.compile(r"\.\s{2,}(?=[A-Z\"'\u2018\u201c])")`,
    js: new RegExp(String.raw`\.\s{2,}(?=[A-Z"'“‘])`),
    key: "selfbody",
  },
];

/** Where a part may be cut, and where it may not. step4_segment.py */
export const CUT_RULES = {
  maxChars: {
    name: "MAX_CHARS",
    file: "backend/ingest_v2/step4_segment.py",
    line: 34,
    python: "MAX_CHARS = 3000",
    role: "The part ceiling. It is a storage limit, not a retrieval unit — a section that will not fit stays whole and is flagged LONG_UNSPLIT.",
    value: 3000,
  },
  sub: {
    name: "SUBL_RE",
    file: "backend/ingest_v2/step4_segment.py",
    line: 35,
    python: String.raw`re.compile(r"^\(\d+[a-z]?\)")`,
    js: new RegExp(String.raw`^\(\d+[a-z]?\)`),
    role: "Cut (a): before a top-level sub-section line.",
  },
  ord: {
    name: "ORD_RE",
    file: "backend/ingest_v2/step4_segment.py",
    line: 39,
    python: String.raw`re.compile(r"^(?:" + ORD_WORDS + r")\.\s*--")`,
    js: new RegExp(`^(?:${ORD_WORDS})\\.\\s*--`),
    role: "Cut (a): before an ordinal clause marker printed with a double dash — `First.--`, `Second.--`.",
  },
  block: {
    name: "BLOCK_START_RE",
    file: "backend/ingest_v2/step4_segment.py",
    line: 40,
    python: String.raw`re.compile(r"^\s*\[?\s*(?:(?:" + ORD_WORDS + r")\s+)?(?:Explanations?|Exceptions?|Illustrations?|Proviso|Provided)\b", re.I)`,
    js: new RegExp(
      `^\\s*\\[?\\s*(?:(?:${ORD_WORDS})\\s+)?(?:Explanations?|Exceptions?|Illustrations?|Proviso|Provided)\\b`,
      "i",
    ),
    role: "Cut (b): once a carve-out block opens, nothing inside it may be cut until the next block starts or the section ends.",
  },
};

/** Structural noise. step6_validate.py */
export const NOISE = [
  {
    name: "WHITELIST_RE",
    file: "backend/ingest_v2/step6_validate.py",
    line: 31,
    python: String.raw`re.compile(r"^(Illustrations?|Explanation|Exceptions?|Provided|Chapter|Part|Schedule)\b")`,
    js: new RegExp(String.raw`^(Illustrations?|Explanation|Exceptions?|Provided|Chapter|Part|Schedule)\b`),
    role: "Structural lines that are kept rather than folded into body text.",
  },
  {
    name: "HYPHEN_BREAK_RE",
    file: "backend/ingest_v2/step6_validate.py",
    line: 34,
    python: String.raw`re.compile(r"[a-z]-\n[a-z]")`,
    js: new RegExp(String.raw`[a-z]-\n[a-z]`),
    role: "A word broken across a line by the typesetter. Rejoined, never left split.",
  },
  {
    name: "PAGENUM_LINE_RE",
    file: "backend/ingest_v2/step6_validate.py",
    line: 35,
    python: String.raw`re.compile(r"^\s*\d{1,3}\s*$")`,
    js: new RegExp(String.raw`^\s*\d{1,3}\s*$`),
    role: "A page number. Formatting, not law.",
  },
  {
    name: "SEP_LINE_RE",
    file: "backend/ingest_v2/step6_validate.py",
    line: 36,
    python: String.raw`re.compile(r"^\s*[-\u2013\u2014*]{5,}\s*$")`,
    js: new RegExp(String.raw`^\s*[-–—*]{5,}\s*$`),
    role: "A rule of five or more dashes or asterisks — the printer's separator between a footnote and the text.",
  },
  {
    name: "FREF_PREFIX_RE",
    file: "backend/ingest_v2/step6_validate.py",
    line: 38,
    python: String.raw`re.compile(r"^\s*(?:\d{1,3}\s*)?\*+\[?|^\s*\d{1,3}\s*\[+")`,
    js: new RegExp(String.raw`^\s*(?:\d{1,3}\s*)?\*+\[?|^\s*\d{1,3}\s*\[+`),
    role: "A footnote-reference prefix glued to the start of a real line. Stripped before the line is read.",
  },
  {
    name: "FREF_RE",
    file: "backend/ingest_v2/v2_scanner.py",
    line: 21,
    python: String.raw`re.compile(r"^\s*(?:\d{1,3}\s*)?(?:[\*\uf000-\uf8ff]+\[*|\[+)")`,
    js: new RegExp(String.raw`^\s*(?:\d{1,3}\s*)?(?:[*\uF000-\uF8FF]+\[*|\[+)`),
    role: "The scanner's own footnote stripper. Applied repeatedly until the line stops changing.",
  },
];

/** The two constraints the pipeline states about itself, in its own words. */
export const CLAIMS = [
  {
    file: "backend/ingest_v2/step4_segment.py",
    line: 13,
    text:
      "Splitting per SPEC A8/A8b: a cut is allowed only\n" +
      '  (a) before a top-level sub-section line "(1)", "(2)", ... or before a line\n' +
      '      starting with an ordinal clause marker ("First.--", "Second.--", ...,\n' +
      "      double dash only), AND\n" +
      "  (b) never inside an open bracket and never inside an Illustration,\n" +
      "      Explanation, Exception or Proviso block (blocks close only at the next\n" +
      "      block start or the section end).",
  },
  {
    file: "backend/ingest_v2/step4_segment.py",
    line: 20,
    text:
      "The partition is the minimum number of parts under those rules (DP). If no\n" +
      "safe partition fits under the limit, the section is kept whole and flagged\n" +
      "LONG_UNSPLIT with its length. No text is ever rewritten; parts keep their\n" +
      "true page range from the scan; every part stores its kept-line indices.",
  },
  {
    file: "backend/ingest_v2/v2_scanner.py",
    line: 5,
    text:
      "scan_document(doc) -> dict with lines/markers/footnotes/stats/classes. " +
      "Rules per SPEC.md AMENDMENTS A1-A6. No hardcoding of numbers/titles.",
  },
];

/** Every entry above, flattened, for the copy-to-clipboard bundle. */
export const ALL_SOURCES = [...SECTION_HEAD, ...ANCHOR_KINDS, ...NOISE].map(
  (e) => `${e.file}:${e.line}  ${e.name}\n  ${e.python}`,
);

export const SOURCE_BUNDLE = ALL_SOURCES.join("\n\n");
