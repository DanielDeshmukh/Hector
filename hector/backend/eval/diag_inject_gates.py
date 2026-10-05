"""Why did injection fire for cmpr-193-179 but not (apparently) cmpf-50-10?"""
import os
import sys
from pathlib import Path

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

os.environ.setdefault(
    "HECTOR_GOLD_PATH",
    os.path.join(SCRIPT_DIR, "gold_compare_iteration1.jsonl"),
)
os.environ["HECTOR_EVAL_CORPUS"] = str(
    Path(SCRIPT_DIR).parent / "ingest_v2" / "output" / "eval_corpus.jsonl"
)
os.environ["HECTOR_EVAL_INDEX"] = "hector"

import run_gold_eval as hg  # noqa: E402

stack = hg.build_stack()
retriever = stack["retriever"]
gold = {g["id"]: g for g in hg.load_gold()}

index = retriever._get_section_index()
print("index size:", len(index))
for probe in [("IPC", "179"), ("BNS", "10"), ("IPC", "50"), ("BNS", "193")]:
    print("  lookup", probe, "->", len(index.get(probe, [])), "records")

for qid in ("cmpr-193-179", "cmpf-50-10", "cmpf-123-136"):
    g = gold[qid]
    pq = retriever._parse_query(g["question"])
    cited = retriever._cited_act_sections(g["question"], pq)
    rows = retriever._citation_injection_rows(g["question"], pq)
    print("\n", qid)
    print("   question:", g["question"][:110])
    print("   parsed acts:", pq["acts"], "sections:", pq["section_numbers"])
    print("   cited:", cited)
    for row in rows:
        print("   -> inject", row["id"], row["reasons"][0],
              "pre=", row["hybrid_score"])
    if not rows:
        print("   !! NO ROWS")
        # step through the gates
        fwd, rev = hg.__dict__.get("_x", None) or (None, None)
        from data.hybrid_retriever import _load_ipc_bns_crosswalk
        fwd, rev = _load_ipc_bns_crosswalk()
        for num, acts in cited:
            print("      cited", num, acts,
                  "fwd=", fwd.get(num), "rev=", rev.get(num))
            for act in acts:
                print("      index[%s, %s] ->" % (act, num),
                      len(index.get((act, num), [])))
