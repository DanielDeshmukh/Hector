# HECTOR — Pending Work: Current State to 100% Deployment Ready

**Date:** June 15, 2026
**Current Status:** ~96% Complete (Functional prototype, not production-ready)
**Goal:** 100% Production Deployment Ready

---

## Table of Contents

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

### C1. Rotate All API Keys
- [ ] **IMMEDIATELY** rotate `GROQ_API_KEY` (committed to git)
- [ ] **IMMEDIATELY** rotate `GEMINI_API_KEY` (committed to git)
- [ ] **IMMEDIATELY** rotate `NVIDIA_API_KEY` / `NIM_API_KEY` (committed to git)
- [ ] Use GitHub secret scanning / pre-commit hooks to prevent re-commitment

### C2. JWT Security
- [ ] Generate cryptographically secure `HECTOR_JWT_SECRET` (32+ bytes random)
- [ ] Remove default `change-me-in-production` value
- [ ] Add JWT token refresh endpoint
- [ ] Add token revocation/blacklisting
- [ ] Implement role-based access control (RBAC) enforcement

### C3. API Security
- [ ] Add request size limits (prevent DoS via large payloads)
- [ ] Add input sanitization for all query parameters
- [ ] Implement CORS allowlist (not `*`)
- [ ] Add HTTPS enforcement (redirect HTTP → HTTPS)
- [ ] Add security headers (CSP, X-Frame-Options, HSTS)
- [ ] Add API key rotation mechanism
- [ ] Implement brute-force protection on auth endpoints

### C4. Data Security
- [ ] Encrypt ChromaDB at rest (if deploying to cloud)
- [ ] Add audit logging for all data access
- [ ] Implement data retention policies
- [ ] Add PII detection/redaction in logs

---

## 5. Phase D — Ingestion Pipeline Fixes

**Goal:** Robust, idempotent PDF ingestion

### D1. Fix Metadata Errors
- [x] Fix `Cannot convert Python object to MetadataValue` (None values) — DONE
- [ ] Fix `set()` types in metadata (ChromaDB rejects non-scalar values)
- [ ] Add metadata validation before `collection.add()` call
- [ ] Log metadata warnings instead of failing silently

### D2. Fix PDF Extraction
- [ ] Add PDF corruption detection (check file header, page count)
- [ ] Add timeout per page extraction (prevent hanging on corrupted PDFs)
- [ ] Add progress bar for large PDFs (>100 pages)
- [ ] Handle encrypted PDFs gracefully (skip with warning)
- [ ] Fix `fixed_The_Code_of_Criminal.pdf` — 0 chunks extracted despite 2.4MB

### D3. Improve Ingestion Quality
- [ ] Add chunk quality scoring (reject chunks < 50 chars)
- [ ] Add legal section boundary detection (don't split mid-section)
- [ ] Add cross-reference linking between IPC ↔ BNS sections
- [ ] Add ingestion deduplication by content hash (not just page_hash)
- [ ] Add ingestion resume capability (skip already-processed books)

### D4. Ingestion Monitoring
- [ ] Add ingestion progress tracking (percentage, ETA)
- [ ] Add ingestion error reporting (which pages failed, why)
- [ ] Add ingestion quality metrics (avg chunk size, metadata coverage)
- [ ] Add ingestion logging to file (not just console)

---

## 6. Phase E — API & Backend Hardening

**Goal:** Production-grade API with proper error handling

### E1. Error Handling
- [ ] Add global exception handler for unhandled errors
- [ ] Add structured error responses (not raw Python tracebacks)
- [ ] Add error codes (not just HTTP status codes)
- [ ] Add request ID tracking for debugging
- [ ] Add retry logic for transient failures (Groq API, ChromaDB)

### E2. Rate Limiting
- [ ] Verify rate limiter works with multiple clients
- [ ] Add per-user rate limiting (not just global)
- [ ] Add rate limit headers in responses (`X-RateLimit-Remaining`)
- [ ] Add rate limit bypass for internal tools

### E3. Caching
- [ ] Verify TTL cache works correctly
- [ ] Add cache invalidation on ingestion
- [ ] Add cache warming on startup
- [ ] Add cache metrics (hit rate, size)

### E4. API Documentation
- [ ] Verify OpenAPI docs generate correctly (`/docs`)
- [ ] Add example requests for all endpoints
- [ ] Add error response examples
- [ ] Add authentication flow documentation

### E5. Health Checks
- [ ] Add ChromaDB connection check to `/status`
- [ ] Add Groq API connectivity check
- [ ] Add disk space check
- [ ] Add memory usage check
- [ ] Add embedding model availability check

---

## 7. Phase F — Frontend Fixes

**Goal:** Polished, accessible, production-ready UI

### F1. Missing nginx.conf
- [ ] Create `frontend/nginx.conf` (referenced in `frontend/Dockerfile`)
- [ ] Configure SPA routing (fallback to `index.html`)
- [ ] Add gzip compression
- [ ] Add cache headers for static assets
- [ ] Add security headers

### F2. UI/UX Improvements
- [ ] Add loading skeletons (not just spinners)
- [ ] Add error boundaries for component crashes
- [ ] Add empty state illustrations
- [ ] Add search history pagination
- [ ] Add keyboard shortcuts (Ctrl+K for search)
- [ ] Add responsive design audit (mobile, tablet, desktop)

### F3. Accessibility
- [ ] Add ARIA labels to all interactive elements
- [ ] Add keyboard navigation support
- [ ] Add color contrast audit (WCAG 2.1 AA)
- [ ] Add screen reader testing
- [ ] Add focus management for modals

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

### G1. Docker Fixes
- [ ] Create `frontend/nginx.conf`
- [ ] Fix frontend Dockerfile (verify Node.js version, build process)
- [ ] Add `.dockerignore` entries for `hector_db/`, `data/Books/`
- [ ] Add multi-platform support (linux/amd64, linux/arm64)
- [ ] Add Docker image scanning (Trivy/Snyk)

### G2. Docker Compose Improvements
- [ ] Add environment-specific overrides (`docker-compose.prod.yml`)
- [ ] Add resource limits (CPU, memory) per service
- [ ] Add log rotation configuration
- [ ] Add volume backup strategy
- [ ] Add network isolation between services

### G3. Production Deployment
- [ ] Create `docker-compose.prod.yml` with:
  - Nginx reverse proxy with SSL termination
  - PostgreSQL for user management (replace SQLite)
  - Redis for caching (replace in-memory)
  - Prometheus + Grafana for monitoring
- [ ] Add deployment scripts (deploy.sh, rollback.sh)
- [ ] Add environment-specific configs (dev/staging/prod)
- [ ] Add secrets management (Docker secrets, AWS SSM, etc.)

### G4. Cloud Deployment Options
- [ ] Create AWS ECS/Fargate task definitions
- [ ] Create Kubernetes manifests (Deployment, Service, Ingress)
- [ ] Create Terraform/IaC for cloud resources
- [ ] Add CI/CD pipeline (GitHub Actions)

---

## 9. Phase H — Testing

**Goal:** Confidence in every deployment

### H1. Unit Tests (Existing but Incomplete)
- [ ] Add `conftest.py` with shared fixtures (test client, mock DB)
- [ ] Add tests for `enhanced_ingestor.py` (currently no tests)
- [ ] Add tests for `legal_structure_parser.py` (currently no tests)
- [ ] Add tests for `hybrid_retriever.py` (edge cases)
- [ ] Add tests for `orchestrator.py` (mock all dependencies)
- [ ] Add tests for `response_generator.py`
- [ ] Add tests for `voice.py`
- [ ] Add tests for `precedent.py`

### H2. Integration Tests
- [ ] Test API → Orchestrator → Retriever → Verifier pipeline
- [ ] Test ingestion → search flow (ingest PDF, verify searchable)
- [ ] Test authentication flow (register → login → access protected endpoint)
- [ ] Test rate limiting under load
- [ ] Test cache behavior (miss → hit → expiry)

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

### I1. README.md Overhaul
- [ ] Add project architecture diagram (Mermaid or ASCII)
- [ ] Add quick start (3 commands: clone → install → run)
- [ ] Add prerequisites (Python 3.11, Node.js 18+, Tesseract)
- [ ] Add environment variable reference table
- [ ] Add troubleshooting section
- [ ] Add contribution guidelines
- [ ] Add license (MIT/Apache 2.0)

### I2. API Documentation
- [ ] Auto-generate OpenAPI spec from FastAPI
- [ ] Add Postman collection for all endpoints
- [ ] Add authentication flow diagram
- [ ] Add rate limiting documentation
- [ ] Add error code reference

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

### J1. Logging
- [ ] Replace `print()` with `logging` module throughout
- [ ] Add structured logging (JSON format)
- [ ] Add log levels (DEBUG/INFO/WARNING/ERROR)
- [ ] Add request ID propagation through all layers
- [ ] Add sensitive data redaction in logs

### J2. Metrics
- [ ] Add Prometheus metrics endpoint (`/metrics`)
- [ ] Track request count, latency, error rate
- [ ] Track search query performance
- [ ] Track ingestion progress
- [ ] Track ChromaDB collection size

### J3. Alerting
- [ ] Add health check alerts (service down)
- [ ] Add error rate alerts (spike in 5xx errors)
- [ ] Add latency alerts (p95 > 5s)
- [ ] Add disk space alerts (DB > 80%)
- [ ] Add API key expiry alerts

---

## 12. Phase K — Legal Accuracy & Verification

**Goal:** Zero hallucination, verified legal information

### K1. Hallucination Prevention
- [ ] Verify Chain-of-Verification works end-to-end
- [ ] Add citation verification (check cited sections exist in corpus)
- [ ] Add confidence scoring (low confidence → warn user)
- [ ] Add "I don't know" responses when corpus lacks information

### K2. Cross-Reference Accuracy
- [ ] Build IPC ↔ BNS mapping table (356 sections)
- [ ] Build CrPC ↔ BNSS mapping table
- [ ] Build Evidence Act ↔ BSA mapping table
- [ ] Add temporal validation (IPC effective until 2024-07-01)

### K3. Corpus Quality
- [ ] Audit existing 18 sources for completeness
- [ ] Remove duplicate/overlapping content
- [ ] Add legal update pipeline (gazette notification → re-ingestion)
- [ ] Add corpus versioning (track when each PDF was last updated)

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
