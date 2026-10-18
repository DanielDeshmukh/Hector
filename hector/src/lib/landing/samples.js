/**
 * Queries, comparison pairs, pipeline stages and FAQ for the landing page.
 *
 * Every entry here is a real question about a provision that is actually in
 * the index. Nothing on this page is pre-recorded: the batch section runs
 * these through the live API and prints whatever comes back, including an
 * error if one does.
 */

/** Provisions the fixtures file holds verbatim text for, in section order. */
export const FIXTURE_CATALOG = [
  { actId: "bns", code: "BNS", section: "101", title: "Murder", chars: 6373 },
  { actId: "bns", code: "BNS", section: "103", title: "Punishment for murder", chars: 455 },
  { actId: "ipc", code: "IPC", section: "302", title: "Punishment for murder", chars: 143 },
  { actId: "ipc", code: "IPC", section: "124A", title: "Sedition", chars: 1047 },
  { actId: "bns", code: "BNS", section: "152", title: "Act endangering sovereignty of India", chars: 918 },
  { actId: "bnss", code: "BNSS", section: "144", title: "Order for maintenance", chars: 4153 },
];

/** The eight queries the batch ledger runs, one HTTP call each, on demand. */
export const BATCH_QUERIES = [
  {
    q: "What is the punishment for murder under the Bharatiya Nyaya Sanhita?",
    expects: "BNS 103",
  },
  {
    q: "What are the exceptions to the definition of murder in BNS Section 101?",
    expects: "BNS 101",
  },
  {
    q: "Does Section 302 of the Indian Penal Code still apply to offences committed before the new criminal laws?",
    expects: "IPC 302",
  },
  {
    q: "What does Section 124A of the Indian Penal Code say about sedition?",
    expects: "IPC 124A",
  },
  {
    q: "What does Section 152 of the Bharatiya Nyaya Sanhita punish?",
    expects: "BNS 152",
  },
  {
    q: "Under Section 144 of the Bharatiya Nagarik Suraksha Sanhita, who is liable to maintain a wife, child or parent?",
    expects: "BNSS 144",
  },
  {
    q: "What is the provision of the Bharatiya Nyaya Sanhita corresponding to Section 302 of the Indian Penal Code?",
    expects: "BNS 103",
  },
  {
    q: "Which section of the Indian Penal Code deals with sedition and what is its punishment?",
    expects: "IPC 124A",
  },
];

/** Only the requested side is sent; the API resolves and asserts the counterpart. */
export const COMPARE_SECTIONS = [
  { act: "IPC", section: "302" },
  { act: "IPC", section: "304" },
  { act: "IPC", section: "124A" },
  { act: "IPC", section: "420" },
  { act: "IPC", section: "498A" },
  { act: "IPC", section: "376" },
  { act: "IPC", section: "34" },
];

/**
 * Ingest pipeline, one row per step that actually runs.
 * Names and artefacts come from each file's own docstring.
 */
export const INGEST_STEPS = [
  {
    n: "02",
    name: "Inspect",
    file: "step2_inspect.py",
    detail:
      "Read the PDF, locate the table of contents, and extract the expected section list. That list is the authority segmentation is held against. No ToC means the run stops, unless the registry has authorised sequence-only fallback.",
    writes: "expected.json, toc_meta.json, markers.json",
  },
  {
    n: "03",
    name: "Clean",
    file: "step3_clean.py",
    detail:
      "Drop only lines that carry a rule label — page number, separator, footnote, header, boilerplate. A section never ends at the first footnote; its text resumes on the following lines.",
    writes: "clean.json",
  },
  {
    n: "04",
    name: "Segment",
    file: "step4_segment.py",
    detail:
      "Cut each section into parts of at most 3,000 characters. A cut is legal only at bracket balance, only before the provision's own clause list is opened, and never inside an Explanation, Illustration or proviso.",
    writes: "segments.json",
  },
  {
    n: "05",
    name: "Records",
    file: "step5_records.py",
    detail:
      "Assemble the 27-key section records, one JSON object per line, and log the page-join continuity evidence that proves a section's text survived the footnote removals.",
    writes: "output/<act>.jsonl",
  },
  {
    n: "06",
    name: "Validate",
    file: "step6_validate.py",
    detail:
      "Nine gates over the assembled records: whitelist and hyphen joins, page-run integrity, numbering continuity, and the re-scans that prove no section was lost between the expected list and the output.",
    writes: "gate evidence",
  },
  {
    n: "08",
    name: "Corpus",
    file: "step8_corpus.py",
    detail:
      "Rebuild the production corpus so the dense leg and the BM25 leg share one id space and one text source. Retrieval fuses them by id; a mismatch between the two would silently break fusion.",
    writes: "eval_corpus.jsonl",
  },
  {
    n: "09",
    name: "Push",
    file: "step9_push.py",
    detail:
      "Embed with nemotron-3-embed-1b at 2,048 dimensions, cosine, and upsert into Pinecone. The dense leg and the evaluation's BM25 leg share one id space and one text source (metadata.document).",
    writes: "Pinecone upsert",
  },
];

/** High-level uncached search path; matches the three timed stages the API returns. */
export const QUERY_STAGES = [
  { id: "route", name: "Route", detail: "Classify the query and choose whether corpus retrieval applies." },
  { id: "retrieve", name: "Retrieve", detail: "Search the legal index for a legal-research request." },
  { id: "generate", name: "Generate", detail: "Build a response from the retrieved results, with confidence and a hallucination summary." },
];

/** The nine gates step6_validate.py runs (G1–G9), in the order the validator prints them. */
export const VALIDATION_GATES = [
  "Act identity holds on sampled pages",
  "Every expected section is accounted for",
  "Each record starts with its own section number",
  "Cleaned text matches the raw document",
  "All 27 record keys present",
  "Re-scan proves text survived verbatim",
  "Section order is preserved",
  "Part sizes within the limit, or flagged whole",
  "Footnote removals fully accounted for",
];

export const FAQ = [
  {
    q: "Where does the text come from?",
    a: "The API accepts PDFs and processes them through EnhancedHectorIngestor. Its current section-aware chunker recognises section boundaries; long sections may be split at sub-section or paragraph boundaries, and very short sections may be merged. The seven-step display on this page documents a separate v2 workflow, not a live API ingestion run.",
  },
  {
    q: "Does HECTOR give legal advice?",
    a: "No. Search and comparison responses may include retrieved text and source references, but citations and confidence values do not guarantee legal correctness. Check the authoritative statute and consult a qualified legal professional.",
  },
  {
    q: "Can the comparison tool always find a counterpart?",
    a: "The search and comparison interfaces accept references to older and newer codes. A corresponding provision is not guaranteed: the comparison endpoint may return no counterpart when it cannot resolve one. Check any proposed mapping against the authoritative texts.",
  },
  {
    q: "How do I know what is actually indexed?",
    a: "The record count is read from the service's unauthenticated readiness probe when the page loads; it is hidden if the request fails. Search and comparison panels call the live API. Grammar and chunking labs use bundled browser-side fixtures, not live records.",
  },
  {
    q: "What happens when the system is not confident?",
    a: "Search responses include a confidence value and may include a hallucination summary. The response generator abstains when it receives no results. Neither confidence nor citations guarantee legal correctness; review the returned sources directly.",
  },
  {
    q: "Can I see the chunking rules?",
    a: "The grammar panel shows a browser-side copy of patterns from the repository's v2 workflow, with source file and line references. The chunking lab runs that scanner against bundled sample text. These panels demonstrate code behavior; they are not a live trace of the current API ingestion path.",
  },
];
