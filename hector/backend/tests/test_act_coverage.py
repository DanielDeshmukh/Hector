#!/usr/bin/env python3
"""HECTOR Act Coverage — semantic-only (no BM25 load needed)."""
import os, sys, time, json
from datetime import datetime

env_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env")
env_path = os.path.abspath(env_path)
import pytest
if not os.path.exists(env_path):
    pytest.skip("requires local .env with live credentials", allow_module_level=True)
for line in open(env_path):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())

sys.path.insert(0, r"D:\Vs Code\VS code\Hector\hector\api")
sys.path.insert(0, r"D:\Vs Code\VS code\Hector\hector")

from data.hybrid_retriever import HectorHybridRetriever
from pinecone import Pinecone

print("=" * 70)
print("HECTOR ACT COVERAGE EVALUATION (Semantic Search)")
print(f"Started: {datetime.now().isoformat()}")
print("=" * 70)

r = HectorHybridRetriever.__new__(HectorHybridRetriever)
r.records = []
r.corpus = []
r.tokenized_corpus = []
r.bm25 = None
r.reranker_disabled = True
r.semantic_disabled = False
r._pc = None
r.collection = None
r.cross_encoder = None
r.embed_fn = None
pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
r._pc = pc
r.pinecone_index = pc.Index("hector-legal")

ACT_QUERIES = {
    "Indian Penal Code, 1860": [
        "punishment for murder IPC Section 302",
        "IPC Section 376 rape punishment",
        "theft offences IPC Section 378",
    ],
    "Bharatiya Nyaya Sanhita, 2023": [
        "punishment for murder BNS Section 101",
        "BNS Section 63 sexual assault",
        "dacoity BNS Section 309",
    ],
    "Code of Criminal Procedure, 1973": [
        "bail provisions CrPC Section 437",
        "FIR registration CrPC Section 154",
        "framing of charges CrPC Section 228",
    ],
    "Bharatiya Nagarik Suraksha Sanhita, 2023": [
        "bail provisions BNSS Section 480",
        "FIR registration BNSS Section 173",
        "framing of charges BNSS Section 248",
    ],
    "Indian Evidence Act, 1872": [
        "dying declaration Section 32 Evidence Act",
        "confession to police Section 25 Evidence Act",
        "burden of proof Section 101 Evidence Act",
    ],
    "Bharatiya Sakshya Adhiniyam, 2023": [
        "dying declaration Section 23 BSA",
        "confession to police Section 24 BSA",
        "burden of proof Section 100 BSA",
    ],
    "Code of Civil Procedure, 1908": [
        "res judicata Section 11 CPC",
        "civil suit institution Section 9 CPC",
        "appeal Section 100 CPC",
    ],
    "Indian Contract Act, 1872": [
        "lawful consideration Section 23 Contract Act",
        "breach of contract compensation Section 73",
        "indemnity Section 124 Contract Act",
    ],
    "Transfer of Property Act, 1882": [
        "lis pendens Section 52 Transfer of Property",
        "sale of immovable property Section 54",
        "mortgage Section 58 Transfer of Property",
    ],
    "Negotiable Instruments Act, 1881": [
        "dishonour of cheque Section 138 NI Act",
        "presumptions Section 118 NI Act",
        "promissory note Section 25 NI Act",
    ],
    "Constitution of India": [
        "right to life Article 21 Constitution",
        "equality before law Article 14 Constitution",
        "freedom of speech Article 19 Constitution",
    ],
    "Motor Vehicles Act, 1988": [
        "drunk driving Section 185 Motor Vehicles Act",
        "accident claims Section 134 Motor Vehicles Act",
        "registration Section 39 Motor Vehicles Act",
    ],
    "Hindu Marriage Act, 1955": [
        "divorce grounds Section 13 Hindu Marriage Act",
        "conditions for marriage Section 5 Hindu Marriage Act",
        "restitution of conjugal rights Section 9",
    ],
    "Hindu Succession Act, 1956": [
        "coparcenary Section 6 Hindu Succession Act",
        "women property Section 14 Hindu Succession Act",
        "intestate succession Section 15 Hindu Succession Act",
    ],
    "Dowry Prohibition Act, 1961": [
        "definition of dowry Dowry Prohibition Act",
        "penalty for taking dowry Section 3",
        "penalty for giving dowry Section 4",
    ],
    "Protection of Women from Domestic Violence Act, 2005": [
        "domestic violence definition Section 3 DV Act",
        "protection order Section 12 DV Act",
        "residence order Section 18 DV Act",
    ],
    "Narcotic Drugs and Psychotropic Substances Act, 1985": [
        "cannabis punishment Section 20 NDPS Act",
        "opioids punishment Section 21 NDPS Act",
        "search seizure Section 50 NDPS Act",
    ],
    "Consumer Protection Act, 2019": [
        "consumer definition Section 2 Consumer Protection Act",
        "district commission jurisdiction Section 38",
        "e-commerce Section 69 Consumer Protection Act",
    ],
    "Information Technology Act, 2000": [
        "computer offences Section 66 IT Act",
        "data breach compensation Section 43A",
        "intermediary liability Section 79 IT Act",
    ],
    "Limitation Act, 1963": [
        "suit for possession Article 58 Limitation Act",
        "compensation Article 113 Limitation Act",
        "extension of limitation period Section 5",
    ],
    "Arbitration and Conciliation Act, 1996": [
        "arbitration agreement Section 8 Arbitration Act",
        "setting aside award Section 34 Arbitration Act",
        "interim measures Section 9 Arbitration Act",
    ],
    "Industrial Disputes Act, 1947": [
        "retrenchment Section 25G Industrial Disputes Act",
        "conditions retrenchment Section 25F",
        "standing orders Section 2A Industrial Disputes Act",
    ],
    "Family Courts Act, 1984": [
        "establishment Section 3 Family Courts Act",
        "jurisdiction Section 7 Family Courts Act",
        "procedure Section 10 Family Courts Act",
    ],
    "Competition Act, 2002": [
        "anti-competitive agreements Section 3 Competition Act",
        "dominant position Section 4 Competition Act",
        "combination regulation Section 29 Competition Act",
    ],
    "Juvenile Justice Act, 2015": [
        "child definition Section 2 Juvenile Justice Act",
        "JJ Board procedure Section 10",
        "adoption Section 31 Juvenile Justice Act",
    ],
    "Forest Act, 1927": [
        "forest offences Section 32 Forest Act",
        "power to enter Section 70 Forest Act",
        "forest officer duties Section 4",
    ],
    "Specific Relief Act, 1963": [
        "specific performance Section 14 Specific Relief Act",
        "injunctions Section 26 Specific Relief Act",
        "suits for specific performance Section 10",
    ],
    "Factories Act, 1948": [
        "occupier duties Section 7A Factories Act",
        "welfare officers Section 41A Factories Act",
        "weekly hours Section 44A Factories Act",
    ],
    "Easements Act, 1882": [
        "easement right Section 15 Easements Act",
        "prescription Section 37 Easements Act",
        "disturbance of easement Section 28",
    ],
    "Arms Act, 1959": [
        "licence to possess arms Section 4 Arms Act",
        "prohibition arms Section 7 Arms Act",
        "punishment Section 25 Arms Act",
    ],
    "Copyright Act, 1957": [
        "works copyright Section 13 Copyright Act",
        "fair dealing Section 52 Copyright Act",
        "infringement Section 51 Copyright Act",
    ],
    "Environment Protection Act, 1986": [
        "power to protect environment Section 3 EPA",
        "restrictions Section 5 EPA",
        "penalty Section 15 Environment Protection Act",
    ],
    "Right to Information Act, 2005": [
        "definition of information Section 3 RTI Act",
        "application Section 6 RTI Act",
        "appeal Section 19 RTI Act",
    ],
    "Legal Services Authorities Act, 1987": [
        "legal services Section 3 Legal Services Authorities Act",
        "eligibility Section 12",
        "Lok Adalat Section 19 Legal Services Authorities Act",
    ],
    "Prevention of Corruption Act, 1988": [
        "public servant gratuity Section 7 Prevention of Corruption Act",
        "taking gratification Section 8",
        "criminal misconduct Section 13 Prevention of Corruption Act",
    ],
    "Gram Nyayalayas Act, 2008": [
        "establishment Section 3 Gram Nyayalayas Act",
        "jurisdiction Section 12 Gram Nyayalayas Act",
        "procedures Section 19 Gram Nyayalayas Act",
    ],
    "Trusts Act, 1882": [
        "definition of trust Section 3 Trusts Act",
        "trustee duties Section 74 Trusts Act",
        "trustee compensation Section 88 Trusts Act",
    ],
}

total = sum(len(qs) for qs in ACT_QUERIES.values())
done = 0
passed = 0
failed = 0
results_log = {}

for act, queries in ACT_QUERIES.items():
    act_results = []
    print(f"\n--- {act} ({len(queries)} queries) ---")
    for qi, query in enumerate(queries, 1):
        done += 1
        t0 = time.time()
        results = r._semantic_search(query, top_k=5)
        elapsed = time.time() - t0

        found_acts = set()
        hit = False
        best_score = 0.0
        for m in results:
            meta = m.get("metadata", {})
            doc_act = meta.get("real_act_name") or meta.get("act_name") or ""
            score = m.get("distance", 0)
            if doc_act:
                found_acts.add(doc_act)
            if act.lower() in doc_act.lower():
                hit = True
                best_score = max(best_score, score)

        status = "PASS" if hit else "FAIL"
        if hit:
            passed += 1
        else:
            failed += 1

        print(f"  [{done}/{total}] Q{qi}: {status} | {elapsed:.1f}s | score={best_score:.3f} | {query}")
        if not hit:
            print(f"         Found: {sorted(found_acts)}")

        act_results.append({
            "query": query, "status": status, "time_ms": round(elapsed * 1000, 1),
            "best_score": round(best_score, 4), "found_acts": sorted(found_acts), "hit": hit,
        })
    results_log[act] = act_results

print(f"\n{'='*70}")
print("SUMMARY")
print(f"{'='*70}")
print(f"Total queries: {total}")
print(f"Passed: {passed}")
print(f"Failed: {failed}")
print(f"Pass rate: {passed / total * 100:.1f}%")
print()

for act, act_res in results_log.items():
    ap = sum(1 for r in act_res if r["hit"])
    at = len(act_res)
    s = "OK" if ap == at else "PARTIAL" if ap > 0 else "MISSING"
    print(f"  [{s}] {act}: {ap}/{at}")

json_path = os.path.join(os.path.dirname(__file__), "..", "..", "test_act_coverage_results.json")
json_path = os.path.abspath(json_path)
with open(json_path, "w", encoding="utf-8") as f:
    json.dump({
        "timestamp": datetime.now().isoformat(),
        "total_acts": len(ACT_QUERIES),
        "total_queries": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": round(passed / total * 100, 1),
        "results": results_log,
    }, f, indent=2, ensure_ascii=False)
print(f"\nResults saved to: {json_path}")
print(f"Finished: {datetime.now().isoformat()}")
