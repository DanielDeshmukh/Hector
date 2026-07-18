"""
HECTOR QI Pipeline Eval — Tests Query Intelligence + Retrieval for all 30 queries.
Shows: QI intent, metadata filters, retrieved chunks, scores.
"""
import os, sys, json, time

os.environ["HF_HUB_OFFLINE"] = "1"
sys.path.insert(0, r"D:\Vs Code\VS code\Hector")

from core.query_intelligence import analyze_query
from core.query_parser import get_parser
from core.query_expander import QueryExpander
from data.hybrid_retriever import HectorHybridRetriever

TEST_QUERIES = [
    {"id": 1, "query": "What is the punishment for murder under Section 302 IPC", "category": "exact", "kw": ["302", "murder", "punishment", "death", "life imprisonment"]},
    {"id": 2, "query": "Section 376 IPC punishment for rape", "category": "exact", "kw": ["376", "rape", "punishment", "imprisonment"]},
    {"id": 3, "query": "Bharatiya Nagarik Suraksha Sanhita bail provisions", "category": "exact", "kw": ["bail", "BNSS", "Bharatiya Nagarik", "anticipatory"]},
    {"id": 4, "query": "Indian Evidence Act Section 65B admissibility of electronic evidence", "category": "exact", "kw": ["65B", "electronic evidence", "admissibility", "certificate"]},
    {"id": 5, "query": "Transfer of Property Act Section 54 sale of immovable property", "category": "exact", "kw": ["54", "sale", "immovable property", "registration"]},
    {"id": 6, "query": "Section 144 CrPC now Section 163 BNSS power to issue orders", "category": "exact", "kw": ["144", "163", "BNSS", "CrPC", "order"]},
    {"id": 7, "query": "Section 498A IPC punishment for dowry harassment", "category": "exact", "kw": ["498A", "dowry", "cruelty", "punishment", "husband"]},
    {"id": 8, "query": "NDPS Act Section 20 punishment for drug trafficking", "category": "exact", "kw": ["NDPS", "Section 20", "drug", "punishment", "trafficking"]},
    {"id": 9, "query": "Article 21 Constitution of India right to life and personal liberty", "category": "exact", "kw": ["Article 21", "right to life", "personal liberty", "Constitution"]},
    {"id": 10, "query": "Consumer Protection Act Section 38 unfair trade practice", "category": "exact", "kw": ["Section 38", "consumer", "unfair trade", "practice"]},
    {"id": 11, "query": "What happens if someone is charged with a crime they didn't commit?", "category": "similar", "kw": ["false", "wrongful", "acquittal", "innocent"]},
    {"id": 12, "query": "My in-laws are demanding money from me. What legal options do I have?", "category": "similar", "kw": ["dowry", "cruelty", "498A", "maintenance"]},
    {"id": 13, "query": "Someone forged my signature on a document. Is that a crime?", "category": "similar", "kw": ["forgery", "fraud", "signature", "crime"]},
    {"id": 14, "query": "Is a confession made to police admissible in court?", "category": "similar", "kw": ["confession", "police", "admissible", "Section 25", "evidence"]},
    {"id": 15, "query": "What is the time limit to file a civil suit in India?", "category": "similar", "kw": ["limitation", "time limit", "3 years", "Limitation Act"]},
    {"id": 16, "query": "My employer is not paying wages. What legal remedy do I have?", "category": "similar", "kw": ["wages", "employer", "Industrial Disputes", "labour court"]},
    {"id": 17, "query": "Can a minor enter into a valid contract?", "category": "similar", "kw": ["minor", "contract", "void", "Section 10", "Indian Contract Act"]},
    {"id": 18, "query": "What is the punishment for driving under influence of alcohol in India?", "category": "similar", "kw": ["drunk driving", "Motor Vehicles Act", "Section 185", "penalty"]},
    {"id": 19, "query": "How does inheritance work if someone dies without a will in Hindu family?", "category": "similar", "kw": ["intestate", "Hindu Succession Act", "heir", "coparcenary"]},
    {"id": 20, "query": "What rights does an accused person have during police interrogation?", "category": "similar", "kw": ["accused", "rights", "police", "legal counsel", "BNSS"]},
    {"id": 21, "query": "What is the capital of France?", "category": "irrelevant", "kw": []},
    {"id": 22, "query": "Tell me a joke about lawyers", "category": "irrelevant", "kw": []},
    {"id": 23, "query": "How do I make pasta carbonara?", "category": "irrelevant", "kw": []},
    {"id": 24, "query": "What is the best programming language?", "category": "irrelevant", "kw": []},
    {"id": 25, "query": "Who won the last FIFA World Cup?", "category": "irrelevant", "kw": []},
    {"id": 26, "query": "How do I train my dog?", "category": "irrelevant", "kw": []},
    {"id": 27, "query": "What is machine learning?", "category": "irrelevant", "kw": []},
    {"id": 28, "query": "Recommend a good restaurant in Mumbai", "category": "irrelevant", "kw": []},
    {"id": 29, "query": "What is the weather today?", "category": "irrelevant", "kw": []},
    {"id": 30, "query": "How do I invest in cryptocurrency?", "category": "irrelevant", "kw": []},
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


def format_chunks(chunks, metas, max_show=3):
    """Format retrieved chunks for display."""
    lines = []
    for i, (chunk, meta) in enumerate(zip(chunks[:max_show], metas[:max_show])):
        act = meta.get("real_act_name", meta.get("act_name", "?"))
        sec = meta.get("section_number", "?")
        title = meta.get("title", "?")
        score = meta.get("score", 0)
        text = chunk[:200].replace("\n", " ")
        lines.append(f"      [{i+1}] {act} | Sec {sec} | score={score:.3f}")
        lines.append(f"          {title[:80]}")
        lines.append(f"          \"{text}...\"")
    if len(chunks) > max_show:
        lines.append(f"      ... +{len(chunks)-max_show} more chunks")
    return "\n".join(lines)


def run():
    print("=" * 80)
    print("HECTOR QI PIPELINE EVAL — 30 Queries with Query Intelligence")
    print("=" * 80)
    print()

    retriever = HectorHybridRetriever()
    parser = get_parser()
    expander = QueryExpander()

    results = []
    start = time.time()

    for q in TEST_QUERIES:
        t0 = time.time()
        query = q["query"]
        category = q["category"]

        # Step 1: QI Analysis (rule-based, no NIM for speed)
        qi = analyze_query(query, use_nim=False)

        # Step 2: Parse entities
        entities = parser.parse(query)
        entity_dict = entities.to_dict()

        # Step 3: Merge QI metadata filters into entities
        qi_filters = qi.metadata_filters
        for act_name in qi_filters.get("act_name", []):
            if act_name and act_name not in (entity_dict.get("acts") or []):
                entity_dict.setdefault("acts", []).append(act_name)
        for sec in qi_filters.get("section_number", []):
            if sec and sec not in (entity_dict.get("sections") or []):
                entity_dict.setdefault("sections", []).append(sec)

        # Step 4: Decide search method based on QI strategy
        has_section = bool(entity_dict.get("sections") or entity_dict.get("ipc_sections") or entity_dict.get("bns_sections"))
        has_act = bool(entity_dict.get("acts"))

        # Step 5: Retrieve
        if has_section or has_act:
            search_results = retriever.search_with_metadata_filters(query, entity_dict, top_k=10)
        else:
            search_results = retriever.search(query, top_k=10)

        elapsed = time.time() - t0

        # Step 6: Extract chunks and score
        chunks = [r.get("document", r.get("text", "")) for r in search_results]
        metas = [r.get("metadata", {}) for r in search_results]
        score = score_retrieval(query, chunks, q["kw"], category)

        # Step 7: Print detailed result
        status = "PASS" if score >= 50 else "FAIL"
        print("-" * 80)
        print(f"Q{q['id']:2d} [{category:9s}] {score:3d}/100 [{status}] {elapsed*1000:6.0f}ms")
        print(f"    Query: {query}")
        print(f"    QI Intent: {qi.intent} | Confidence: {qi.confidence:.2f}")
        print(f"    QI Source: {qi.source_act} {qi.source_section}")
        print(f"    QI Target: {qi.target_act} {qi.target_section}")
        print(f"    QI Mapping: {qi.mapping_info or 'N/A'}")
        print(f"    QI Strategy: {qi.search_strategy}")
        print(f"    QI Filters: {qi.metadata_filters}")
        print(f"    Search Method: {'filtered' if (has_section or has_act) else 'unfiltered'}")
        print(f"    Results: {len(search_results)} chunks")
        if search_results:
            print(f"    Top Chunks:")
            print(format_chunks(chunks, metas, max_show=3))
        print()

        result = {
            "id": q["id"],
            "query": query[:80],
            "category": category,
            "score": score,
            "qi_intent": qi.intent,
            "qi_confidence": qi.confidence,
            "qi_source": f"{qi.source_act} {qi.source_section}",
            "qi_target": f"{qi.target_act} {qi.target_section}",
            "qi_strategy": qi.search_strategy,
            "qi_filters": qi.metadata_filters,
            "search_method": "filtered" if (has_section or has_act) else "unfiltered",
            "retrieve_ms": round(elapsed * 1000, 1),
            "n_chunks": len(chunks),
        }
        results.append(result)

    elapsed_total = time.time() - start

    # Summary
    exact_scores = [r["score"] for r in results if r["category"] == "exact"]
    similar_scores = [r["score"] for r in results if r["category"] == "similar"]
    irrelevant_scores = [r["score"] for r in results if r["category"] == "irrelevant"]
    all_scores = [r["score"] for r in results]

    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Exact (10):      {sum(exact_scores)/len(exact_scores):.1f}% avg | {exact_scores}")
    print(f"Similar (10):    {sum(similar_scores)/len(similar_scores):.1f}% avg | {similar_scores}")
    print(f"Irrelevant (10): {sum(irrelevant_scores)/len(irrelevant_scores):.1f}% avg | {irrelevant_scores}")
    print(f"OVERALL:         {sum(all_scores)/len(all_scores):.1f}% avg")
    print(f"Time:            {elapsed_total:.0f}s total ({elapsed_total/30:.1f}s/query)")
    print()

    # QI stats
    qi_intents = {}
    qi_filtered = 0
    qi_unfiltered = 0
    for r in results:
        intent = r["qi_intent"]
        qi_intents[intent] = qi_intents.get(intent, 0) + 1
        if r["search_method"] == "filtered":
            qi_filtered += 1
        else:
            qi_unfiltered += 1

    print("QI STATS:")
    print(f"  Intents: {qi_intents}")
    print(f"  Filtered searches: {qi_filtered}")
    print(f"  Unfiltered searches: {qi_unfiltered}")
    print()

    # Cross-act mapping queries specifically
    cross_act = [r for r in results if r["qi_intent"] == "cross_act_mapping"]
    if cross_act:
        print(f"CROSS-ACT MAPPING QUERIES ({len(cross_act)}):")
        for r in cross_act:
            print(f"  Q{r['id']}: {r['query'][:60]}")
            print(f"    Source: {r['qi_source']} -> Target: {r['qi_target']}")
            print(f"    Filters: {r['qi_filters']}")
            print(f"    Score: {r['score']}/100")
        print()

    # Save results
    output = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "overall_pct": round(sum(all_scores)/len(all_scores), 1),
        "exact_pct": round(sum(exact_scores)/len(exact_scores), 1),
        "similar_pct": round(sum(similar_scores)/len(similar_scores), 1),
        "irrelevant_pct": round(sum(irrelevant_scores)/len(irrelevant_scores), 1),
        "qi_stats": qi_intents,
        "results": results,
    }
    with open("qi_pipeline_results.json", "w") as f:
        json.dump(output, f, indent=2)
    print("Saved to qi_pipeline_results.json")


if __name__ == "__main__":
    run()
