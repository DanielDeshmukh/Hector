"""Debug the same-act floor decision for the two misses it did not recover.

Prints, for one query: legal_query acts, the act tag of each item in the
post-rerank window, which branch of _apply_same_act_floor was taken, and the
final position of the expected section."""

import json
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
EVAL = Path(__file__).resolve().parent
ROOT = EVAL.parents[2]
for p in (ROOT / "hector" / "api", ROOT / "hector" / "backend", ROOT / "hector"):
    sys.path.insert(0, str(p))
for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
    s = line.strip()
    if s and not s.startswith("#") and "=" in s:
        k, _, v = s.partition("=")
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
os.environ["HECTOR_EVAL_CORPUS"] = str(
    EVAL.parent / "ingest_v2" / "output" / "eval_corpus.jsonl")
os.environ["HECTOR_EVAL_INDEX"] = "hector"

import run_gold_eval as rge  # noqa: E402
from data.hybrid_retriever import SAME_ACT_FLOOR_RATIO  # noqa: E402

TARGET = "IPC 300"
Q = "What treatment does the Indian Penal Code provide for murder?"


def main():
    import data.hybrid_retriever as hr
    print("floor method present:",
          hasattr(hr.HybridRetriever, "_apply_same_act_floor")
          if hasattr(hr, "HybridRetriever") else "class name differs")
    print("module file:", hr.__file__)
    print("ratio:", SAME_ACT_FLOOR_RATIO)

    stack = rge.build_stack()
    ret, expander = stack["retriever"], stack["expander"]
    print("retriever class:", type(ret).__module__, type(ret).__name__)
    print("has floor:", hasattr(ret, "_apply_same_act_floor"))

    q = expander.expand(Q)
    lq = ret._parse_query(q)
    print("legal_query acts:", lq["acts"], "| sections:", lq["section_numbers"])

    results = ret.search(q, top_k=rge.TOP_K, candidate_pool=rge.CANDIDATE_POOL)
    st = ((getattr(ret, "last_stage_info", None) or {}).get("stages") or {})
    print("TOP_K:", rge.TOP_K)
    print("window (final) acts:")
    for i, cid in enumerate(st.get("final", [])[:12]):
        rec = next((r for r in ret.records if r["id"] == cid), None)
        act = (rec or {}).get("act")
        print(f"   {i + 1:>2} {cid:<20} act={act!r}")
    print("returned results[0..4] act:",
          [r.get("act") for r in results[:5]])
    print("returned ids:", [r["id"] for r in results[:10]])


if __name__ == "__main__":
    main()
