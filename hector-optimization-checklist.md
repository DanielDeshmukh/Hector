# HECTOR Optimization Checklist — Accuracy + Speed + Model Selection

## PART 1: Retrieval Accuracy (50% → 90-94%)

- [ ] **Metadata-filtered retrieval** — tag every chunk with `act`, `section_number`, `chapter` at ingest. When entity parser extracts a section number, filter to that section FIRST, then semantic-rank within the filtered set (not global search + boost). *Biggest single fix — resolves wrong-section retrieval (Q1, 5, 7, 10, 18).*
- [ ] **Fix chunk boundaries** — ensure chunks don't span two sections. Boundary bleed causes false matches.
- [ ] **Rule-first intent routing** — don't route to GENERAL just because no "section/act" keyword is present. Pre-check against a legal-topic embedding/keyword set before the LLM router runs. *Fixes Q14, Q17 (currently 0% from misrouting, not bad retrieval.)*
- [ ] **Expand synonym dictionary via corpus, not hand-writing** — auto-generate section-topic mappings from each Act's own definitions/headers at ingest time (one-time LLM pass, cached), instead of manually maintaining 500+ entries.
- [ ] **Weight primary source over commentary** — tag Bare Act text vs. commentary separately; retrieve primary first, fall back to commentary only if weak match. Fixes the "more data made it worse" regression.
- [ ] **Verify entity reranker checks correctness, not just presence** — a chunk mentioning "Section 302" isn't necessarily *about* Section 302; reranker should confirm the chunk's own metadata tag matches, not just substring match.
- [ ] **Re-run LLM-judge eval after each fix** to isolate which change moved the needle — don't batch all five and lose the signal.

Expected: metadata filtering + routing fix alone ≈ +35-40 points. Remaining points come from expansion/weighting — last 4-6% (94%+) gets expensive (query ambiguity, judge strictness), diminishing returns.

## PART 2: Retrieval Speed ("instantaneous")

- [ ] **Pre-filter before embedding search** — metadata filtering (Part 1) also cuts search space, so it's a speed win too, not just accuracy.
- [ ] **Cache embeddings, don't recompute** — ensure query embedding + all chunk embeddings are computed once and reused; verify you're not re-embedding the corpus per query.
- [ ] **Use ANN index, not brute-force cosine** — confirm ChromaDB is using HNSW indexing (default) not exact search; check `hnsw:space` config is set correctly for your collection size.
- [ ] **Reduce reranking scope** — cross-encoder reranking is the slowest step; only rerank top-20 candidates post-filter, not the full retrieved set.
- [ ] **Parallelize BM25 + semantic search** — run both retrieval paths concurrently (asyncio/threads), fuse after, instead of sequentially.
- [ ] **Cache repeated/common queries** — legal queries cluster around common sections (302, 376, 498A etc.); cache final responses for exact or near-duplicate queries with short TTL.
- [ ] **Batch NIM calls where possible** — avoid sequential LLM calls in the pipeline (router → expansion → generation → verification) if any can be merged into one prompt/call.
- [ ] **Profile the pipeline stage-by-stage** — measure latency at each of the 7 stages before optimizing blind; NIM inference calls are almost certainly your bottleneck, not vector search.
- [ ] **Consider a smaller/faster model for router + verifier stages** (see Part 3) — these don't need synthesis-quality reasoning.

## PART 3: Which NIM Model for Which Stage

| Stage | Task | Best-suited NIM model type | Why |
|---|---|---|---|
| Intent Router | Simple classification (4 categories) | Small/fast model (e.g. Llama 3.1 8B or smaller instruct model) | Classification doesn't need deep reasoning — speed matters more than depth here |
| Query Expansion | Synonym/mapping generation (can be pre-computed offline) | Do this OFFLINE at ingest with a larger model once, cache result — don't call NIM live per query at all |
| Response Generation | Synthesizing legal answer from retrieved chunks with citations | Larger, stronger reasoning model (Llama 3.1 70B tier if available/affordable) | This is the actual value-delivery step — quality matters most here, worth the latency cost |
| Chain-of-Verification | Citation grounding, checking claims against source chunks | Mid-size model, or even rule-based checks where possible (does cited section number appear in chunk metadata?) | Verification is largely pattern-matching against retrieved text — don't need max reasoning power; can partly replace with deterministic checks (grep-style) instead of an LLM call |
| Cross-encoder reranking | Not an LLM/NIM task | Dedicated cross-encoder model (e.g. ms-marco), not NIM | Keep this separate — it's a lightweight scoring model, not generative |

**Rule of thumb**: reserve your biggest/slowest NIM model for response generation only. Everything else (routing, verification) should use the smallest model that reliably works, or be replaced with deterministic/rule-based logic where the task is really pattern-matching, not reasoning. This is also your fastest speed win — you're likely paying 70B-model latency for tasks a classifier could do instantly.

## Priority Order (do in this sequence)

1. Metadata-filtered retrieval (accuracy + speed)
2. Rule-first intent routing (accuracy)
3. Profile pipeline latency stage-by-stage (informs everything else)
4. Right-size NIM model per stage (speed)
5. Parallelize retrieval paths + cache queries (speed)
6. Corpus-driven query expansion (accuracy)
7. Primary-vs-commentary weighting (accuracy, fixes regression)
8. Re-eval after each step, don't batch changes
