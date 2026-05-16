# H.E.C.T.O.R.
### **Hierarchical Evaluation of Civil-Criminal Textual's Orchestrator & Retrieval**

**HECTOR** is a high-precision, "Hard-RAG" legal intelligence system designed to navigate the complexities of Indian Law. Unlike standard LLMs that provide general summaries, HECTOR is engineered for **zero-hallucination** retrieval. It specializes in mapping the transition from the Indian Penal Code (IPC) to the **Bharatiya Nyaya Sanhita (BNS)**, providing authoritative citations directly from a curated library of 20+ legal commentaries and Bare Acts.

---

## **API Quick Start**

HECTOR now exposes a FastAPI backend for search, routing, comparison, ingestion, health checks, and streaming search events.

```bash
uvicorn api.app:app --reload
```

Authenticate with either:
- `X-API-Key: hector-dev-key`
- `POST /auth/token?api_key=hector-dev-key` for a JWT bearer token

Core endpoints:
- `POST /search`
- `POST /compare`
- `POST /route`
- `GET /status`
- `POST /ingest`
- `WS /ws/search`

---

## **Frontend Quick Start**

The Next.js 14 frontend provides a professional "Lambo-Dark" interface for legal research.

```bash
# Start API server (in one terminal)
uvicorn api.app:app --reload

# Start frontend (in another terminal)
cd frontend
npm run dev
```

Access the UI at: http://localhost:3000

Features:
- Dual-Pane Viewer (AI Summary | PDF Source)
- Search History & Bookmarks
- IPC ↔ BNS Comparison Tool
- High-contrast dark theme with gold accents

---

## **How HECTOR Works**

HECTOR operates on a **Chain-of-Verification (CoVe)** architecture. When a user inputs a legal query, the system follows a four-stage internal logic:

1.  **Intent Routing (The Gatekeeper):** The query is first analyzed by a "Taxonomy Agent" that classifies the legal domain (Criminal, Civil, or Procedural). This prevents "data bleeding," ensuring that a criminal query doesn't pull irrelevant civil precedents.
2.  **Hybrid Retrieval (The Researcher):** HECTOR utilizes a dual-search mechanism. It performs **Semantic Search** to understand the intent (e.g., "harming reputation") and **Keyword/Sparse Search** to pinpoint specific legal sections (e.g., "Section 356 BNS").
3.  **Hierarchical Contextualization:** Legal text is not flat. HECTOR’s retrieval engine ensures that if a sub-clause is retrieved, it automatically pulls the parent Section, Chapter, and Act titles to provide a complete legal context.
4.  **Strict Citation Grounding:** Before the final output is generated, a "Validator Agent" checks the response against the retrieved source. If the information is not explicitly present in the loaded books, HECTOR refuses to answer rather than guessing. Every response is appended with a verifiable **Source, Page, and Paragraph** reference.
