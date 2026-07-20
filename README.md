<p align="center">
  <img src="banner.png" alt="HECTOR" width="100%">
</p>

<p align="center">
  <a href="https://github.com/DanielDeshmukh/Hector/actions"><img src="https://img.shields.io/github/actions/workflow/status/DanielDeshmukh/Hector/ci.yml?branch=main&style=for-the-badge&label=CI&color=%23111315&labelColor=%231a1a1a&messageColor=%23c9a962&border_radius=10" alt="CI"></a>
  <a href="https://github.com/DanielDeshmukh/Hector"><img src="https://img.shields.io/github/stars/DanielDeshmukh/Hector?style=for-the-badge&color=%23111315&labelColor=%231a1a1a&label=Stars&messageColor=%23c9a962&border_radius=10" alt="Stars"></a>
  <a href="#"><img src="https://img.shields.io/badge/tests-1124%20passed-22c55e?style=for-the-badge&color=%23111315&labelColor=%231a1a1a&messageColor=%23c9a962&border_radius=10" alt="Tests"></a>
  <a href="#"><img src="https://img.shields.io/badge/live-vercel.app-000?style=for-the-badge&color=%23111315&labelColor=%231a1a1a&logo=vercel&logoColor=white&messageColor=%23c9a962&border_radius=10" alt="Live"></a>
</p>

<p align="center">
  <a href="https://nextjs.org"><img src="https://img.shields.io/badge/Next.js-16-000?style=for-the-badge&logo=next.js&logoColor=white&color=%23111315&labelColor=%231a1a1a&messageColor=%23c9a962&border_radius=10" alt="Next.js"></a>
  <a href="https://www.typescriptlang.org"><img src="https://img.shields.io/badge/TypeScript-5-3178c6?style=for-the-badge&logo=typescript&logoColor=white&color=%23111315&labelColor=%231a1a1a&messageColor=%23c9a962&border_radius=10" alt="TypeScript"></a>
  <a href="https://build.nvidia.com/nim"><img src="https://img.shields.io/badge/NVIDIA%20NIM-Llama%203.1-76b900?style=for-the-badge&logo=nvidia&logoColor=white&color=%23111315&labelColor=%231a1a1a&messageColor=%23c9a962&border_radius=10" alt="NVIDIA NIM"></a>
  <a href="https://www.pinecone.io"><img src="https://img.shields.io/badge/Pinecone-Vector%20DB-000?style=for-the-badge&color=%23111315&labelColor=%231a1a1a&messageColor=%23c9a962&border_radius=10" alt="Pinecone"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.13-3776ab?style=for-the-badge&logo=python&logoColor=white&color=%23111315&labelColor=%231a1a1a&messageColor=%23c9a962&border_radius=10" alt="Python"></a>
  <a href="https://fastapi.tiangolo.com"><img src="https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white&color=%23111315&labelColor=%231a1a1a&messageColor=%23c9a962&border_radius=10" alt="FastAPI"></a>
</p>

---

**HECTOR** — *Hierarchical Evaluation of Civil-Criminal Textual's Orchestrator & Retrieval*

A zero-hallucination legal research engine purpose-built for the Indian legal system. HECTOR ingests bare acts, commentaries, and constitutional texts, then answers complex legal queries with grounded, cited responses — never fabricating a single provision.

India's legal landscape is brutal for AI. Over 700 central acts, three parallel criminal codes (IPC, BNS, BNSS), hundreds of state amendments, and a citation culture where a wrong section number can lose a case. Existing legal AI tools are either trained on Common Law jurisdictions or hallucinate sections that don't exist. We built HECTOR to solve this from the ground up.

### What It Does

HECTOR takes a natural language legal query — *"What is the punishment for dowry death under BNS?"* — and runs it through an 8-stage pipeline that extracts legal entities, classifies intent, expands the query with domain synonyms, performs hybrid semantic + BM25 retrieval across a curated corpus of 45 Indian legal texts, re-ranks results with entity-aware scoring, generates a contextual response, and then verifies every citation against the source documents before returning it to the user.

The system maintains a 496-entry IPC-to-BNS cross-reference map so when someone asks about Section 304B IPC, HECTOR automatically retrieves the equivalent BNS provision alongside it — bridging the transition from the 1860 Penal Code to the 2023 Bharatiya Nyaya Sanhita.

### How We Built It

The backend is a **Python/FastAPI** service running a modular pipeline architecture. The orchestrator (`orchestrator.py`) is the spine — it chains together a query parser, embedding router, query intelligence layer, synonym expander, hybrid retriever, entity reranker, response generator, and chain-of-verification verifier. Every stage is timed, logged, and independently testable.

**Retrieval** uses a custom `HectorHybridRetriever` that fuses three ranking signals: semantic similarity (via NVIDIA NIM embeddings), BM25 keyword matching (custom implementation, zero dependencies), and a domain-specific legal boost system that scores results on act-match, section-match, citation-match, concept-match, current-law preference, jurisdiction authority, and source type. The fusion uses Reciprocal Rank Fusion with tunable `k=60`, and the final scoring blends RRF scores with boost signals.

**Query Intelligence** sits before the retrieval pipeline. It uses NVIDIA Nemotron Nano 8B to analyze query structure — detecting cross-act mapping intent, extracting metadata filters, selecting search strategies, and producing structured JSON that the downstream pipeline consumes. Before QI, the system scored 82.8% accuracy on our evaluation benchmark. After, it hit 94.2%.

**The frontend** is a Next.js 16 App Router application with Tailwind CSS v4, using EB Garamond for the serif display type, Inter for body text, and JetBrains Mono for code/data. The UI is dark-themed with a gold accent palette — the entire color system is defined in `globals.css` using CSS custom properties.

**Deployment** runs as a single Vercel application. The Next.js frontend serves the UI, and Python serverless functions in the `api/` directory handle the FastAPI backend. Pinecone Cloud hosts the vector database (13,479 chunks across 45 legal texts), and all LLM inference routes through NVIDIA NIM and Groq APIs.

### Problems We Solved

**The IPC-to-BNS transition.** India is simultaneously operating two criminal codes. A user asking about "Section 302" might mean IPC (murder) or BNS (also murder, different number). We built a 496-entry cross-reference mapping and a query intelligence layer that automatically detects intent and retrieves both versions, ranking the current law higher.

**Zero-hallucination requirement.** Legal AI that fabricates a section number is worse than no AI at all. We implemented a Chain-of-Verification system that cross-checks every generated claim against the source documents. The verifier uses Groq's Llama 3.3 70B with a strict system prompt: if the information isn't in the retrieved context, it says so explicitly rather than guessing. Citation format is enforced as `[Source: Book Name, Page: X, Section: Y]`.

**94.2% accuracy from 82.8%.** The jump came from the Query Intelligence layer — a dedicated Nemotron Nano 8B model that analyzes query structure before retrieval. It extracts section numbers, act names, and legal concepts, then passes them as metadata filters to the retriever. This eliminates the "Section 302 query returns Section 304" false match problem that plagued the earlier pipeline.

**Hybrid retrieval without heavy dependencies.** The BM25 implementation is 45 lines of pure Python — no `rank-bm25`, no `elasticsearch`, no external services. It runs in-memory on cold start, tokenizing the corpus with a simple `[a-z0-9]+` pattern. Combined with Pinecone's vector similarity search and our legal-domain boost system, it consistently outperforms either approach alone.

**Cold start on Vercel.** Moving from a persistent server to Vercel serverless meant losing disk access. Pinecone Cloud solved the vector storage. The BM25 index rebuilds from Pinecone on each cold start (~5s for 13K documents). Sentence-transformers and torch were removed from production dependencies, cutting the deployment from ~2GB to under 50MB.

### The Corpus

45 Indian legal texts ingested into **13,479 chunks** with rich metadata:

| Act | Type |
|---|---|
| Indian Penal Code, 1860 | Criminal |
| Bharatiya Nyaya Sanhita, 2023 | Criminal |
| Bharatiya Nagarik Suraksha Sanhita, 2023 | Criminal Procedure |
| Code of Criminal Procedure, 1973 | Criminal Procedure |
| Bharatiya Sakshya Adhiniyam, 2023 | Evidence |
| Indian Evidence Act, 1872 | Evidence |
| Constitution of India | Constitutional |
| Code of Civil Procedure, 1908 | Civil |
| Indian Contract Act, 1872 | Contract |
| Consumer Protection Act, 2019 | Consumer |
| Motor Vehicles Act, 1988 | Motor |
| Hindu Marriage Act, 1955 | Family |
| Hindu Succession Act, 1956 | Family |
| Transfer of Property Act, 1882 | Property |
| Information Technology Act, 2000 | Cyber |
| Negotiable Instruments Act, 1881 | Commercial |
| Industrial Disputes Act, 1947 | Labour |
| 30+ more acts and commentaries | Various |

### NVIDIA NIM Models

| Model | Pipeline Role |
|---|---|
| `meta/llama-3.1-8b-instruct` | Router, response generation, chain-of-verification |
| `nvidia/llama-3.1-nemotron-nano-8b-v1` | Query intelligence, structured analysis |
| `nvidia/nv-embedqa-e5-v5` | 1024-dim embeddings for semantic search |
| `groq/llama-3.3-70b-versatile` | Hallucination detection (Groq fallback) |

### Architecture

```
Query
  |
  v
[Query Intelligence] ── Nemotron Nano 8B
  |  (entity extraction, cross-act detection, metadata filters)
  v
[Intent Router] ── Rules + Embedding fallback
  |
  v
[Query Expansion] ── Synonym injection
  |
  v
[Hybrid Retrieval] ── Pinecone (semantic) + BM25 (keyword) + Legal Boosts
  |  (RRF fusion, entity reranking)
  v
[Response Generation] ── Llama 3.1 8B
  |
  v
[Chain-of-Verification] ── Groq Llama 3.3 70B
  |  (citation grounding, hallucination check)
  v
Cited Response
```

### Numbers

| Metric | Value |
|---|---|
| Total corpus chunks | 13,479 |
| IPC-to-BNS mappings | 496 |
| Evaluation accuracy | 94.2% |
| Test functions | 1,124 |
| Commits | 253 |
| Core pipeline modules | 20 |
| Supported query routes | 4 |

---

<p align="center">
  Built by <b>Daniel Deshmukh</b>
</p>
