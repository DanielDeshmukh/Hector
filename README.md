<div align="center">

# HECTOR

### Hierarchical Evaluation of Civil-Criminal Textual's Orchestrator & Retrieval

[![CI/CD](https://github.com/DanielDeshmukh/Hector/actions/workflows/ci.yml/badge.svg)](https://github.com/DanielDeshmukh/Hector/actions)
[![Tests](https://img.shields.io/badge/tests-1081%20passed-brightgreen)](#test-suite)
[![Stars](https://img.shields.io/github/stars/DanielDeshmukh/Hector?style=flat&color=yellow)](https://github.com/DanielDeshmukh/Hector/stargazers)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://www.python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**A production-grade, zero-hallucination RAG system for Indian legal intelligence.**

</div>

---

## System Overview

HECTOR is a hard-RAG legal reasoning engine purpose-built for Indian Law. It maps the transition from the Indian Penal Code (IPC) to the Bharatiya Nyaya Sanhita (BNS), grounding every response in verified Bare Act citations with a strict chain-of-verification pipeline that flags unverifiable claims instead of guessing.

### Core Design Principles

- **Zero hallucination** — Every citation is verified against the source corpus before delivery
- **Section-aware chunking** — Documents split at legal section boundaries, never mid-sentence
- **Temporal integrity** — IPC-to-BNS mappings validated against the 2024 repeal timeline
- **Deterministic retrieval** — Hybrid BM25 + semantic search with cross-encoder reranking
- **Defense in depth** — 4 verification layers: citation grounding, temporal validation, BNS section bounds, and chain-of-verification

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         INTERFACE LAYER                              │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐                 │
│  │  React SPA   │  │  REST API    │  │   CLI     │                 │
│  │  (Vite/TW)   │  │  (FastAPI)   │  │  (Typer)  │                 │
│  └──────┬───────┘  └──────┬───────┘  └─────┬─────┘                 │
│         └─────────────────┴────────────────┘                        │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
┌─────────────────────────────────▼───────────────────────────────────┐
│                        QUERY PIPELINE                                │
│                                                                     │
│  ┌──────────┐  ┌───────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │  Entity   │  │  Intent   │  │  Hybrid  │  │  Chain-of-       │  │
│  │  Parser   │→ │  Router   │→ │ Retriever│→ │  Verification    │  │
│  │  (regex)  │  │(embedding)│  │ (BM25+   │  │  (citation +     │  │
│  │           │  │           │  │  vector) │  │   temporal check) │  │
│  └──────────┘  └───────────┘  └──────────┘  └──────────────────┘  │
│                                                                     │
│  ┌───────────────┐  ┌────────────────┐  ┌───────────────────────┐  │
│  │   Query       │  │    Entity      │  │    Response           │  │
│  │   Expander    │  │    Reranker    │  │    Generator          │  │
│  │  (synonyms)   │  │  (score boost) │  │  (citation grounded)  │  │
│  └───────────────┘  └────────────────┘  └───────────────────────┘  │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
┌─────────────────────────────────▼───────────────────────────────────┐
│                         DATA LAYER                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │   ChromaDB   │  │  BM25 Index  │  │  45 Bare Acts &          │  │
│  │  (semantic)  │  │  (keyword)   │  │  Commentaries (~17,800   │  │
│  │              │  │              │  │  section-aware chunks)    │  │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Pipeline Stages

| Stage | Module | Purpose |
|-------|--------|---------|
| **Entity Extraction** | `core/query_parser.py` | Regex-based extraction of act names (107 known acts), sections, topics, courts (17 jurisdictions), and articles from natural language queries |
| **Intent Routing** | `core/embedding_router.py` | Sentence-transformers cosine similarity classifies query intent into LEGAL_RESEARCH, DOCUMENT_ANALYSIS, PRECEDENT, or GENERAL |
| **Query Expansion** | `core/query_expander.py` | Legal synonym dictionary expands queries with related terms (e.g., "murder" → "culpable homicide", "section 302") |
| **Hybrid Retrieval** | `data/hybrid_retriever.py` | BM25 keyword + semantic vector search fused via Reciprocal Rank Fusion, reranked by cross-encoder (`ms-marco-MiniLM-L-6-v2`) |
| **Entity Reranking** | `core/entity_reranker.py` | Score boosting for matches on section numbers, act names, topic keywords, and constitutional articles |
| **Chain-of-Verification** | `core/verifier.py` | 4-layer verification: citation grounding, temporal validation, BNS section bounds (≤395), hallucination detection |
| **Response Generation** | `core/response_generator.py` | Generates citation-grounded answers with IPC↔BNS comparison tables, source attributions, and confidence scores |

---

## Verification Layers

HECTOR employs four independent verification mechanisms to prevent legal misinformation:

```
Query → Retrieved Chunks → Citation Grounding → Temporal Validation
                                                    ↓
Answer ← Confidence Score ← BNS Bounds Check ← Hallucination Scan
```

| Layer | What It Checks | Failure Mode |
|-------|---------------|-------------|
| **Citation Grounding** | Every cited section exists in retrieved source text | Unverifiable claims flagged, not guessed |
| **Temporal Validation** | IPC sections cited as "current law" are checked against the July 2024 repeal | Repealed law flagged as historical context only |
| **BNS Section Bounds** | BNS section numbers must be ≤ 395 (the actual maximum) | Invalid section numbers rejected |
| **Chain-of-Verification** | Response claims cross-checked against source for factual consistency | Contradictions surfaced to user |

---

## Security

| Mechanism | Implementation |
|-----------|---------------|
| **Authentication** | HMAC-SHA256 JWT tokens with configurable expiry |
| **API Key Storage** | bcrypt hashing for at-rest key storage |
| **Rate Limiting** | Per-key token bucket algorithm with configurable refill rate |
| **CORS** | Configurable origin allowlist |
| **Health Probes** | `/healthz` (liveness) and `/readyz` (readiness) for orchestrators |
| **Input Validation** | Pydantic models enforce strict request schemas |

---

## Corpus

| Metric | Value |
|--------|-------|
| Total documents | 45 PDFs |
| Legal domains covered | 80+ topics |
| IPC→BNS mappings | 495 cross-references |
| Court jurisdictions | 17 (Supreme Court, 25 High Courts, tribunals) |
| Known act names | 107 (with real-name extraction from PDF content) |
| Chunk strategy | Section-aware (never splits mid-section) |
| Deduplication | Content-hash based, survives reindex crashes |

### Covered Domains

Criminal Law · Family Law · Constitutional Law · Commercial Law · Intellectual Property · Tax Law · Environmental Law · Telecom Law · Labor Law · Education Law · Cyber Law · RTI · Evidence Law · Property Law · Insurance · Banking · Juvenile Justice · Prevention of Corruption · Narcotics · National Security

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI, Python 3.11+ |
| Vector Database | ChromaDB |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) |
| Reranker | Cross-encoder (`ms-marco-MiniLM-L-6-v2`) |
| Intent Router | Local sentence-transformers (cosine similarity) |
| LLM (optional) | Groq (`llama-3.3-70b-versatile`) |
| Frontend | Vite 5, React 18, Tailwind CSS 4 |
| OCR | Tesseract 5, Poppler, pdf2image |
| Auth | HMAC-SHA256 JWT, bcrypt |
| Rate Limiting | Token bucket (per-key, sliding refill) |
| CLI | Typer |
| Testing | pytest (1,081 tests) |
| Linting | ruff (format + check) |

---

## Test Suite

```
1,081 tests · 0 failures · 1 skipped
```

| Category | Coverage |
|----------|----------|
| Query Parser | Entity extraction, act name resolution, section parsing |
| Embedding Router | Intent classification, confidence scoring |
| Query Expander | Legal synonym expansion |
| Entity Reranker | Score boosting, topic matching |
| Legal Chunker | Section boundary detection, metadata enrichment |
| Nemo Retriever | Provider abstraction, fallback logic |
| Retrieval Accuracy | End-to-end legal QA against 25 curated test pairs |
| Rate Limiting | Token bucket behavior, window expiration, key isolation |
| Auth Flow | JWT lifecycle, API key verification, bcrypt hashing |
| Enhanced Ingestor | PDF processing, content-hash dedup, chunk generation |
| Verifier | Citation grounding, temporal validation, BNS bounds |
| API Endpoints | Search, compare, route, health, auth |
| Frontend Components | Response rendering, pipeline display, document panel |

---

## API Reference

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/search` | API Key / JWT | Hybrid legal search with full pipeline |
| `POST` | `/compare` | API Key / JWT | IPC ↔ BNS section comparison |
| `POST` | `/route` | API Key / JWT | Intent classification |
| `POST` | `/ingest` | API Key / JWT | PDF ingestion trigger |
| `GET` | `/status` | API Key / JWT | System health + ChromaDB stats |
| `GET` | `/healthz` | None | Kubernetes liveness probe |
| `GET` | `/readyz` | None | Kubernetes readiness probe |
| `POST` | `/auth/token` | API Key | JWT bearer token issuance |
| `WS` | `/ws/search` | Query param | Streaming search events |

---

## Project Structure

```
Hector/
├── api/                        # FastAPI application layer
│   ├── app.py                  # Routes, middleware, CORS
│   ├── security.py             # AuthManager, JWT, bcrypt hashing
│   ├── rate_limit.py           # Token bucket rate limiter
│   ├── services.py             # Business logic, score normalization
│   └── schemas.py              # Pydantic request/response models
├── core/                       # Reasoning engine
│   ├── orchestrator.py         # Pipeline coordinator
│   ├── query_parser.py         # Entity extraction (107 acts, 17 courts)
│   ├── embedding_router.py     # Cosine similarity intent classifier
│   ├── query_expander.py       # Legal synonym expansion
│   ├── entity_reranker.py      # Score boosting with real act names
│   ├── legal_chunker.py        # Section-aware document splitter
│   ├── hybrid_retriever.py     # BM25 + semantic + cross-encoder
│   ├── verifier.py             # Chain-of-Verification (4 layers)
│   ├── response_generator.py   # Citation-grounded response builder
│   ├── embedding_provider.py   # Local + Nemotron embedding factory
│   ├── rerank_provider.py      # Local + Nemotron rerank factory
│   ├── nemo_retriever.py       # Unified NVIDIA NeMo retriever
│   └── mapping.json            # 495 IPC→BNS cross-references
├── utils/                      # Ingestion pipeline
│   ├── enhanced_ingestor.py    # PDF → ChromaDB with content-hash dedup
│   ├── legal_structure_parser.py # Legal document structure extraction
│   ├── ingestor.py             # Base ingestion utilities
│   └── diagnostics.py          # System health diagnostics
├── data/Books/                 # PDF corpus (45 Bare Acts)
├── frontend/                   # React SPA
│   └── src/
│       ├── api/hectorApi.js    # API client with real_act_name support
│       └── components/
│           ├── ResponseDisplay.jsx   # Confidence badges, warnings, provisions
│           ├── PipelineStatus.jsx    # Per-stage timing display
│           └── DocumentPanel.jsx     # Document metadata display
├── tests/                      # 1,081 test cases
├── benchmark/                  # Performance regression framework
├── evaluation/                 # RAG quality evaluation (RAGAS)
├── docker-compose.yml          # Container orchestration
└── requirements.txt            # Python dependencies
```

---

## Environment Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `HECTOR_API_KEY` | **Yes** | — | API authentication key |
| `HECTOR_JWT_SECRET` | **Yes** | — | JWT signing secret (min 32 chars) |
| `HECTOR_JWT_EXPIRY_SECONDS` | No | `3600` | Token lifetime |
| `HECTOR_ROUTER_MODEL` | No | `llama-3.3-70b-versatile` | Groq model for routing |
| `HECTOR_BOOKS_DIR` | No | `./data/Books` | PDF corpus directory |
| `HECTOR_DB_PATH` | No | `./hector_db` | ChromaDB storage path |
| `HECTOR_EMBEDDING_PROVIDER` | No | `local` | `local` or `nemotron` |
| `HECTOR_RERANK_PROVIDER` | No | `local` | `local` or `nemotron` |
| `HECTOR_NEMO_RETRIEVER_ENABLED` | No | `false` | Unified NeMo retriever |
| `HECTOR_TESSERACT_CMD` | No | `tesseract` | Tesseract OCR path |
| `HECTOR_POPPLER_PATH` | No | — | Poppler bin directory |
| `HECTOR_CORS_ORIGINS` | No | `http://localhost:3000` | Comma-separated origins |
| `HECTOR_LOG_LEVEL` | No | `INFO` | Logging level |
| `HECTOR_DEBUG` | No | `false` | Debug mode |
| `GROQ_API_KEY` | No | — | Groq API key for LLM routing |
| `NVIDIA_API_KEY` | No | — | NVIDIA NIM API key |

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

<div align="center">

**Built for the Indian legal ecosystem.**

*Not a substitute for professional legal advice. Always consult a qualified legal professional.*

</div>
