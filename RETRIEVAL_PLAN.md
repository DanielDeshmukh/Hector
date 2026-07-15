# HECTOR Retrieval Accuracy Improvement Plan

## Current State
- **Overall accuracy**: 64% (was 53% before pipeline v2)
- **Exact matches**: 61% ✅
- **Similar/paraphrased**: 32% ⚠️ (main weakness)
- **Irrelevant rejection**: 99% ✅
- **Tests**: 123 passing

## What We Built (Pipeline v2)
- Phase A: Query Parser (entity extraction)
- Phase B: Embedding Router (cosine similarity)
- Phase C: Query Expansion (synonym dictionary)
- Phase D: Entity Re-ranking (score boosting)

## What the Skills Tell Us to Fix Next

### Priority 1: Section-Level Chunking (P0)
**Source**: `hector-rag-accuracy.skill` Section 1
> "Never split mid-section. A Section is the atomic unit."

**Problem**: Our chunks are fixed-size (512 tokens). A 200-token section gets merged with the next section, and a 1000-token section gets split in half. This causes:
- "Section 302 IPC" returns text from Section 303
- Provisos retrieved without their parent rule
- Wrong section cited as current law

**Task**: Rewrite ingestion to split at section boundaries:
1. Parse PDF structure (Act → Chapter → Section)
2. Create chunks per section (not per token count)
3. Keep provisos/exceptions attached to parent clause
4. Prepend Act name + Chapter + Section as text inside chunk

### Priority 2: IPC→BNS Supersession Tracking (P0)
**Source**: `hector-rag-accuracy.skill` Section 2
> "IPC was replaced by BNS in 2023. Retrieving repealed law as current is the worst failure mode."

**Problem**: Our DB doesn't track which laws are current vs. superseded. When someone asks "Section 302 IPC", we should:
1. Map to BNS equivalent (Section 103)
2. Return BNS as primary, IPC as historical reference
3. Never cite repealed IPC sections as current law

**Task**: Add metadata fields:
- `effective_date`: When this section came into force
- `superseded_by`: What replaced it (if anything)
- `status`: "current" | "repealed" | "amended"

### Priority 3: Denormalized Context in Chunks
**Source**: `hector-rag-accuracy.skill` Section 1
> "Prepend Act name, Chapter title, and Section number as text inside the chunk"

**Problem**: Dense embeddings need the legal context in the semantic content, not just metadata. A chunk titled "Section 415: Cheating" without the Act name in the text may not retrieve when queried with "Indian Penal Code cheating".

**Task**: Transform chunk format:
```
[Indian Penal Code, 1860 | Chapter XVII: Offences Against Property | Section 415: Cheating]
Whoever, by deceiving any person...
```

### Priority 4: Formal Eval Set with Labeled Chunk IDs
**Source**: `hector-rag-accuracy.skill` Section 6 + `references/eval-harness.md`
> "30-50 labeled (query → correct_chunk_ids[]) pairs. Measure recall@5 and MRR."

**Problem**: Our current test suite measures route accuracy and keyword matching, not whether the right chunk was retrieved. We need:
- Labeled eval set: query → expected chunk_ids
- Metrics: recall@5 and MRR (not just keyword match)
- Track hard failures (recall@5 = 0) separately

**Task**: Create `evaluation/retrieval_eval.json` with 50 labeled queries.

### Priority 5: Improve Similar/Paraphrased Queries (32% → 60%+)
**Source**: Current test results show this is the weakest category.

**Root causes**:
1. "How to file a case against someone who took dowry" → missing "dowry" in LEGAL_KEYWORDS
2. "Can a minor enter into a valid contract" → no "contract" + "minor" combination
3. "What is the punishment for driving under influence" → "driving under influence" not in dictionary

**Task**: 
- Expand LEGAL_KEYWORDS in router
- Add more synonym groups to query expander
- Add "natural language → statutory" mapping table

## Implementation Order

| Phase | Task | Est. Time | Impact |
|-------|------|-----------|--------|
| 1 | Section-level chunking | 2-3 hours | +15% accuracy |
| 2 | IPC→BNS supersession tracking | 1-2 hours | Correctness (P0) |
| 3 | Denormalized context in chunks | 1 hour | +5% accuracy |
| 4 | Formal eval set (50 queries) | 1-2 hours | Measurable quality |
| 5 | Expand similar/paraphrased handling | 1-2 hours | +10% accuracy |

**Total**: 6-10 hours of work
**Expected result**: 64% → 85%+ accuracy

## Commits (per phase)
Each phase gets its own branch and commit:
- `feat/retrieval-section-chunking`
- `feat/retrieval-supersession-tracking`
- `feat/retrieval-denormalized-chunks`
- `test/retrieval-eval-set`
- `feat/retrieval-paraphrase-improvement`

## Notes
- The `rag-blueprint` skill is for NVIDIA RAG Blueprint deployment (Docker/K8s), not directly applicable to our custom Python pipeline
- The `hector-rag-accuracy.skill` is the actionable playbook for our system
- We should install `rag-eval` skill when available for RAGAS scoring
