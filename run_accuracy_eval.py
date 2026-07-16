"""Run full 30-query accuracy evaluation with LLM-as-judge scoring."""

import os
import sys
import time
import json

os.environ["HF_HUB_OFFLINE"] = "1"
sys.path.insert(0, r"D:\Vs Code\VS code\Hector")

from core.orchestrator import HectorOrchestrator

# Suppress noisy logs
import logging

logging.disable(logging.WARNING)

TEST_QUERIES = [
    # EXACT (10)
    {
        "id": 1,
        "query": "What is the punishment for murder under Section 302 IPC",
        "category": "exact",
        "expected_keywords": [
            "302",
            "murder",
            "punishment",
            "death",
            "life imprisonment",
        ],
    },
    {
        "id": 2,
        "query": "Section 376 IPC punishment for rape",
        "category": "exact",
        "expected_keywords": ["376", "rape", "punishment", "imprisonment"],
    },
    {
        "id": 3,
        "query": "Bharatiya Nagarik Suraksha Sanhita bail provisions",
        "category": "exact",
        "expected_keywords": ["bail", "BNSS", "Bharatiya Nagarik", "anticipatory"],
    },
    {
        "id": 4,
        "query": "Indian Evidence Act Section 65B admissibility of electronic evidence",
        "category": "exact",
        "expected_keywords": [
            "65B",
            "electronic evidence",
            "admissibility",
            "certificate",
        ],
    },
    {
        "id": 5,
        "query": "Transfer of Property Act Section 54 sale of immovable property",
        "category": "exact",
        "expected_keywords": ["54", "sale", "immovable property", "registration"],
    },
    {
        "id": 6,
        "query": "Section 144 CrPC now Section 163 BNSS power to issue orders",
        "category": "exact",
        "expected_keywords": ["144", "163", "BNSS", "CrPC", "order"],
    },
    {
        "id": 7,
        "query": "Section 498A IPC punishment for dowry harassment",
        "category": "exact",
        "expected_keywords": ["498A", "dowry", "cruelty", "punishment", "husband"],
    },
    {
        "id": 8,
        "query": "NDPS Act Section 20 punishment for drug trafficking",
        "category": "exact",
        "expected_keywords": [
            "NDPS",
            "Section 20",
            "drug",
            "punishment",
            "trafficking",
        ],
    },
    {
        "id": 9,
        "query": "Article 21 Constitution of India right to life and personal liberty",
        "category": "exact",
        "expected_keywords": [
            "Article 21",
            "right to life",
            "personal liberty",
            "Constitution",
        ],
    },
    {
        "id": 10,
        "query": "Consumer Protection Act Section 38 unfair trade practice",
        "category": "exact",
        "expected_keywords": ["Section 38", "consumer", "unfair trade", "practice"],
    },
    # SIMILAR (10)
    {
        "id": 11,
        "query": "What happens if someone is charged with a crime they didn't commit?",
        "category": "similar",
        "expected_keywords": ["false", "wrongful", "acquittal", "innocent"],
    },
    {
        "id": 12,
        "query": "My in-laws are demanding money from me. What legal options do I have?",
        "category": "similar",
        "expected_keywords": ["dowry", "cruelty", "498A", "maintenance"],
    },
    {
        "id": 13,
        "query": "Someone forged my signature on a document. Is that a crime?",
        "category": "similar",
        "expected_keywords": ["forgery", "fraud", "signature", "crime"],
    },
    {
        "id": 14,
        "query": "Is a confession made to police admissible in court?",
        "category": "similar",
        "expected_keywords": [
            "confession",
            "police",
            "admissible",
            "Section 25",
            "evidence",
        ],
    },
    {
        "id": 15,
        "query": "What is the time limit to file a civil suit in India?",
        "category": "similar",
        "expected_keywords": ["limitation", "time limit", "3 years", "Limitation Act"],
    },
    {
        "id": 16,
        "query": "My employer is not paying wages. What legal remedy do I have?",
        "category": "similar",
        "expected_keywords": [
            "wages",
            "employer",
            "Industrial Disputes",
            "labour court",
        ],
    },
    {
        "id": 17,
        "query": "Can a minor enter into a valid contract?",
        "category": "similar",
        "expected_keywords": [
            "minor",
            "contract",
            "void",
            "Section 10",
            "Indian Contract Act",
        ],
    },
    {
        "id": 18,
        "query": "What is the punishment for driving under influence of alcohol in India?",
        "category": "similar",
        "expected_keywords": [
            "drunk driving",
            "Motor Vehicles Act",
            "Section 185",
            "penalty",
        ],
    },
    {
        "id": 19,
        "query": "How does inheritance work if someone dies without a will in Hindu family?",
        "category": "similar",
        "expected_keywords": [
            "intestate",
            "Hindu Succession Act",
            "heir",
            "coparcenary",
        ],
    },
    {
        "id": 20,
        "query": "What rights does an accused person have during police interrogation?",
        "category": "similar",
        "expected_keywords": ["accused", "rights", "police", "legal counsel", "BNSS"],
    },
    # IRRELEVANT (10)
    {
        "id": 21,
        "query": "What is the capital of France?",
        "category": "irrelevant",
        "expected_keywords": [],
    },
    {
        "id": 22,
        "query": "Tell me a joke about lawyers",
        "category": "irrelevant",
        "expected_keywords": [],
    },
    {
        "id": 23,
        "query": "How do I make pasta carbonara?",
        "category": "irrelevant",
        "expected_keywords": [],
    },
    {
        "id": 24,
        "query": "What is the best programming language?",
        "category": "irrelevant",
        "expected_keywords": [],
    },
    {
        "id": 25,
        "query": "Who won the last FIFA World Cup?",
        "category": "irrelevant",
        "expected_keywords": [],
    },
    {
        "id": 26,
        "query": "How do I train my dog?",
        "category": "irrelevant",
        "expected_keywords": [],
    },
    {
        "id": 27,
        "query": "What is machine learning?",
        "category": "irrelevant",
        "expected_keywords": [],
    },
    {
        "id": 28,
        "query": "Recommend a good restaurant in Mumbai",
        "category": "irrelevant",
        "expected_keywords": [],
    },
    {
        "id": 29,
        "query": "What is the weather today?",
        "category": "irrelevant",
        "expected_keywords": [],
    },
    {
        "id": 30,
        "query": "How do I invest in cryptocurrency?",
        "category": "irrelevant",
        "expected_keywords": [],
    },
]


def llm_judge_score(query, response, expected_keywords, category="exact"):
    """Use NIM LLM to score answer quality 0-100. Retries on failure."""
    try:
        from core.nim_llm import get_nim_llm
        import time as _time

        client = get_nim_llm()

        hint = ""
        if expected_keywords:
            hint = f"\nExpected key terms: {', '.join(expected_keywords[:10])}"

        if category == "irrelevant":
            system_msg = (
                "You are a legal answer evaluator. The query is NOT a legal question.\n"
                "Score based on whether the system correctly identified it as non-legal:\n"
                "- 90-100: Correctly refused or redirected (not giving legal advice)\n"
                "- 50-89: Partially correct, acknowledged it's not legal\n"
                "- 0-49: Incorrectly gave legal advice or irrelevant response\n\n"
                'Return ONLY a JSON object: {"score": <int>, "reason": "<one sentence>"}'
            )
        else:
            system_msg = (
                "You are a legal answer evaluator. Score the answer from 0-100.\n"
                "Scoring criteria:\n"
                "- 90-100: Correct, complete, cites relevant sections/acts, directly answers the query\n"
                "- 70-89: Mostly correct, may miss some details or citations\n"
                "- 50-69: Partially correct, addresses the topic but incomplete\n"
                "- 30-49: Vague or tangential, some relevant content\n"
                "- 0-29: Wrong, irrelevant, or no meaningful answer\n\n"
                'Return ONLY a JSON object: {"score": <int>, "reason": "<one sentence>"}'
            )

        messages = [
            {"role": "system", "content": system_msg},
            {
                "role": "user",
                "content": f"Query: {query}\nAnswer: {response[:2000]}\n{hint}\n\n"
                "Score this answer 0-100. Return JSON only.",
            },
        ]
        # Try up to 2 times
        for attempt in range(2):
            try:
                result = client.chat_json(messages, temperature=0.0, max_tokens=100)
                return max(0, min(100, int(result.get("score", 50)))), "llm"
            except Exception:
                if attempt == 0:
                    _time.sleep(2)
                    continue
                raise
    except Exception:
        # Improved fallback: fuzzy keyword matching
        response_lower = response.lower()
        matched = 0
        for kw in expected_keywords:
            kw_lower = kw.lower()
            if kw_lower in response_lower:
                matched += 1
            elif all(w in response_lower for w in kw_lower.split()):
                matched += 0.5
        return min(
            100, int((matched / max(len(expected_keywords), 1)) * 100)
        ), "keyword"


def run():
    print("=" * 70)
    print("HECTOR ACCURACY EVALUATION (30 queries, LLM-as-judge)")
    print("=" * 70)

    orchestrator = HectorOrchestrator(enable_verification=False)
    results = []
    start = time.time()

    for q in TEST_QUERIES:
        t0 = time.time()
        response = orchestrator.execute(q["query"])
        elapsed = time.time() - t0
        timing = orchestrator.get_last_timing()

        score, method = llm_judge_score(
            q["query"], response, q["expected_keywords"], q["category"]
        )

        result = {
            "id": q["id"],
            "query": q["query"][:80],
            "category": q["category"],
            "score": score,
            "method": method,
            "retrieve_ms": timing.get("retrieve_ms", 0),
            "elapsed_s": round(elapsed, 1),
        }
        results.append(result)

        status = "PASS" if score >= 50 else "FAIL"
        print(
            f"Q{q['id']:2d} [{q['category']:9s}] {score:3d}/100 [{status}] {method:8s} {elapsed:5.1f}s | {q['query'][:55]}"
        )

    # Summary
    elapsed_total = time.time() - start
    exact_scores = [r["score"] for r in results if r["category"] == "exact"]
    similar_scores = [r["score"] for r in results if r["category"] == "similar"]
    irrelevant_scores = [r["score"] for r in results if r["category"] == "irrelevant"]
    all_scores = [r["score"] for r in results]

    print(f"\n{'=' * 70}")
    print("RESULTS")
    print(f"{'=' * 70}")
    print(
        f"Exact (10):     {sum(exact_scores) / len(exact_scores):.1f}% avg | scores: {exact_scores}"
    )
    print(
        f"Similar (10):   {sum(similar_scores) / len(similar_scores):.1f}% avg | scores: {similar_scores}"
    )
    print(
        f"Irrelevant (10): {sum(irrelevant_scores) / len(irrelevant_scores):.1f}% avg | scores: {irrelevant_scores}"
    )
    print(f"OVERALL:        {sum(all_scores) / len(all_scores):.1f}% avg")
    print(
        f"Time:           {elapsed_total:.0f}s total ({elapsed_total / 30:.1f}s/query)"
    )

    # Save results
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
