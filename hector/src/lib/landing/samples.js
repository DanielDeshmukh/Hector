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
      "Embed with nemotron-3-embed-1b at 2,048 dimensions, cosine, and upsert into Pinecone. The same embeddings are reused for both the index and the evaluation's BM25 leg.",
    writes: "Pinecone upsert",
  },
];

/** The four stages the query pipeline reports on every request. */
export const QUERY_STAGES = [
  { id: "route", name: "Route", detail: "Classify the question and select the corpus slice." },
  { id: "retrieve", name: "Retrieve", detail: "Hybrid dense and lexical search, fused by record id." },
  { id: "assemble", name: "Assemble", detail: "Pull parent provisions so a clause is never quoted alone." },
  { id: "verify", name: "Verify", detail: "Re-check every citation against the source text before answering." },
];

/** Gates step6_validate.py enforces; shown as a compact manifest, not a claim. */
export const VALIDATION_GATES = [
  "Whitelist only removes labelled noise",
  "Hyphen joins restored across line breaks",
  "Page-run continuity preserved",
  "Section numbering strictly increasing",
  "Every expected section accounted for",
  "No orphan fragments between sections",
  "Amendment markers preserved, not stripped",
  "Provision headers survive cleaning",
  "Record ids stable across rebuilds",
];

export const FAQ = [
  {
    q: "Where does the text come from?",
    a: "Bare Acts and the Constitution of India, as published PDFs. Each file is inspected for its table of contents, cleaned line by line against a rule set, segmented, validated by nine gates, and only then embedded. The pipeline does not paraphrase or summarise at ingest time; the units in the index are the statute's own text.",
  },
  {
    q: "Does HECTOR give legal advice?",
    a: "No. It retrieves provisions and shows the citations it used. Every answer on this page is the live system responding to a real question, and the provision it grounded on is printed beside it. Read the provision, not the paraphrase.",
  },
  {
    q: "Why are the old codes still in the corpus alongside the new ones?",
    a: "Because the questions still get asked. The Bharatiya Nyaya Sanhita, Bharatiya Nagarik Suraksha Sanhita and Bharatiya Sakshya Adhiniyam replaced the IPC, CrPC and Indian Evidence Act, but the conduct being asked about frequently predates them. Both sets are indexed, and the comparison tool maps a provision across the two.",
  },
  {
    q: "How do I know what is actually indexed?",
    a: "This page asks the index. The record count beside the hero is a live reading from the service's readiness probe, not a figure typed into the source. If the index is down, the figure disappears rather than freezing at a stale number.",
  },
  {
    q: "What happens when the system is not confident?",
    a: "It says so. A search response carries a confidence level and, where retrieval was thin, a warning that the answer should be treated as incomplete. The comparison endpoint will refuse to invent a correspondence and returns an explicit note when it cannot find one.",
  },
  {
    q: "Can I see the chunking rules?",
    a: "They are printed on this page, in Python, with the file and line they come from. The chunking lab runs the JavaScript port of those same rules against a real section so you can watch the cuts land — and watch a fixed-window splitter fail on the same text.",
  },
];
