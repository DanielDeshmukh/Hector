# HECTOR Optimization Checklist — Accuracy + Speed + Model Selection

**Status: 15/17 complete | Accuracy: 60.9% (baseline 59%) | Speed: 37x faster for filtered queries**

## PART 1: Retrieval Accuracy (50% → 90-94%)

- [x] **Metadata-filtered retrieval** ✅ — `search_with_metadata_filters()` with `$eq` where clauses on `section_number` and `real_act_name`. `feat/metadata-filtered-retrieval` branch.
- [x] **Fix chunk boundaries** ✅ — `_find_other_section_refs()` detects cross-section bleed during merge. Chunks no longer span two sections.
- [x] **Rule-first intent routing** ✅ — `LEGAL_TOPICS` (80+ legal concept keywords) in `core/router.py`. Fixes misrouting of "confession", "minor", "contract", "accused" queries.
- [x] **Expand synonym dictionary via corpus** ✅ — `auto_synonyms.json` with 64 concepts, 668 entries extracted from 42 acts' section headers. `QueryExpander` loads auto-generated file at init.
- [x] **Weight primary source over commentary** ✅ — `_source_type_boost()`: bare_act +0.05, commentary -0.02. All 32,433 chunks tagged with `source_type` metadata.
- [x] **Verify entity reranker checks correctness** ✅ — 3-tier section matching: metadata tag (+0.25) > citation (+0.15) > text mention (+0.05). Not just substring match.
- [x] **Re-run LLM-judge eval after each fix** ✅ — 30-query eval with category-aware LLM-as-judge scoring. Results in `retrieval_test_results_v2.json`.

**Accuracy: 60.9% overall** (Exact 59%, Similar 44.8%, Irrelevant 79%). Need +29 points to hit 90% target.

## PART 2: Retrieval Speed ("instantaneous")

- [x] **Pre-filter before embedding search** ✅ — Metadata filtering cuts search space before semantic ranking. 81ms filtered vs 3,019ms unfiltered (37x).
- [x] **Cache embeddings, don't recompute** ✅ — sentence-transformers local model cached. All 32,433 chunk embeddings computed once at ingest.
- [x] **Use ANN index, not brute-force cosine** ✅ — ChromaDB HNSW default. Collection properly configured.
- [x] **Reduce reranking scope** ✅ — Cross-encoder reranks top-20 candidates post-filter, not full retrieved set.
- [x] **Parallelize BM25 + semantic search** ✅ — `ThreadPoolExecutor(max_workers=2)` runs both paths concurrently in `hybrid_retriever.py`.
- [x] **Cache repeated/common queries** ✅ — LRU OrderedDict (100 entries) in orchestrator. Cached queries return in 0ms.
- [ ] **Batch NIM calls where possible** — Router → generation → verification still sequential. Could merge router + verification into one prompt. *Low priority — each stage needs different model (8B vs 70B).*
- [x] **Profile the pipeline stage-by-stage** ✅ — Sub-stage timing: `search_ms`, `rerank_ms`, `generate_ms` in `last_timing["sub_stages"]`. NIM generation identified as bottleneck.
- [x] **Consider a smaller/faster model for router + verifier** ✅ — Router: 8B, Generation: 70B, Verification: 8B. Right-sized per stage.

## PART 3: Which NIM Model for Which Stage

| Stage | Task | Model | Status |
|---|---|---|---|
| Intent Router | Simple classification (4 categories) | `meta/llama-3.1-8b-instruct` | ✅ |
| Query Expansion | Synonym generation (offline, corpus-driven) | Offline at ingest | ✅ |
| Response Generation | Synthesizing legal answer with citations | `meta/llama-3.3-70b-instruct` | ✅ |
| Chain-of-Verification | Citation grounding, claim checking | Groq (not NIM) | ✅ |
| Cross-encoder reranking | Lightweight scoring (not generative) | `cross-encoder/ms-marco-MiniLM-L-6-v2` | ✅ |

**Rule of thumb applied**: 70B reserved for generation only. Router + verifier use 8B or rule-based logic.

## Priority Order (completed)

1. [x] Metadata-filtered retrieval (accuracy + speed)
2. [x] Rule-first intent routing (accuracy)
3. [x] Profile pipeline latency stage-by-stage (informs everything else)
4. [x] Right-size NIM model per stage (speed)
5. [x] Parallelize retrieval paths + cache queries (speed)
6. [x] Corpus-driven query expansion (accuracy)
7. [x] Primary-vs-commentary weighting (accuracy, fixes regression)
8. [x] Re-eval after each step, don't batch changes

## Remaining Work

- [ ] **Batch NIM calls** — merge router + verification into single prompt (low priority)
- [ ] **Accuracy gap** — 60.9% → 90% target. Next moves: upgrade generation model quality, fix remaining 11 failing queries, fix chunk boundaries for mislabelled PDFs
- [ ] **Corpus quality** — many PDFs mislabelled (filename doesn't match content), OCR artifacts in section headers
