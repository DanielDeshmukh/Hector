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

---

## **Development Roadmap**

### [x] **Phase 1: Knowledge Base Acquisition & Curation**
*   **Tasks:** 
    *   Sourcing and verifying the "Big Three" legal commentaries (Ratanlal & Dhirajlal, Mulla, Sarkar).
    *   Digitizing Bare Acts for BNS, BNSS, and BSA (2025/2026 editions).
*   **Required Outcome:** A localized repository of 20+ high-fidelity PDFs ready for ingestion.

### [ ] **Phase 2: Layout-Aware Data Engineering**
*   **Tasks:** 
    *   Implementing `Marker` or `LlamaParse` to convert complex legal layouts into Markdown.
    *   Isolating footnotes, side-notes, and margin-citations from the main body text.
*   **Required Outcome:** A clean, structured Markdown dataset that preserves legal hierarchy.

### [ ] **Phase 3: Hierarchical Vector Indexing**
*   **Tasks:** 
    *   Configuring a Vector Database (Pinecone/ChromaDB) with a specialized metadata schema.
    *   Implementing "Parent-Document Retrieval" to ensure sub-clauses maintain their legal context.
*   **Required Outcome:** A searchable index where every "chunk" is tagged with its Act, Section, and Page Number.

### [ ] **Phase 4: Multi-Domain Intent Routing**
*   **Tasks:** 
    *   Developing the `src/core/intent_router.py` logic.
    *   Training the router to distinguish between Criminal (BNS) and Civil (CPC) queries.
*   **Required Outcome:** A robust classification layer that directs queries to the correct specialized index.

### [ ] **Phase 5: The IPC-BNS Bridge (Translation Layer)**
*   **Tasks:** 
    *   Creating a JSON-based mapping table between old IPC sections and new BNS sections.
    *   Coding a "Redirect Agent" that alerts users when they search for a repealed law.
*   **Required Outcome:** Seamless transition capability for practitioners moving to the new legal framework.

### [ ] **Phase 6: CLI Engine Development**
*   **Tasks:** 
    *   Building a `Typer`-based command-line interface for the "Hector Engine."
    *   Implementing the `--compare` and `--deep-cite` terminal flags.
*   **Required Outcome:** A fully functional terminal tool that performs legal RAG in real-time.

### [ ] **Phase 7: Logic Hardening & Hallucination Guardrails**
*   **Tasks:** 
    *   Writing the "Strict Citation" system prompt.
    *   Implementing a secondary LLM "Verifier" to cross-check the RAG output against the raw source.
*   **Required Outcome:** A system that achieves near-zero hallucination in testing benchmarks.

### [x] **Phase 8: API Layer & FastAPI Integration**
*   **Tasks:**
    *   Exposing the CLI logic via a high-performance FastAPI backend.
    *   Setting up WebSocket support for streaming legal analysis.
*   **Required Outcome:** A scalable backend capable of supporting a fullstack web application.

### [x] **Phase 9: Fullstack UI ("Lambo-Dark" Edition)**
*   **Tasks:**
    *   Designing the Next.js 14 dashboard with a high-contrast, minimalist dark theme.
    *   Building the "Dual-Pane" viewer (AI Summary vs. PDF Source).
    *   Adding search history and bookmarks functionality.
    *   Implementing IPC ↔ BNS comparison tool.
*   **Required Outcome:** A professional-grade, high-performance web interface for legal researchers.
*   **Frontend Location:** `frontend/` directory

### [ ] **Phase 10: Live Update & Maintenance Pipeline**
*   **Tasks:** 
    *   Developing a "Gazette Scraper" to monitor new amendments.
    *   Implementing a partial re-indexing script for Layer 2 (Amendment) data.
*   **Required Outcome:** An evergreen intelligence system that stays current with the dynamic Indian legal landscape.
