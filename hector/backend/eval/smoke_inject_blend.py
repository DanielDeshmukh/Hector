"""One-off smoke: injection + blend behave as designed (no API, no Pinecone)."""
import sys

sys.path.insert(0, r"D:\Vs Code\VS code\Hector\hector\api")
import data.hybrid_retriever as hr

records = [
    {"id": "ipc-103",
     "document": "Section 103 IPC. The right of private defence of property extends to causing death.",
     "metadata": {"source": "IPC.pdf", "page": 1, "section_number": "103"}},
    {"id": "bns-112",
     "document": "112. Zorawar property defence clause applies to theft.",
     "metadata": {"source": "BNS.pdf", "page": 1, "section_number": "112"}},
    {"id": "bns-302",
     "document": "Section 302 BNS. Deliberate act done to outrage religious feelings of any class.",
     "metadata": {"source": "BNS.pdf", "page": 9, "section_number": "302"}},
    {"id": "ipc-302",
     "document": "Section 302 IPC. Punishment for murder.",
     "metadata": {"source": "IPC.pdf", "page": 50, "section_number": "302"}},
    {"id": "iea-9",
     "document": "Section 9 IEA. Cases in which order of court relates to explanation of particulars.",
     "metadata": {"source": "IEA.pdf", "page": 3, "section_number": "9"}},
    {"id": "bnss-154",
     "document": "Section 154 BNSS. Information to police cognizable offence.",
     "metadata": {"source": "BNSS.pdf", "page": 7, "section_number": "154"}},
]

q = ("Which section of the Bharatiya Nyaya Sanhita, 2023 corresponds to "
     "Section 103 of the Indian Penal Code?")

# 1) reranker disabled (fallback path); pool=2 forces injection (bm25/dense
#    cannot fit both the cited section and its counterpart).
r = hr.HectorHybridRetriever.from_records(records)
res = r.search(q, top_k=3, candidate_pool=2)
print("--- disabled path (fallback reranker, pool=2) ---")
for i, x in enumerate(res, 1):
    print("  %d %-12s score=%.3f reasons=%s"
          % (i, x["id"], x["score"], x["reasons"][:2]))
print("  injected:", (r.last_stage_info.get("detail") or {}).get("injected"))


# 2) provider path with a saturated fake reranker that DEMOTES the citations
class FakeProvider:
    def rerank(self, query, candidates):
        for d in candidates:
            d["reranker_score"] = 0.997
            if d["id"] in ("ipc-103", "bns-112"):
                d["reranker_score"] = 0.85
            d["score"] = d["reranker_score"]
            d["similarity_score"] = d["reranker_score"]
        candidates.sort(key=lambda d: d["reranker_score"], reverse=True)
        return candidates


r2 = hr.HectorHybridRetriever.from_records(records)
r2.reranker_disabled = False
r2._reranker_cached = FakeProvider()
res2 = r2.search(q, top_k=3, candidate_pool=2)
print("--- provider path + blend (alpha=0.5, pool=2) ---")
for i, x in enumerate(res2, 1):
    print("  %d %-12s score=%.3f rer=%s pre=%s reasons=%s"
          % (i, x["id"], x["score"], x.get("reranker_score"),
             x.get("pre_rerank_score"), x["reasons"][:1]))
print("  injected:", (r2.last_stage_info.get("detail") or {}).get("injected"))
