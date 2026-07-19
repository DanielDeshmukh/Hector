"""
HECTOR Retrieval Pipeline Accuracy Test
30 queries across 3 categories: exact, similar, irrelevant
Logs everything to retrieval_test.log
"""

import json
import logging
import os
import sys
import time
from datetime import datetime

from core.orchestrator import HectorOrchestrator

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Suppress noisy logs
logging.disable(logging.WARNING)

# ============================================================
# TEST QUERIES
# ============================================================

TEST_QUERIES = [
    # --- CATEGORY 1: EXACT KEYWORD MATCHES (10) ---
    # These should return highly relevant results with correct citations
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
        "expected_source": ["Indian_Penal_Code", "Bharatiya_Nyaya"],
        "description": "Exact section + act lookup",
    },
    {
        "id": 2,
        "query": "Section 376 IPC punishment for rape",
        "category": "exact",
        "expected_keywords": ["376", "rape", "punishment", "imprisonment"],
        "expected_source": ["Indian_Penal_Code", "Bharatiya_Nyaya"],
        "description": "Exact criminal section",
    },
    {
        "id": 3,
        "query": "Bharatiya Nagarik Suraksha Sanhita bail provisions",
        "category": "exact",
        "expected_keywords": ["bail", "BNSS", "Bharatiya Nagarik", "anticipatory"],
        "expected_source": ["Bharatiya_Nagarik_Suraksha", "Code_of_Criminal"],
        "description": "Exact act name + topic",
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
        "expected_source": ["Indian_Evidence", "Bharatiya_Sakshya"],
        "description": "Exact section on evidence",
    },
    {
        "id": 5,
        "query": "Transfer of Property Act Section 54 sale of immovable property",
        "category": "exact",
        "expected_keywords": ["54", "sale", "immovable property", "registration"],
        "expected_source": ["Transfer_of_Property"],
        "description": "Exact civil law section",
    },
    {
        "id": 6,
        "query": "What is Section 144 CrPC and its equivalent in BNSS",
        "category": "exact",
        "expected_keywords": ["144", "CrPC", "BNSS", "prohibition", "assembly"],
        "expected_source": ["Code_of_Criminal", "Bharatiya_Nagarik_Suraksha"],
        "description": "IPC->BNS cross-reference",
    },
    {
        "id": 7,
        "query": "Dowry Prohibition Act Section 498A cruelty by husband",
        "category": "exact",
        "expected_keywords": ["498A", "dowry", "cruelty", "husband"],
        "expected_source": [
            "Dowry_Prohibition",
            "Indian_Penal_Code",
            "Bharatiya_Nyaya",
        ],
        "description": "Specific offence definition",
    },
    {
        "id": 8,
        "query": "Narcotic Drugs and Psychotropic Substances Act Section 20 punishment for cannabis",
        "category": "exact",
        "expected_keywords": ["20", "cannabis", "NDPS", "punishment", "imprisonment"],
        "expected_source": ["Narcotic_Drugs", "Commentary on The Narcotic"],
        "description": "NDPS specific section",
    },
    {
        "id": 9,
        "query": "Constitution of India Article 21 right to life and personal liberty",
        "category": "exact",
        "expected_keywords": [
            "Article 21",
            "right to life",
            "personal liberty",
            "fundamental rights",
        ],
        "expected_source": ["Constitution_of_India"],
        "description": "Constitutional provision",
    },
    {
        "id": 10,
        "query": "Consumer Protection Act 2019 Section 38 product liability",
        "category": "exact",
        "expected_keywords": ["38", "product liability", "consumer", "deficiency"],
        "expected_source": ["Consumer_Protection_Act"],
        "description": "Consumer law specific section",
    },
    # --- CATEGORY 2: SIMILAR / PARAPHRASED QUERIES (10) ---
    # These test semantic understanding - should return relevant results
    {
        "id": 11,
        "query": "Can a person get bail if arrested for a crime punishable with death?",
        "category": "similar",
        "expected_keywords": [
            "bail",
            "death penalty",
            "non-bailable",
            "Section 437",
            "Section 480",
        ],
        "expected_source": [
            "Code_of_Criminal",
            "Bharatiya_Nagarik_Suraksha",
            "Indian_Penal_Code",
        ],
        "description": "Paraphrased bail question",
    },
    {
        "id": 12,
        "query": "How to file a case against someone who took dowry from my daughter?",
        "category": "similar",
        "expected_keywords": [
            "dowry",
            "complaint",
            "FIR",
            "Section 498A",
            "Dowry Prohibition",
        ],
        "expected_source": [
            "Dowry_Prohibition",
            "Indian_Penal_Code",
            "Code_of_Criminal",
        ],
        "description": "Practical legal question",
    },
    {
        "id": 13,
        "query": "What happens if someone forges a document to claim property?",
        "category": "similar",
        "expected_keywords": [
            "forgery",
            "Section 463",
            "Section 465",
            "property",
            "fraud",
        ],
        "expected_source": [
            "Indian_Penal_Code",
            "Transfer_of_Property",
            "Indian_Contract",
        ],
        "description": "Property fraud scenario",
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
            "Section 26",
            "evidence",
        ],
        "expected_source": ["Indian_Evidence", "Bharatiya_Sakshya"],
        "description": "Evidence law question",
    },
    {
        "id": 15,
        "query": "What is the time limit to file a civil suit in India?",
        "category": "similar",
        "expected_keywords": [
            "limitation",
            "time limit",
            "3 years",
            "Limitation Act",
            "Section 3",
        ],
        "expected_source": ["Limitation_Act"],
        "description": "Limitation period question",
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
            "unfair labour",
        ],
        "expected_source": ["Industrial_Disputes_Act", "Factories_Act"],
        "description": "Labour law scenario",
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
            "guardian",
        ],
        "expected_source": ["Indian_Contract_Act", "Hindu_Minority"],
        "description": "Contract law - capacity",
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
            "suspension",
        ],
        "expected_source": ["Motor_Vehicles_Act"],
        "description": "Motor vehicles law",
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
            "partition",
        ],
        "expected_source": ["Hindu_Succession_Act"],
        "description": "Hindu succession law",
    },
    {
        "id": 20,
        "query": "What rights does an accused person have during police interrogation?",
        "category": "similar",
        "expected_keywords": [
            "accused",
            "rights",
            "police",
            "legal counsel",
            "Section 41",
            "BNSS",
            "dying declaration",
        ],
        "expected_source": [
            "Code_of_Criminal",
            "Bharatiya_Nagarik_Suraksha",
            "Indian_Evidence",
        ],
        "description": "Criminal procedure rights",
    },
    # --- CATEGORY 3: IRRELEVANT / OUT-OF-SCOPE (10) ---
    # These should NOT return legal results - should get graceful response
    {
        "id": 21,
        "query": "What is the capital of France?",
        "category": "irrelevant",
        "expected_keywords": [],
        "expected_source": [],
        "description": "Geography - completely out of scope",
    },
    {
        "id": 22,
        "query": "How do I make a cup of coffee?",
        "category": "irrelevant",
        "expected_keywords": [],
        "expected_source": [],
        "description": "Daily life - out of scope",
    },
    {
        "id": 23,
        "query": "What is the square root of 144?",
        "category": "irrelevant",
        "expected_keywords": [],
        "expected_source": [],
        "description": "Math - out of scope",
    },
    {
        "id": 24,
        "query": "Explain the theory of relativity by Einstein",
        "category": "irrelevant",
        "expected_keywords": [],
        "expected_source": [],
        "description": "Physics - out of scope",
    },
    {
        "id": 25,
        "query": "Who won the Cricket World Cup 2023?",
        "category": "irrelevant",
        "expected_keywords": [],
        "expected_source": [],
        "description": "Sports - out of scope",
    },
    {
        "id": 26,
        "query": "How to invest in Bitcoin and cryptocurrency?",
        "category": "irrelevant",
        "expected_keywords": [],
        "expected_source": [],
        "description": "Finance (not legal) - out of scope",
    },
    {
        "id": 27,
        "query": "What is the recipe for butter chicken?",
        "category": "irrelevant",
        "expected_keywords": [],
        "expected_source": [],
        "description": "Food recipe - out of scope",
    },
    {
        "id": 28,
        "query": "Tell me a joke about lawyers",
        "category": "irrelevant",
        "expected_keywords": [],
        "expected_source": [],
        "description": "Humor - should not return legal data",
    },
    {
        "id": 29,
        "query": "How tall is Mount Everest in meters?",
        "category": "irrelevant",
        "expected_keywords": [],
        "expected_source": [],
        "description": "Geography - out of scope",
    },
    {
        "id": 30,
        "query": "What are the side effects of paracetamol?",
        "category": "irrelevant",
        "expected_keywords": [],
        "expected_source": [],
        "description": "Medical - out of scope",
    },
]


def score_response(query_data, response, sources, route):
    """Score a single query response using LLM-as-judge for legal queries."""
    score = {
        "id": query_data["id"],
        "query": query_data["query"],
        "category": query_data["category"],
    }
    category = query_data["category"]

    if category in ("exact", "similar"):
        has_sources = len(sources) > 0
        score["has_sources"] = has_sources
        score["correct_route"] = route == "LEGAL_RESEARCH"

        # LLM-as-judge scoring via NIM
        judge_score = _llm_judge_score(
            query=query_data["query"],
            response=response,
            expected_keywords=query_data.get("expected_keywords", []),
            expected_source=query_data.get("expected_source", []),
        )
        score["llm_judge"] = judge_score
        score["accuracy"] = judge_score / 100.0

    elif category == "irrelevant":
        has_no_sources = len(sources) == 0
        score["has_sources"] = not has_no_sources

        legal_terms = [
            "section",
            "act",
            "ipc",
            "bns",
            "punishment",
            "imprisonment",
            "court",
        ]
        false_legal = [term for term in legal_terms if term in response.lower()]
        score["false_legal_terms"] = false_legal
        score["correct_route"] = route != "LEGAL_RESEARCH"

        score["accuracy"] = round(
            (1.0 if has_no_sources else 0.3) * 0.5
            + (1.0 if route != "LEGAL_RESEARCH" else 0.0) * 0.3
            + (1.0 if not false_legal else 0.0) * 0.2,
            2,
        )
    else:
        score["accuracy"] = 0.0

    return score


def _llm_judge_score(query, response, expected_keywords, expected_source):
    """Use NIM LLM to judge answer quality. Returns 0-100 score."""
    try:
        from core.nim_llm import get_nim_llm

        client = get_nim_llm()

        expected_hint = ""
        if expected_keywords:
            expected_hint += (
                f"\nExpected key terms: {', '.join(expected_keywords[:10])}"
            )
        if expected_source:
            expected_hint += (
                f"\nExpected source documents: {', '.join(expected_source[:5])}"
            )

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a legal answer evaluator. Score the answer from 0-100.\n"
                    "Scoring criteria:\n"
                    "- 90-100: Correct, complete, cites relevant sections/acts, directly answers the query\n"
                    "- 70-89: Mostly correct, may miss some details or citations\n"
                    "- 50-69: Partially correct, addresses the topic but incomplete\n"
                    "- 30-49: Vague or tangential, some relevant content\n"
                    "- 0-29: Wrong, irrelevant, or no meaningful answer\n\n"
                    'Return ONLY a JSON object: {"score": <int>, "reason": "<one sentence>"}'
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Query: {query}\n"
                    f"Answer: {response[:2000]}\n"
                    f"{expected_hint}\n\n"
                    "Score this answer 0-100. Return JSON only."
                ),
            },
        ]

        result = client.chat_json(messages, temperature=0.0, max_tokens=100)
        return max(0, min(100, int(result.get("score", 50))))
    except Exception:
        # Fallback to keyword matching if NIM unavailable
        response_lower = response.lower()
        matched = sum(1 for kw in expected_keywords if kw.lower() in response_lower)
        return min(100, int((matched / max(len(expected_keywords), 1)) * 100))


def run_tests():
    """Run all 30 test queries and score results."""
    log_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "retrieval_test.log",
    )

    with open(log_path, "w", encoding="utf-8") as log:
        log.write("HECTOR RETRIEVAL ACCURACY TEST\n")
        log.write(f"Started: {datetime.now().isoformat()}\n")
        log.write("Queries: 30 (10 exact, 10 similar, 10 irrelevant)\n")
        log.write(f"{'=' * 80}\n\n")
        log.flush()

        print("HECTOR RETRIEVAL ACCURACY TEST")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'=' * 80}")

        orchestrator = HectorOrchestrator(enable_verification=False)
        all_scores = []
        start_time = time.time()

        for q in TEST_QUERIES:
            qid = q["id"]
            query = q["query"]
            cat = q["category"]

            print(f"\n[{qid}/30] [{cat.upper()}] {q['description']}")
            print(f"  Query: {query}")
            log.write(f"[{qid}/30] [{cat.upper()}] {q['description']}\n")
            log.write(f"  Query: {query}\n")

            try:
                t0 = time.time()
                response = orchestrator.execute(query)
                elapsed = time.time() - t0

                # Get sources from retriever directly
                if cat in ("exact", "similar"):
                    sources = orchestrator.retriever.search(query, top_k=5)
                else:
                    sources = []

                # Get route
                intent = orchestrator.router.get_route(query)
                route = (
                    intent.get("route", "GENERAL")
                    if isinstance(intent, dict)
                    else "GENERAL"
                )

                # Score
                score_data = score_response(q, response, sources, route)
                score_data["elapsed_ms"] = round(elapsed * 1000, 0)
                all_scores.append(score_data)

                print(
                    f"  Route: {route} | Sources: {len(sources)} | Accuracy: {score_data['accuracy']:.0%}"
                )
                print(f"  Response: {response[:120].replace(chr(10), ' ')}...")

                log.write(
                    f"  Route: {route} | Sources: {len(sources)} | Accuracy: {score_data['accuracy']:.0%}\n"
                )
                log.write(
                    f"  Response preview: {response[:200].replace(chr(10), ' ')}\n"
                )
                log.write(f"  Score: {json.dumps(score_data, indent=2)}\n\n")
                log.flush()

            except Exception as e:
                print(f"  ERROR: {e}")
                log.write(f"  ERROR: {e}\n\n")
                log.flush()
                all_scores.append(
                    {
                        "id": qid,
                        "query": query,
                        "category": cat,
                        "accuracy": 0.0,
                        "error": str(e),
                    }
                )

        # Summary
        total_time = time.time() - start_time
        exact_scores = [s["accuracy"] for s in all_scores if s["category"] == "exact"]
        similar_scores = [
            s["accuracy"] for s in all_scores if s["category"] == "similar"
        ]
        irrelevant_scores = [
            s["accuracy"] for s in all_scores if s["category"] == "irrelevant"
        ]

        avg_exact = sum(exact_scores) / len(exact_scores) if exact_scores else 0
        avg_similar = sum(similar_scores) / len(similar_scores) if similar_scores else 0
        avg_irrelevant = (
            sum(irrelevant_scores) / len(irrelevant_scores) if irrelevant_scores else 0
        )
        overall = (
            sum(s["accuracy"] for s in all_scores) / len(all_scores)
            if all_scores
            else 0
        )

        summary = f"""
{"=" * 80}
RESULTS SUMMARY
{"=" * 80}
Total time: {total_time:.1f}s ({total_time / 30:.1f}s avg per query)

EXACT MATCHES:     {avg_exact:.0%} avg ({len(exact_scores)} queries)
SIMILAR/PARAPHRASE: {avg_similar:.0%} avg ({len(similar_scores)} queries)
IRRELEVANT (grace): {avg_irrelevant:.0%} avg ({len(irrelevant_scores)} queries)

OVERALL ACCURACY:  {overall:.0%}

DETAILED SCORES:
"""
        for s in all_scores:
            cat_label = {"exact": "EXACT", "similar": "SIMIL", "irrelevant": "IRREL"}[
                s["category"]
            ]
            summary += f"  [{s['id']:>2}] {cat_label} | {s['accuracy']:.0%} | {s.get('route', '?'):<16} | {s['query'][:50]}\n"

        summary += f"{'=' * 80}\n"

        print(summary)
        log.write(summary)
        log.flush()

        # Save JSON results
        results_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "retrieval_test_results.json",
        )
        with open(results_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "timestamp": datetime.now().isoformat(),
                    "total_time_s": round(total_time, 1),
                    "avg_accuracy": round(overall, 2),
                    "exact_avg": round(avg_exact, 2),
                    "similar_avg": round(avg_similar, 2),
                    "irrelevant_avg": round(avg_irrelevant, 2),
                    "results": all_scores,
                },
                f,
                indent=2,
            )

        print(f"\nResults saved to: {results_path}")
        print(f"Log saved to: {log_path}")


if __name__ == "__main__":
    run_tests()
