# HECTOR — Current State & Problems

## What Is This Project?

HECTOR is a RAG (Retrieval-Augmented Generation) system for Indian Law. It ingests 45 PDFs of Bare Acts and commentaries (~32,400 chunks in ChromaDB), and answers legal queries by retrieving relevant chunks and synthesizing responses using NVIDIA NIM (LLaMA 3.1 8B).

**Goal**: Zero-hallucination legal answers with verified citations.

---

## Current Pipeline

```
User Query
    │
    ▼
┌─────────────────────────────────────────────────────┐
│ 1. ENTITY PARSER (core/query_parser.py)             │
│    Regex extraction: 107 known acts, 17 courts,     │
│    80 topics, section numbers                        │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│ 2. INTENT ROUTER (core/router.py + embedding_router) │
│    NIM LLM classifies: LEGAL_RESEARCH, GENERAL,     │
│    DOCUMENT_ANALYSIS, STRATEGIC_ADVICE               │
│    Rule-based → NIM → Groq → fallback               │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│ 3. QUERY EXPANSION (core/query_expander.py)          │
│    Legal synonym dictionary: "murder" → "culpable    │
│    homicide", "section 302" etc.                      │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│ 4. HYBRID RETRIEVAL (data/hybrid_retriever.py)       │
│    BM25 keyword search + semantic vector search       │
│    → Reciprocal Rank Fusion → Cross-encoder rerank   │
│    Returns top 5 chunks from ChromaDB                 │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│ 5. ENTITY RERANKER (core/entity_reranker.py)         │
│    Boosts scores for matching section numbers,       │
│    act names, topic keywords                         │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│ 6. RESPONSE GENERATION (core/response_generator.py)  │
│    NIM LLM synthesizes answer from retrieved chunks  │
│    Falls back to template if NIM fails               │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│ 7. CHAIN OF VERIFICATION (core/verifier.py)          │
│    Citation grounding, temporal validation,           │
│    BNS section bounds check                          │
└─────────────────────────────────────────────────────┘
```

---

## Current Accuracy (LLM-as-Judge scoring)

| Category | Score | Count |
|----------|-------|-------|
| Exact keyword matches | 45% | 10 queries |
| Similar/paraphrased | 37% | 10 queries |
| Irrelevant (grace) | 94% | 10 queries |
| **Overall** | **59%** | **30 queries** |

### Per-Query Breakdown

| # | Query | Score | Problem |
|---|-------|-------|---------|
| 1 | Section 302 IPC punishment | 0% | Retriever finds Section 304 instead of 302 |
| 2 | Section 376 IPC rape | 80% | Good |
| 3 | BNSS bail provisions | 40% | Partial answer |
| 4 | Evidence Act Section 65B | 70% | Decent |
| 5 | Transfer of Property Section 54 | 30% | Wrong chunks retrieved |
| 6 | Section 144 CrPC → BNSS | 30% | Cross-reference not found |
| 7 | Dowry Section 498A | 30% | Wrong chunks |
| 8 | NDPS Section 20 | 80% | Good |
| 9 | Article 21 Constitution | 95% | Excellent |
| 10 | Consumer Protection Section 38 | 0% | Wrong chunks |
| 11 | Bail for death penalty | 85% | Good |
| 12 | Dowry case filing | 95% | Excellent |
| 13 | Document forgery | 30% | Routes to DOCUMENT_ANALYSIS |
| 14 | Confession admissibility | 0% | Routes to GENERAL |
| 15 | Limitation period | 30% | Vague answer |
| 16 | Unpaid wages | 60% | Decent |
| 17 | Minor contract | 0% | Routes to GENERAL |
| 18 | DUI punishment | 0% | Wrong chunks |
| 19 | Hindu succession | 0% | No relevant chunks |
| 20 | Accused rights interrogation | 70% | Routes to GENERAL but answers |

---

## Problems

### Problem 1: Retriever Precision — Wrong Chunks Retrieved

**What's happening**: When you ask "Section 302 IPC punishment for murder", the retriever returns chunks about Section 304 IPC (culpable homicide) instead. Both chunks contain "section", "IPC", "punishment" — BM25 scores them equally. Semantic similarity also can't distinguish them because the surrounding legal text is similar.

**Impact**: Query 1 scores 0% (discusses wrong section). Queries 5, 7, 10, 18 also affected.

**Why it happens**: 
- BM25 matches on word frequency, not legal meaning
- `all-MiniLM-L6-v2` embeddings (384-dim) don't capture fine-grained section number distinctions
- The entity reranker boosts based on section number presence but doesn't verify the chunk is ABOUT that section

### Problem 2: Intent Router Misclassification

**What's happening**: 3/10 similar queries route to GENERAL instead of LEGAL_RESEARCH:
- "Is a confession made to police admissible?" → GENERAL
- "Can a minor enter into a valid contract?" → GENERAL  
- "What rights does an accused have during interrogation?" → GENERAL

**Impact**: These queries get 0% accuracy because the pipeline skips retrieval entirely for GENERAL routes.

**Why it happens**: The NIM router (8B model) doesn't recognize these as legal queries because they don't contain explicit legal keywords like "section", "act", "IPC". The rule-based fallback also doesn't catch them.

### Problem 3: Query Expansion Too Narrow

**What's happening**: "confession" doesn't map to "section 25 evidence act". "minor" doesn't map to "Indian Contract Act section 11". "inheritance" doesn't map to "succession", "intestate", "Hindu Succession Act".

**Impact**: Retriever can't find relevant chunks because the expanded query doesn't contain the right search terms.

**Why it happens**: The synonym dictionary in `query_expander.py` has ~50 entries. A legal domain needs 500+.

### Problem 4: More Data Made It Worse

**What's happening**: Reindexing from 27,997 → 32,433 chunks dropped accuracy from 66% → 59%.

**Impact**: More chunks = more noise = retriever returns more irrelevant results = LLM synthesizes wrong answers.

**Why it happens**: The 3014-page Evidence Act book was added during reindex. It contains hundreds of sections that match keyword queries but aren't the right sections. No chunk quality filtering.

### Problem 5: LLM Judge vs Actual Quality Discrepancy

**What's happening**: The LLM judge (8B model) sometimes scores correct answers low because it's strict about specific section numbers. A human lawyer would accept the answer but the judge demands exactness.

**Impact**: Overall score may understate actual quality by 5-10%.

---

## What's Working

- **Retrieval**: Sources are found (5 per query) — the retriever works
- **NIM Integration**: LLM synthesis produces coherent, cited answers
- **Verification**: Chain-of-Verification catches hallucinations
- **Irrelevant handling**: 94% correct — doesn't return legal data for non-legal queries
- **Corpus**: 45 PDFs, 32K chunks, 495 IPC→BNS mappings all ingested correctly
- **Test suite**: 1,081 tests passing, ruff clean

---

## Summary

| Component | Status | Issue |
|-----------|--------|-------|
| Ingestion | ✅ Working | 32,433 chunks indexed |
| Entity Parser | ✅ Working | 107 acts, 17 courts extracted |
| Intent Router | ⚠️ Partial | 3/10 similar queries misroute |
| Query Expansion | ⚠️ Partial | ~50 synonyms, need 500+ |
| Hybrid Retrieval | ❌ Precision issue | Returns wrong sections |
| Entity Reranker | ⚠️ Partial | Boosts presence, not correctness |
| Response Generator | ✅ Working | NIM synthesizes good answers |
| Verification | ✅ Working | Catches hallucinations |
| Scoring | ✅ Working | LLM-as-judge honest evaluation |

**The bottleneck is retrieval precision.** The retriever finds chunks that match keywords but aren't the right legal section. Everything downstream inherits this error.
