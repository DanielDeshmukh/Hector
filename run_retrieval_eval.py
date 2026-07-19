"""Lightweight retrieval-only accuracy eval — no orchestrator, no NIM API."""

import os
import sys
import json
import time

os.environ["HF_HUB_OFFLINE"] = "1"
sys.path.insert(0, r"D:\Vs Code\VS code\Hector")

from data.hybrid_retriever import HectorHybridRetriever as HybridRetriever
from core.query_expander import QueryExpander

TEST_QUERIES = [
    {
        "id": 1,
        "query": "What is the punishment for murder under Section 302 IPC",
        "category": "exact",
        "kw": ["302", "murder", "punishment", "death", "life imprisonment"],
    },
    {
        "id": 2,
        "query": "Section 376 IPC punishment for rape",
        "category": "exact",
        "kw": ["376", "rape", "punishment", "imprisonment"],
    },
    {
        "id": 3,
        "query": "Bharatiya Nagarik Suraksha Sanhita bail provisions",
        "category": "exact",
        "kw": ["bail", "BNSS", "Bharatiya Nagarik", "anticipatory"],
    },
    {
        "id": 4,
        "query": "Indian Evidence Act Section 65B admissibility of electronic evidence",
        "category": "exact",
        "kw": ["65B", "electronic evidence", "admissibility", "certificate"],
    },
    {
        "id": 5,
        "query": "Transfer of Property Act Section 54 sale of immovable property",
        "category": "exact",
        "kw": ["54", "sale", "immovable property", "registration"],
    },
    {
        "id": 6,
        "query": "Section 144 CrPC now Section 163 BNSS power to issue orders",
        "category": "exact",
        "kw": ["144", "163", "BNSS", "CrPC", "order"],
    },
    {
        "id": 7,
        "query": "Section 498A IPC punishment for dowry harassment",
        "category": "exact",
        "kw": ["498A", "dowry", "cruelty", "punishment", "husband"],
    },
    {
        "id": 8,
        "query": "NDPS Act Section 20 punishment for drug trafficking",
        "category": "exact",
        "kw": ["NDPS", "Section 20", "drug", "punishment", "trafficking"],
    },
    {
        "id": 9,
        "query": "Article 21 Constitution of India right to life and personal liberty",
        "category": "exact",
        "kw": ["Article 21", "right to life", "personal liberty", "Constitution"],
    },
    {
        "id": 10,
        "query": "Consumer Protection Act Section 38 unfair trade practice",
        "category": "exact",
        "kw": ["Section 38", "consumer", "unfair trade", "practice"],
    },
    {
        "id": 11,
        "query": "What happens if someone is charged with a crime they didn't commit?",
        "category": "similar",
        "kw": ["false", "wrongful", "acquittal", "innocent"],
    },
    {
        "id": 12,
        "query": "My in-laws are demanding money from me. What legal options do I have?",
        "category": "similar",
        "kw": ["dowry", "cruelty", "498A", "maintenance"],
    },
    {
        "id": 13,
        "query": "Someone forged my signature on a document. Is that a crime?",
        "category": "similar",
        "kw": ["forgery", "fraud", "signature", "crime"],
    },
    {
        "id": 14,
        "query": "Is a confession made to police admissible in court?",
        "category": "similar",
        "kw": ["confession", "police", "admissible", "Section 25", "evidence"],
    },
    {
        "id": 15,
        "query": "What is the time limit to file a civil suit in India?",
        "category": "similar",
        "kw": ["limitation", "time limit", "3 years", "Limitation Act"],
    },
    {
        "id": 16,
        "query": "My employer is not paying wages. What legal remedy do I have?",
        "category": "similar",
        "kw": ["wages", "employer", "Industrial Disputes", "labour court"],
    },
    {
        "id": 17,
        "query": "Can a minor enter into a valid contract?",
        "category": "similar",
        "kw": ["minor", "contract", "void", "Section 10", "Indian Contract Act"],
    },
    {
        "id": 18,
        "query": "What is the punishment for driving under influence of alcohol in India?",
        "category": "similar",
        "kw": ["drunk driving", "Motor Vehicles Act", "Section 185", "penalty"],
    },
    {
        "id": 19,
        "query": "How does inheritance work if someone dies without a will in Hindu family?",
        "category": "similar",
        "kw": ["intestate", "Hindu Succession Act", "heir", "coparcenary"],
    },
    {
        "id": 20,
        "query": "What rights does an accused person have during police interrogation?",
        "category": "similar",
        "kw": ["accused", "rights", "police", "legal counsel", "BNSS"],
    },
    {
        "id": 21,
        "query": "What is the capital of France?",
        "category": "irrelevant",
        "kw": [],
    },
    {
        "id": 22,
        "query": "Tell me a joke about lawyers",
        "category": "irrelevant",
        "kw": [],
    },
    {
        "id": 23,
        "query": "How do I make pasta carbonara?",
        "category": "irrelevant",
        "kw": [],
    },
    {
        "id": 24,
        "query": "What is the best programming language?",
        "category": "irrelevant",
        "kw": [],
    },
    {
        "id": 25,
        "query": "Who won the last FIFA World Cup?",
        "category": "irrelevant",
        "kw": [],
    },
    {"id": 26, "query": "How do I train my dog?", "category": "irrelevant", "kw": []},
    {
        "id": 27,
        "query": "What is machine learning?",
        "category": "irrelevant",
        "kw": [],
    },
    {
        "id": 28,
        "query": "Recommend a good restaurant in Mumbai",
        "category": "irrelevant",
        "kw": [],
    },
    {
        "id": 29,
        "query": "What is the weather today?",
        "category": "irrelevant",
        "kw": [],
    },
    {
        "id": 30,
        "query": "How do I invest in cryptocurrency?",
        "category": "irrelevant",
        "kw": [],
    },
]


def score_retrieval(query, chunks, expected_kw, category):
    if category == "irrelevant":
        legal_terms = ["section", "act", "court", "punishment", "IPC", "BNS"]
        legal_hits = sum(1 for c in chunks if any(t in c.lower() for t in legal_terms))
        if legal_hits == 0:
            return 100
        elif legal_hits <= 2:
            return 70
        else:
            return 30

    all_text = " ".join(chunks).lower()
    matched = 0
    for kw in expected_kw:
        if kw.lower() in all_text:
            matched += 1
        elif all(w in all_text for w in kw.lower().split()):
            matched += 0.5
    return min(100, int((matched / max(len(expected_kw), 1)) * 100))


def run():
    print("=" * 70)
    print("HECTOR RETRIEVAL-ONLY ACCURACY EVAL (30 queries)")
    print("=" * 70)

    retriever = HybridRetriever()
    expander = QueryExpander()
    results = []
    start = time.time()

    for q in TEST_QUERIES:
        t0 = time.time()
        expanded_q = expander.expand(q["query"])
        search_results = retriever.search(expanded_q, top_k=10)
        elapsed = time.time() - t0

        chunks = [r.get("document", r.get("text", "")) for r in search_results]
        score = score_retrieval(q["query"], chunks, q["kw"], q["category"])

        result = {
            "id": q["id"],
            "query": q["query"][:80],
            "category": q["category"],
            "score": score,
            "retrieve_ms": round(elapsed * 1000, 1),
            "n_chunks": len(chunks),
        }
        results.append(result)

        status = "PASS" if score >= 50 else "FAIL"
        print(
            f"Q{q['id']:2d} [{q['category']:9s}] {score:3d}/100 [{status}] {elapsed * 1000:6.0f}ms | {q['query'][:55]}"
        )

    elapsed_total = time.time() - start
    exact_scores = [r["score"] for r in results if r["category"] == "exact"]
    similar_scores = [r["score"] for r in results if r["category"] == "similar"]
    irrelevant_scores = [r["score"] for r in results if r["category"] == "irrelevant"]
    all_scores = [r["score"] for r in results]

    print(f"\n{'=' * 70}")
    print("RESULTS")
    print(f"{'=' * 70}")
    print(
        f"Exact (10):     {sum(exact_scores) / len(exact_scores):.1f}% avg | {exact_scores}"
    )
    print(
        f"Similar (10):   {sum(similar_scores) / len(similar_scores):.1f}% avg | {similar_scores}"
    )
    print(
        f"Irrelevant (10): {sum(irrelevant_scores) / len(irrelevant_scores):.1f}% avg | {irrelevant_scores}"
    )
    print(f"OVERALL:        {sum(all_scores) / len(all_scores):.1f}% avg")
    print(
        f"Time:           {elapsed_total:.0f}s total ({elapsed_total / 30:.1f}s/query)"
    )

    output = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "overall_pct": round(sum(all_scores) / len(all_scores), 1),
        "exact_pct": round(sum(exact_scores) / len(exact_scores), 1),
        "similar_pct": round(sum(similar_scores) / len(similar_scores), 1),
        "irrelevant_pct": round(sum(irrelevant_scores) / len(irrelevant_scores), 1),
        "results": results,
    }
    with open("retrieval_test_results_v2.json", "w") as f:
        json.dump(output, f, indent=2)
    print("\nSaved to retrieval_test_results_v2.json")


if __name__ == "__main__":
    run()
