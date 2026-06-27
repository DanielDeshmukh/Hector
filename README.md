# H.E.C.T.O.R.

### **Hierarchical Evaluation of Civil-Criminal Textual's Orchestrator & Retrieval**

**HECTOR** is a high-precision "Hard-RAG" legal intelligence system for Indian Law. It specializes in mapping the transition from the Indian Penal Code (IPC) to the **Bharatiya Nyaya Sanhita (BNS)**, providing authoritative citations from a curated library of Bare Acts and commentaries with zero hallucination.

---

## Quick Start

### Docker (Recommended)

```bash
git clone <repo-url> && cd Hector
cp .env.example .env          # Add your API keys
docker compose --profile full up -d
# Frontend: http://localhost:3000
# API:      http://localhost:8000
# Docs:     http://localhost:8000/docs
```

### Local Development

```bash
# Backend
python -m venv venv && venv\Scripts\activate   # Windows
pip install -r requirements.txt
cp .env.example .env            # Add your API keys
uvicorn api.app:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install && npm run dev
```

### CLI

```bash
pip install -e .
hector status                   # Verify system
hector ingest                   # Index books
hector search "Section 302 IPC"
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER LAYER                               │
│  ┌──────────┐  ┌──────────────┐  ┌─────────┐  ┌────────────┐  │
│  │ React UI │  │  REST API    │  │   CLI   │  │  Voice I/O │  │
│  │ (Vite)   │  │  (FastAPI)   │  │ (Typer) │  │  (Web API) │  │
│  └────┬─────┘  └──────┬───────┘  └────┬────┘  └─────┬──────┘  │
│       └────────────────┴───────────────┴─────────────┘         │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│                      CORE ENGINE                                │
│                                                                 │
│  ┌─────────┐    ┌──────────────┐    ┌────────────┐             │
│  │ Router  │───▶│  Retriever   │───▶│  Verifier  │             │
│  │(Groq)   │    │(Hybrid RAG)  │    │(Chain-of-  │             │
│  │         │    │              │    │Verification)│             │
│  └─────────┘    └──────┬───────┘    └─────┬──────┘             │
│                        │                  │                     │
│  ┌─────────────────────▼──────────────────▼─────────────┐      │
│  │              RESPONSE GENERATOR                       │      │
│  │  (Citation grounding, IPC↔BNS comparison tables)     │      │
│  └──────────────────────────────────────────────────────┘      │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│                     DATA LAYER                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐    │
│  │   ChromaDB   │  │  BM25 Index  │  │  PDF Corpus        │    │
│  │  (Semantic)  │  │  (Keyword)   │  │  (24 Bare Acts +   │    │
│  │              │  │              │  │   13 Commentaries)  │    │
│  └──────────────┘  └──────────────┘  └────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### Query Pipeline

1. **Intent Routing** -- Taxonomy agent classifies domain (Criminal/Civil/Procedural) to prevent data bleeding
2. **Hybrid Retrieval** -- Semantic search (sentence-transformers) + BM25 keyword search, fused via Reciprocal Rank Fusion, reranked by cross-encoder
3. **Hierarchical Contextualization** -- Sub-clauses automatically pull parent Section, Chapter, and Act titles
4. **Citation Grounding** -- Validator checks response against source; unverified claims flagged, never guessed
5. **IPC to BNS Mapping** -- 495 cross-reference mappings with temporal validation (IPC repealed July 1, 2024)

---

## Environment Variables

Copy `.env.example` to `.env` and configure:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `HECTOR_API_KEY` | **Yes** | -- | API authentication key |
| `HECTOR_JWT_SECRET` | **Yes** | -- | JWT signing secret (min 32 chars) |
| `HECTOR_JWT_EXPIRY_SECONDS` | No | `3600` | Token lifetime |
| `GROQ_API_KEY` | **Yes** | -- | Groq API key for LLM routing |
| `GEMINI_API_KEY` | No | -- | Google Gemini API key |
| `NVIDIA_API_KEY` | No | -- | NVIDIA NIM API key |
| `NIM_API_KEY` | No | -- | NVIDIA NIM API key (alt) |
| `NIM_BASE_URL` | No | `https://integrate.api.nvidia.com/v1` | NIM endpoint |
| `HECTOR_ROUTER_MODEL` | No | `llama-3.3-70b-versatile` | Groq model for routing |
| `HECTOR_BOOKS_DIR` | No | `./data/Books` | PDF corpus directory |
| `HECTOR_DB_PATH` | No | `./hector_db` | ChromaDB storage path |
| `HECTOR_TESSERACT_CMD` | No | `tesseract` | Tesseract OCR binary path |
| `HECTOR_POPPLER_PATH` | No | -- | Poppler `bin/` directory (for `pdf2image`) |
| `HECTOR_CORS_ORIGINS` | No | `http://localhost:3000` | Comma-separated CORS origins |
| `HECTOR_LOG_LEVEL` | No | `INFO` | Logging level |
| `HECTOR_DEBUG` | No | `false` | Debug mode |

**Frontend** (`frontend/.env`):

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `VITE_API_URL` | No | `http://localhost:8000` | Backend API URL |
| `VITE_API_KEY` | No | -- | Pre-configured API key for UI |

---

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/search` | API Key / JWT | Hybrid legal search |
| `POST` | `/compare` | API Key / JWT | IPC to BNS section comparison |
| `POST` | `/route` | API Key / JWT | Intent classification |
| `POST` | `/ingest` | API Key / JWT | PDF ingestion trigger |
| `GET` | `/status` | API Key / JWT | System health + ChromaDB status |
| `GET` | `/healthz` | None | Liveness probe (for orchestrators) |
| `GET` | `/readyz` | None | Readiness probe (ChromaDB + disk) |
| `POST` | `/auth/token` | API Key | Get JWT bearer token |
| `WS` | `/ws/search` | Query param | Streaming search events |

Authenticate with:
- `X-API-Key: <your-key>` header, or
- `Authorization: Bearer <jwt-token>` header

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI, Python 3.11+ |
| Vector DB | ChromaDB |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) |
| Reranker | cross-encoder (`ms-marco-MiniLM-L-6-v2`) |
| LLM Router | Groq (`llama-3.3-70b-versatile`) |
| Frontend | Vite 5, React 18, Tailwind CSS 4 |
| OCR | Tesseract 5, Poppler, pdf2image |
| CLI | Typer |
| Containerization | Docker Compose |

---

## Project Structure

```
Hector/
├── api/                    # FastAPI application
│   ├── app.py              # Main app, middleware, routes
│   ├── security.py         # AuthManager, JWT, bcrypt
│   ├── rate_limit.py       # Token bucket rate limiting
│   ├── schemas.py          # Pydantic request/response models
│   └── services.py         # Business logic layer
├── core/                   # Core engine
│   ├── router.py           # Intent classification (Groq LLM)
│   ├── orchestrator.py     # Query pipeline coordinator
│   ├── hybrid_retriever.py # Semantic + BM25 + cross-encoder
│   ├── verifier.py         # Chain-of-Verification
│   ├── response_generator.py # Citation-grounded responses
│   ├── voice.py            # Voice I/O (Web Speech API)
│   ├── precedent.py        # Precedent analysis
│   ├── enterprise/         # Enterprise user management
│   └── mapping.json        # 495 IPC-BNS cross-references
├── data/Books/             # PDF corpus (24 bare acts + commentaries)
├── frontend/               # Vite + React frontend
│   ├── src/                # React components
│   ├── nginx.conf          # Production nginx config
│   └── Dockerfile          # Multi-stage build
├── tests/                  # Test suite
├── utils/                  # Ingestion pipeline
│   ├── enhanced_ingestor.py # PDF to ChromaDB pipeline
│   └── legal_structure_parser.py # Legal document parsing
├── docker-compose.yml      # Container orchestration
├── requirements.txt        # Python dependencies
└── main.py                 # CLI entry point
```

---

## Prerequisites

- **Python 3.11+**
- **Node.js 18+** (for frontend)
- **Tesseract OCR** (for scanned PDFs): `winget install UB-Mannheim.TesseractOCR`
- **Poppler** (for `pdf2image`): Download from [github.com/oschwartz10612/poppler-windows](https://github.com/oschwartz10612/poppler-windows/releases)
- **Docker** (optional, for containerized deploy)

---

## Troubleshooting

### Server refuses to start -- missing environment variables

```
RuntimeError: HECTOR_API_KEY and HECTOR_JWT_SECRET must be set
```

**Fix:** Copy `.env.example` to `.env` and add your API keys. The server will not start without them.

### Tesseract not found

```
TesseractNotFoundError: ...
```

**Fix:** Set `HECTOR_TESSERACT_CMD` in `.env` to the full path:
```
HECTOR_TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
```

### Poppler not found (PDF to image conversion fails)

**Fix:** Set `HECTOR_POPPLER_PATH` in `.env` to the Poppler `bin/` directory:
```
HECTOR_POPPLER_PATH=C:\path\to\poppler-xx\Library\bin
```

### CORS errors in browser

**Fix:** Ensure `HECTOR_CORS_ORIGINS` in `.env` includes your frontend URL:
```
HECTOR_CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### ChromaDB collection not found

**Fix:** Run ingestion first:
```bash
hector ingest           # via CLI
# or
python main.py ingest   # via main.py
```

### Rate limited (429 responses)

The API enforces rate limiting. Wait for the `Retry-After` period in the response header.

### Docker build fails

**Fix:** Ensure `.env` exists in the project root. Docker Compose reads it automatically:
```bash
cp .env.example .env
# Edit .env with your keys
docker compose --profile full up -d
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, branch workflow, and PR guidelines.

---

## Legal Disclaimer

HECTOR is provided for **informational and educational purposes only**. It is not a substitute for professional legal advice. The IPC-to-BNS mappings, section references, and generated responses are derived from publicly available legal texts and may contain inaccuracies.

**Always consult a qualified legal professional before making legal decisions.**

The authors and contributors of HECTOR assume no liability for any decisions made or actions taken based on the information provided by this software.

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
