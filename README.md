⭐ If HECTOR helped you navigate IPC → BNS 2023 mapping without hallucinations — a star helps other legal-AI builders find it. Takes 2 seconds.

# H.E.C.T.O.R.
### **Hierarchical Evaluation of Civil-Criminal Textual's Orchestrator & Retrieval**

**HECTOR** is a high-precision, "Hard-RAG" legal intelligence system designed to navigate the complexities of Indian Law. Unlike standard LLMs that provide general summaries, HECTOR is engineered for **zero-hallucination** retrieval. It specializes in mapping the transition from the Indian Penal Code (IPC) to the **Bharatiya Nyaya Sanhita (BNS)**, providing authoritative citations directly from a curated library of legal Bare Acts and commentaries.

---

## **API Quick Start**

HECTOR exposes a FastAPI backend for search, routing, comparison, ingestion, health checks, and streaming search events.

```bash
uvicorn api.app:app --reload
```

Authenticate with either:
- `X-API-Key: hector-dev-key`
- `POST /auth/token?api_key=hector-dev-key` for a JWT bearer token

Core endpoints:
- `POST /search` — Hybrid search across legal corpus
- `POST /compare` — IPC ↔ BNS section comparison
- `POST /route` — Intent classification
- `GET /status` — System health check
- `POST /ingest` — PDF ingestion
- `WS /ws/search` — Streaming search events

---

## **Frontend Quick Start**

The Vite + React 18 frontend provides a professional dark-theme interface for legal research.

```bash
# Start API server (in one terminal)
uvicorn api.app:app --reload

# Start frontend (in another terminal)
cd frontend
npm run dev
```

Access the UI at: http://localhost:3000

### Features
- **Dual-Pane Viewer** — AI-generated summary alongside source document detail
- **Search History** — localStorage-backed query history with re-submit
- **Bookmarks** — Save and manage favorite sources from search results
- **IPC ↔ BNS Comparison Tool** — Dedicated comparison UI with act selector
- **Multi-Language Support** — Hindi/English UI toggle
- **Voice Query** — Browser-based speech input (Web Speech API)
- **High-contrast dark theme** — Professional dark UI with gold accents and Google Fonts
- **Structured Citations** — Source, page, and paragraph references on every response

---

## **CLI Commands**

HECTOR provides a command-line interface for easy access to all features.

### Quick Start

```powershell
# One-time setup from the project root
venv\Scripts\python.exe -m pip install -e .

# Then use the CLI directly
hector init
hector status
hector ingest
hector --help
```

### Commands

| Command | Description | Options |
|---------|-------------|---------|
| `hector init` | Start HECTOR (API + Frontend) | `--port, -p` (default: 8000), `--frontend-port, -fp` (default: 3000), `--no-frontend`, `--auto-port`, `--kill-existing` |
| `hector ingest` | Ingest books from data/Books | `--force, -f` (re-ingest all), `--verbose, -v` (detailed) |
| `hector status` | Display system status | - |
| `hector --help` | Show help message | - |

**Examples:**
```powershell
# Install the CLI into the project virtualenv
venv\Scripts\python.exe -m pip install -e .

# Then use from the terminal as a normal command
hector init                    # Start both API and frontend
hector init --port 9000        # Custom API port
hector init --no-frontend      # API only
hector ingest                  # Ingest new books
hector status                  # Check system status
hector --help                  # Show help
```

---

## **How HECTOR Works**

HECTOR operates on a **Chain-of-Verification (CoVe)** architecture. When a user inputs a legal query, the system follows a four-stage internal logic:

1.  **Intent Routing (The Gatekeeper):** The query is first analyzed by a "Taxonomy Agent" that classifies the legal domain (Criminal, Civil, or Procedural). This prevents "data bleeding," ensuring that a criminal query doesn't pull irrelevant civil precedents.
2.  **Hybrid Retrieval (The Researcher):** HECTOR utilizes a dual-search mechanism. It performs **Semantic Search** to understand the intent (e.g., "harming reputation") and **Keyword/Sparse Search** (BM25) to pinpoint specific legal sections (e.g., "Section 356 BNS"). Results are merged via **Reciprocal Rank Fusion** and reranked with a **cross-encoder**.
3.  **Hierarchical Contextualization:** Legal text is not flat. HECTOR's retrieval engine ensures that if a sub-clause is retrieved, it automatically pulls the parent Section, Chapter, and Act titles to provide a complete legal context.
4.  **Strict Citation Grounding:** Before the final output is generated, a "Validator Agent" checks the response against the retrieved source. If the information is not explicitly present in the loaded books, HECTOR flags unverified claims rather than guessing. Every response is appended with a verifiable **Source, Page, and Paragraph** reference.

---

## **Environment Configuration**

Copy `.env.example` to `.env` and configure:

```bash
# Authentication
HECTOR_API_KEY=your-api-key
HECTOR_JWT_SECRET=your-jwt-secret

# LLM Routing (Groq)
GROQ_API_KEY=your-groq-key

# Paths (optional — auto-detected)
HECTOR_BOOKS_DIR=./data/Books
HECTOR_DB_PATH=./hector_db
HECTOR_POPPLER_PATH=/path/to/poppler/bin
HECTOR_TESSERACT_CMD=tesseract
```

Frontend env (copy `.env.example` in `frontend/`):
```bash
VITE_API_URL=http://localhost:8000
VITE_API_KEY=your-api-key
```

---

## **Tech Stack**

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI, Python 3.11+ |
| Vector DB | ChromaDB |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Reranker | cross-encoder (ms-marco-MiniLM-L-6-v2) |
| LLM Router | Groq (llama-3.3-70b-versatile) |
| Frontend | Vite 5, React 18, Tailwind CSS 4 |
| OCR | Tesseract, pdf2image |
| CLI | argparse (main.py) |
