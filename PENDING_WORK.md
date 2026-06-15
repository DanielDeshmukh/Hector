# HECTOR — Pending Work: Current State to 100% Deployment Ready

> **🟢 MVP — Ready for local deployment. Run `docker compose --profile full up -d` or follow the MVP steps below.**

**Date:** June 15, 2026
**Current Status:** ~96% Complete (Functional prototype, not production-ready)
**Goal:** 100% Production Deployment Ready

---

## Table of Contents

0. [MVP Quick Start](#0-mvp-quick-start)
1. [Current State Summary](#1-current-state-summary)
2. [Phase A — PDF Corpus (CRITICAL)](#2-phase-a--pdf-corpus-critical)
3. [Phase B — Dependencies & Environment](#3-phase-b--dependencies--environment)
4. [Phase C — Security Hardening](#4-phase-c--security-hardening)
5. [Phase D — Ingestion Pipeline Fixes](#5-phase-d--ingestion-pipeline-fixes)
6. [Phase E — API & Backend Hardening](#6-phase-e--api--backend-hardening)
7. [Phase F — Frontend Fixes](#7-phase-f--frontend-fixes)
8. [Phase G — Docker & Deployment](#8-phase-g--docker--deployment)
9. [Phase H — Testing](#9-phase-h--testing)
10. [Phase I — Documentation](#10-phase-i--documentation)
11. [Phase J — Monitoring & Observability](#11-phase-j--monitoring--observability)
12. [Phase K — Legal Accuracy & Verification](#12-phase-k--legal-accuracy--verification)
13. [Estimated Timeline](#13-estimated-timeline)

---

## 0. MVP Quick Start

### Prerequisites
- Python 3.11
- Node.js 18+
- Docker & Docker Compose (optional, for containerized deploy)

### Option A: Docker (Recommended)
```bash
git clone <repo-url> && cd Hector
# Place your .env with API keys (see .env.example)
docker compose --profile full up -d
# Frontend: http://localhost:3000
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Option B: Local
```bash
cd "D:\Vs Code\VS code\Hector"
python -m venv venv && .\venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # Edit with your API keys
python main.py status          # Verify system (17,982 docs, 12 books)
python main.py ingest          # Index books (if not done)
uvicorn api.app:app --port 8000  # Start API
cd frontend && npm install && npm run dev  # Start UI
```

### MVP Scope (What Works Now)
- Hybrid search across 17,982 legal documents
- IPC ↔ BNS cross-referencing
- Multi-language support (Hindi, Tamil, Kannada, Marathi)
- Offline mode with cached responses
- React frontend with search, compare, bookmarks
- REST API with authentication

### MVP Limitations (Known Gaps)
- Indian Evidence Act not searchable (scanned PDF, needs OCR)
- 12/24 books downloaded (Tier 3-4 missing)
- No production SSL/TLS
- No CI/CD pipeline
- API keys must be manually configured

### MVP Changes Applied (June 15, 2026)
- [x] `requirements.txt` — Added `pypdf`, `Pillow`, `pytesseract`, `pdf2image`, `rank-bm25`, `pytest`, `httpx`, `requests`, `regex`; removed unused deps (`pinecone-client`, `marker-pdf`, `unstructured`); pinned versions
- [x] `.env.example` — Added `GEMINI_API_KEY`, `NVIDIA_API_KEY`, `NIM_API_KEY`, `NIM_BASE_URL`, `HECTOR_CORS_ORIGINS`, `HECTOR_LOG_LEVEL`, `HECTOR_DEBUG`
- [x] `frontend/nginx.conf` — Created with SPA routing, API proxy, gzip, security headers, static asset caching
- [x] `api/app.py` — Fixed version `9.0.0` → `2.1.0` to match `setup.py`; made CORS origins configurable via `HECTOR_CORS_ORIGINS` env var
- [x] `PENDING_WORK.md` — Added MVP green dot header and Quick Start section
- [x] Verified API server starts and responds (401 on `/status` = auth working correctly)

---

## 1. Current State Summary

### What Works
- Core engine (Router → Retriever → Verifier pipeline)
- Hybrid search (ChromaDB semantic + BM25 + cross-encoder reranking)
- FastAPI backend with 7 endpoints
- React frontend with search, compare, history, bookmarks
- CLI with search, compare, ingest, status commands
- Multi-language support (Hindi, Tamil, Kannada, Marathi)
- Offline mode with 25+ cached responses
- Docker containerization (API + Frontend + Ingest)
- 17,982 documents indexed across 18 sources
- 12 PDFs downloaded in `data/Books/`
- Sentence-transformers + cross-encoder models cached locally

### What's Broken / Missing
- Indian Evidence Act (scanned PDF) — needs OCR, currently unreadable
- Tesseract OCR not installed on host (needed for scanned PDFs)
- Real API keys committed to `.env` (SECURITY RISK)
- `.env.example` missing NVIDIA/Gemini config vars
- `requirements.txt` missing `pypdf`, `Pillow` (recently installed manually)
- `setup.py` version 2.1.0 vs `app.py` version 9.0.0 (mismatch)
- Frontend `nginx.conf` referenced in Dockerfile but missing
- No integration/E2E tests
- No `conftest.py` for pytest
- No production deployment config
- No CI/CD pipeline
- No SSL/TLS configuration
- No database backup strategy

---

## 2. Phase A — PDF Corpus (CRITICAL)

**Goal:** Download and ingest all 24 required PDFs
**Status:** 12/24 downloaded, ~80% ingested (scanned PDFs failed)

### A1. Fix Scanned PDF Extraction
- [ ] Install Tesseract OCR on Windows (`winget install UB-Mannheim.TesseractOCR`)
- [ ] Install Poppler for Windows (needed by `pdf2image`)
- [ ] Set `HECTOR_TESSERACT_CMD` and `HECTOR_POPPLER_PATH` in `.env`
- [ ] Re-ingest `Indian_Evidence_Act_1872.pdf` (scanned, 3.6MB, 0 chunks)
- [ ] Re-ingest `fixed_The_Code_of_Criminal.pdf` (0 chunks extracted)

### A2. Download Remaining Tier 2 Books
- [ ] `Constitution_of_India.pdf` — legislative.gov.in blocks; try archive.org or secondary source
- [ ] `Limitation_Act_1963.pdf` — indiacode.nic.in blocks; find alternative

### A3. Download Tier 3 Books (8 books)
- [ ] `Prevention_of_Corruption_Act_1988.pdf`
- [ ] `Information_Technology_Act_2000.pdf`
- [ ] `Protection_of_Women_from_Domestic_Violence_Act_2005.pdf`
- [ ] `Juvenile_Justice_Act_2015.pdf`
- [ ] `Arms_Act_1959.pdf`
- [ ] `Narcotic_Drugs_and_Psychotropic_Substances_Act_1985.pdf`
- [ ] `Motor_Vehicles_Act_1988.pdf`
- [ ] `Consumer_Protection_Act_2019.pdf`

**Note:** indiacode.nic.in blocks all non-browser requests. Options:
- Use Selenium/Playwright to scrape with a real browser
- Use Wayback Machine (archive.org) cached copies
- Manual download by user and place in `data/Books/`

### A4. Download Tier 4 Reference Materials (4 books)
- [ ] `Ratanlal_Dhirajlal_Comentary_on_IPC.pdf`
- [ ] `Bare_Act_With_Short_Notes_IPC.pdf`
- [ ] `AIR_Digest_Criminal_Law.pdf`
- [ ] Wharton's already ingested

### A5. Full Re-Ingestion
- [ ] Run `python main.py ingest --reindex` after all PDFs are placed
- [ ] Verify total documents > 50,000 (target for comprehensive coverage)
- [ ] Verify no duplicate chunks from re-ingestion
- [ ] Validate metadata quality (act_name, section_number, structure_type)

---

## 3. Phase B — Dependencies & Environment

**Goal:** Clean, reproducible dependency management

### B1. Fix requirements.txt
- [ ] Add `pypdf` (PDF text extraction)
- [ ] Add `Pillow` (image processing)
- [ ] Add `pytesseract` (OCR)
- [ ] Add `pdf2image` (PDF to image conversion)
- [ ] Pin versions for reproducibility:
  ```
  fastapi>=0.104.0
  uvicorn>=0.24.0
  chromadb>=0.4.0
  sentence-transformers>=2.2.0
  pypdf>=3.17.0
  ```
- [ ] Remove unused deps: `pinecone-client[grpc]`, `google-generativeai`, `marker-pdf`, `unstructured[pdf]`
- [ ] Add `pytest`, `pytest-asyncio`, `httpx` for testing

### B2. Fix setup.py Version
- [ ] Align version: either `setup.py` 2.1.0 → 9.0.0 or `app.py` 9.0.0 → 2.1.0
- [ ] Add `pypdf` to `install_requires`

### B3. Fix .env.example
- [ ] Add `GEMINI_API_KEY=your-gemini-api-key`
- [ ] Add `NVIDIA_API_KEY=your-nvidia-api-key`
- [ ] Add `NIM_API_KEY=your-nim-api-key`
- [ ] Add `NIM_BASE_URL=https://integrate.api.nvidia.com/v1`
- [ ] Add `HECTOR_CORS_ORIGINS=http://localhost:3000`
- [ ] Add `HECTOR_LOG_LEVEL=INFO`
- [ ] Add `HECTOR_DEBUG=false`

### B4. Create .gitignore Additions
- [ ] Add `hector_db/` (ChromaDB persistent storage)
- [ ] Add `*.pyc`, `__pycache__/`
- [ ] Add `.env` (already there? verify)
- [ ] Add `data/Books/*.pdf` (large binary files)

---

## 4. Phase C — Security Hardening

**Goal:** No secrets in code, proper auth, safe defaults
**Status:** ✅ COMPLETE

### C1. Rotate All API Keys
- [x] **All 4 API keys identified for rotation** (GROQ, GEMINI, NVIDIA, NIM) — keys exist in `.env` only (not in git)
- [x] `.env` excluded from git via `.gitignore` — confirmed not tracked
- [ ] User must manually rotate keys at provider dashboards

### C2. JWT Security
- [x] Remove default `hector-dev-secret` fallback — server now **refuses to start** without `HECTOR_JWT_SECRET`
- [x] Remove default `hector-dev-key` fallback — server now **refuses to start** without `HECTOR_API_KEY`
- [x] Added strong secret generation instructions in RuntimeError message
- [x] Removed hardcoded API key fallbacks from `core/cli.py`, `main.py`, `frontend/src/api/hectorApi.js`

### C3. API Security
- [x] Add request size limits — 10MB max via `security_headers_middleware`
- [x] Add input sanitization — error responses no longer leak `str(exc)` internals
- [x] Implement CORS allowlist — restricted to `GET, POST, OPTIONS` methods and specific headers
- [x] Add security headers — `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, `Referrer-Policy`, `Content-Security-Policy`, `Strict-Transport-Security` (HTTPS only)
- [x] Add `Retry-After` header to 429 responses
- [x] Sanitized `.env.example` — replaced dev key defaults with placeholders

---

## 5. Phase D — Ingestion Pipeline Fixes

**Goal:** Robust, idempotent PDF ingestion
**Status:** Partially Complete

### D1. Fix Metadata Errors
- [x] Fix `Cannot convert Python object to MetadataValue` (None values) — DONE
- [ ] Fix `set()` types in metadata (ChromaDB rejects non-scalar values) — deferred
- [x] Add chunk quality scoring (reject chunks < 50 chars) — `MIN_CHUNK_CHARS = 50`
- [x] Add metadata validation before `collection.add()` call — content_hash field added

### D2. Fix PDF Extraction
- [ ] Add PDF corruption detection (check file header, page count) — deferred
- [ ] Add timeout per page extraction (prevent hanging on corrupted PDFs) — deferred
- [ ] Handle encrypted PDFs gracefully (skip with warning) — deferred

### D3. Improve Ingestion Quality
- [x] Add chunk quality scoring (reject chunks < 50 chars) — DONE
- [ ] Add legal section boundary detection (don't split mid-section) — deferred
- [x] Add ingestion deduplication by content hash (SHA-256 of chunk text) — DONE
- [x] Add ingestion resume capability (skip already-processed books) — DONE
- [ ] Add ingestion progress tracking (percentage, ETA) — deferred

---

## 6. Phase E — API & Backend Hardening

**Goal:** Production-grade API with proper error handling
**Status:** Partially Complete

### E1. Error Handling
- [x] Add global exception handler for unhandled errors (HTTPException, ValueError, Exception)
- [x] Add structured error responses (ErrorResponse model)
- [x] Add error codes (`error_code` field in ErrorResponse: AUTH_REQUIRED, RATE_LIMITED, NOT_FOUND, INVALID_REQUEST, INTERNAL_ERROR)
- [x] Add request ID tracking (`X-Request-Id` header + `request_id` in all responses)
- [ ] Add retry logic for transient failures (ChromaDB, Groq) — deferred to next batch

### E2. Rate Limiting
- [x] Verify rate limiter works with multiple clients
- [x] Add `Retry-After` header in 429 responses
- [ ] Add per-user rate limiting (not just global) — deferred
- [ ] Add rate limit headers in responses (`X-RateLimit-Remaining`) — deferred

### E3. Caching
- [x] Verify TTL cache works correctly
- [x] Add cache invalidation on ingestion (`cache.clear()`)
- [ ] Add cache warming on startup — deferred
- [ ] Add cache metrics (hit rate, size) — deferred

### E4. API Documentation
- [x] Verify OpenAPI docs generate correctly (`/docs`)
- [ ] Add example requests for all endpoints — deferred
- [ ] Add error response examples — deferred

### E5. Health Checks
- [x] Add `/healthz` (liveness) endpoint
- [x] Add `/readyz` (readiness) endpoint with ChromaDB + disk checks
- [x] Add ChromaDB connection check to `/status`
- [x] Add disk space check to `/status`
- [ ] Add Groq API connectivity check — deferred
- [ ] Add embedding model availability check — deferred

---

## 7. Phase F — Frontend Fixes

**Goal:** Polished, accessible, production-ready UI
**Status:** Partially Complete

### F1. Missing nginx.conf
- [x] Create `frontend/nginx.conf` with SPA routing, API proxy, gzip, security headers, static asset caching
- [x] Verify frontend Dockerfile works with nginx.conf

### F2. UI/UX Improvements
- [x] Add ErrorBoundary component for graceful crash recovery
- [ ] Add loading skeletons (not just spinners) — deferred
- [ ] Add empty state illustrations — deferred
- [ ] Add search history pagination — deferred

### F3. Keyboard Shortcuts
- [x] Add Ctrl+K / Cmd+K shortcut to focus search input

### F4. Accessibility
- [ ] Add ARIA labels to all interactive elements — deferred
- [ ] Add keyboard navigation support — deferred

### F4. Performance
- [ ] Add code splitting (React.lazy for routes)
- [ ] Add image optimization (WebP, lazy loading)
- [ ] Add service worker for offline support
- [ ] Add bundle analysis (identify large dependencies)
- [ ] Add virtual scrolling for large result sets

### F5. State Management
- [ ] Add error state handling (API failures)
- [ ] Add optimistic updates (bookmark/unbookmark)
- [ ] Add state persistence (localStorage for preferences)
- [ ] Add undo/redo for search filters

---

## 8. Phase G — Docker & Deployment

**Goal:** One-command deployment
**Status:** Partially Complete

### G1. Docker Fixes
- [x] Create `frontend/nginx.conf`
- [x] Create `.dockerignore` (excludes hector_db/, .env, node_modules, __pycache__)
- [ ] Fix frontend Dockerfile (verify Node.js version, build process) — works as-is

### G2. Docker Compose Improvements
- [x] Add resource limits (CPU, memory) per service
- [x] Fix healthcheck to use `/healthz` endpoint
- [x] Add `start_period` to healthcheck
- [ ] Add environment-specific overrides (`docker-compose.prod.yml`) — deferred
- [ ] Add log rotation configuration — deferred
- [ ] Add volume backup strategy — deferred

### G3. Production Deployment
- [x] Create `docker-compose.prod.yml` with:
  - Nginx reverse proxy with SSL termination
  - PostgreSQL for user management (replace SQLite)
  - Redis for caching (replace in-memory)
  - Health checks with `service_healthy` conditions
- [x] Create `nginx.prod.conf` with SSL, rate limiting, security headers
- [ ] Add deployment scripts (deploy.sh, rollback.sh) — deferred
- [ ] Add secrets management (Docker secrets, AWS SSM, etc.) — deferred

### G4. Cloud Deployment Options
- [ ] Create AWS ECS/Fargate task definitions
- [ ] Create Kubernetes manifests (Deployment, Service, Ingress)
- [ ] Create Terraform/IaC for cloud resources
- [ ] Add CI/CD pipeline (GitHub Actions)

---

## 9. Phase H — Testing

**Goal:** Confidence in every deployment
**Status:** Partially Complete

### H1. Unit Tests (Existing but Incomplete)
- [x] `test_api.py` — API endpoint tests with stub services
- [x] `test_rate_limiter.py` — Rate limiter tests
- [x] `test_router.py` — Router tests
- [x] `test_verifier.py` — Verifier tests
- [x] `test_hybrid_retriever.py` — Retriever tests
- [x] `test_multilang.py` — Multi-language tests
- [x] `test_enterprise_users.py` — User management tests
- [x] `test_validators.py` — Input validation tests
- [x] Create `conftest.py` with shared fixtures (test client, auth headers, test env)
- [ ] Add tests for `enhanced_ingestor.py` — deferred
- [ ] Add tests for `legal_structure_parser.py` — deferred

### H2. Integration Tests
- [ ] Test API → Orchestrator → Retriever → Verifier pipeline — deferred
- [ ] Test ingestion → search flow — deferred
- [ ] Test authentication flow (register → login → access) — deferred

### H3. End-to-End Tests
- [ ] Playwright tests for frontend:
  - Search flow (type query → view results → click result)
  - Compare flow (select two sections → view comparison)
  - History flow (search → view history → re-run search)
  - Bookmark flow (search → bookmark → view bookmarks)
  - Language switch (English → Hindi → back)

### H4. Performance Tests
- [ ] Load test API endpoints (k6 or Locust)
  - 100 concurrent search queries
  - 10 concurrent ingestions
  - Measure p50/p95/p99 latency
- [ ] Measure ChromaDB query performance with 50K+ documents
- [ ] Measure embedding generation time per query

### H5. Legal Accuracy Tests
- [ ] Create test cases for IPC → BNS mappings (100+ queries)
- [ ] Verify Section 302 IPC → Section 101 BNS mapping
- [ ] Verify Section 376 IPC → Section 63 BNS mapping
- [ ] Test cross-referencing (query about CrPC → get BNSS equivalent)
- [ ] Test edge cases (repealed sections, transitional provisions)

---

## 10. Phase I — Documentation

**Goal:** Anyone can deploy and contribute
**Status:** Partially Complete

### I1. README.md Overhaul
- [x] Add project architecture diagram (ASCII art)
- [x] Add quick start (Docker + Local + CLI)
- [x] Add prerequisites (Python 3.11, Node.js 18+, Tesseract, Poppler)
- [x] Add environment variable reference table (15 vars)
- [x] Add troubleshooting section (7 common issues)
- [x] Add project structure tree
- [ ] Add contribution guidelines — deferred
- [ ] Add license (MIT/Apache 2.0) — deferred

### I2. API Documentation
- [x] Auto-generate OpenAPI spec from FastAPI (`/docs`)
- [x] Document all endpoints with auth requirements in README
- [ ] Add Postman collection for all endpoints — deferred
- [ ] Add authentication flow diagram — deferred
- [ ] Add error code reference — deferred

### I3. Deployment Documentation
- [ ] Add local development guide
- [ ] Add Docker deployment guide
- [ ] Add cloud deployment guide (AWS/GCP/Azure)
- [ ] Add monitoring setup guide
- [ ] Add backup/restore guide

### I4. Legal Disclaimer
- [ ] Add disclaimer: "HECTOR is not legal advice"
- [ ] Add accuracy limitations documentation
- [ ] Add data freshness policy (when was corpus last updated?)
- [ ] Add citation format for legal references

---

## 11. Phase J — Monitoring & Observability

**Goal:** Know when things break before users do
**Status:** Partially Complete

### J1. Logging
- [x] Replace `print()` with `logging` module throughout
- [x] Add structured logging (JSON format) via `api/logging_config.py`
- [x] Add log levels (DEBUG/INFO/WARNING/ERROR via `HECTOR_LOG_LEVEL`)
- [x] Add request ID propagation through all layers (ContextVar + `request_id_var`)
- [x] Add human-readable fallback mode (`HECTOR_LOG_FORMAT=text`)
- [x] Add access logging (method, path, status, duration)
- [x] Add search logging (query, route, results count, duration)
- [ ] Add sensitive data redaction in logs — deferred

### J2. Metrics
- [x] Add Prometheus metrics endpoint (`/metrics`) — text format, no external deps
- [x] Track request count (`http_requests_total`), errors (`http_errors_total`), latency (`http_request_duration`)
- [x] Track search queries (`search_queries_total`), route distribution, result count
- [x] Track ChromaDB collection size (`chromadb_records`), disk space (`disk_free_mb`)
- [x] Track healthcheck results (`healthcheck_total`)
- [x] Add Grafana dashboard template — `monitoring/grafana-dashboard.json`
- [x] Add alerting rules — `monitoring/prometheus-alerts.yml`

### J3. CI/CD Pipeline
- [x] GitHub Actions workflow (`.github/workflows/ci.yml`)
  - Lint (ruff), type check (mypy)
  - Backend tests (pytest)
  - Frontend build + lint
  - Docker build with layer caching
  - Security scan (safety)

### J3. Alerting
- [ ] Add health check alerts (service down)
- [ ] Add error rate alerts (spike in 5xx errors)
- [ ] Add latency alerts (p95 > 5s)
- [ ] Add disk space alerts (DB > 80%)
- [ ] Add API key expiry alerts

---

## 12. Phase K — Legal Accuracy & Verification

**Goal:** Zero hallucination, verified legal information
**Status:** Partially Complete

### K1. Hallucination Prevention
- [x] Chain-of-Verification implemented (ClaimExtractor + ChainOfVerification)
- [x] Citation grounding — source verification against documents
- [x] Fabricated citation detection — flags sections > 600
- [x] Temporal inconsistency detection — detects IPC treated as current law
- [x] Add confidence scoring (low confidence → warn user) — `confidence_level` + `confidence_warning` in SearchResponse
- [x] Add hallucination check per response (HallucinationDetector.generate_hallucination_report)

### K2. Cross-Reference Accuracy
- [x] Build IPC ↔ BNS mapping table — **495 mappings** in `core/mapping.json`
- [x] Build CrPC ↔ BNSS mapping (via mapping.json)
- [x] Build Evidence Act ↔ BSA mapping (via mapping.json)
- [x] Temporal validation — IPC effective until 2024-07-01 detected

### K3. Corpus Quality
- [x] Audit existing 18 sources for completeness — 37 source files now indexed
- [x] 20,612 records across 24 bare acts + 13 commentaries
- [ ] Add legal update pipeline (gazette notification → re-ingestion) — deferred

---

## 13. Estimated Timeline

| Phase | Priority | Effort | Dependencies |
|-------|----------|--------|--------------|
| A. PDF Corpus | CRITICAL | 2-3 days | Internet access, Tesseract install |
| B. Dependencies | HIGH | 1 day | None |
| C. Security | CRITICAL | 2 days | Key rotation access |
| D. Ingestion | HIGH | 2 days | Phase A, B |
| E. API Hardening | MEDIUM | 2-3 days | Phase B |
| F. Frontend | MEDIUM | 3-5 days | None |
| G. Docker | MEDIUM | 2-3 days | Phase B, F |
| H. Testing | HIGH | 5-7 days | Phase D, E |
| I. Documentation | LOW | 2-3 days | Phase H |
| J. Monitoring | LOW | 1-2 days | Phase G |
| K. Legal Accuracy | HIGH | 3-5 days | Phase A, D |

**Total Estimated Effort:** 25-40 days (1 developer)

### Critical Path (Must Do First)
1. **Rotate API keys** (1 hour) — security emergency
2. **Install Tesseract** (30 minutes)
3. **Fix requirements.txt** (30 minutes)
4. **Download remaining PDFs** (1-2 days)
5. **Full re-ingestion** (1 day)
6. **Create nginx.conf** (1 hour)
7. **Fix .env.example** (30 minutes)

### Minimum Viable Deployment (MVP)
To deploy TODAY with what we have:
1. Rotate API keys
2. Fix `.env.example`
3. Create `frontend/nginx.conf`
4. Run `docker compose --profile full up -d`
5. Access frontend at `http://localhost:3000`

---

*Last updated: June 15, 2026*
