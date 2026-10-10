"""diagnose_misses.py - print top-10 sections for specific gold queries."""
from __future__ import annotations

import hashlib
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
sys.path.insert(0, os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "api")))

CORPUS_PATH = os.path.abspath(
    os.path.join(SCRIPT_DIR, "..", "ingest_v2", "output", "eval_corpus.jsonl"))
os.environ.setdefault("HF_HUB_OFFLINE", "1")
for _line in open(os.path.join(SCRIPT_DIR, "..", "..", "..", ".env"),
                  encoding="utf-8"):
    _line = _line.strip()
    if _line and not _line.startswith("#") and "=" in _line:
        _k, _v = _line.split("=", 1)
        os.environ.setdefault(_k, _v)

from run_gold_eval import read_jsonl, section_hit, TOP_K, CANDIDATE_POOL  # noqa: E402

GOLD = {
    "ipc": os.path.join(SCRIPT_DIR, "gold_set_ipc.jsonl"),
    "bns": os.path.join(SCRIPT_DIR, "gold_bns.jsonl"),
    "bnss": os.path.join(SCRIPT_DIR, "gold_bnss.jsonl"),
}
MISS_IDS = [
    "bns-255-a", "bnss-124-a", "bnss-145-a", "bnss-469-a",
    "ipc-9-a", "ipc-11-a", "ipc-143-a", "ipc-311-a", "ipc-312-a",
]


def main() -> int:
    golds = {}
    for path in GOLD.values():
        for g in read_jsonl(path):
            golds[g["id"]] = g
    records = []
    with open(CORPUS_PATH, encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                r = json.loads(line)
                records.append({
                    "id": r["id"],
                    "document": r["document"],
                    "metadata": r["metadata"],
                })
    by_id = {r["id"]: r for r in records}

    from data.hybrid_retriever import HectorHybridRetriever
    from core.query_expander import QueryExpander

    retriever = HectorHybridRetriever.from_records(records)
    retriever._pinecone_dead = True
    retriever._local_records_loaded = True
    retriever.reranker_disabled = False  # production rerank, like sweep --rerank
    expander = QueryExpander()

    for qid in MISS_IDS:
        g = golds[qid]
        raw = g["question"]
        expanded = expander.expand(raw) or raw
        print(f"=== {qid} expected={g['expected_sections']}")
        print(f"    Q: {raw[:160]}")
        if expanded != raw:
            print(f"    E: {expanded[:220]}")
        for label, q in (("expanded", expanded), ("raw", raw)):
            out = retriever.search(q, top_k=TOP_K,
                                   candidate_pool=CANDIDATE_POOL, raw_query=raw)
            stage = retriever.last_stage_info or {}
            scored = (stage.get("stages") or {}).get("scored") or []
            in_pool = [i for i in scored
                       if section_hit(by_id[i]["document"],
                                      by_id[i]["metadata"],
                                      g["expected_sections"][0])]
            in_top = [i + 1 for i, c in enumerate(out)
                      if section_hit(c.get("document"), c.get("metadata") or {},
                                     g["expected_sections"][0])]
            print(f"    [{label:<8}] pool={len(scored)} in_pool={bool(in_pool)}"
                  f" top10_hit_at={in_top}")
            if not in_top and label == "raw":
                for i, c in enumerate(out):
                    md = c.get("metadata") or {}
                    sc = c.get("score")
                    sc = f"{sc:.4f}" if isinstance(sc, float) else str(sc)
                    print(f"       {i + 1:>2}. "
                          f"{md.get('section_number', '?')!s:<8} score={sc} "
                          f"{(md.get('title') or '')[:50]!r}")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
