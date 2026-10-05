"""Inspect index keys vs records for the missing (BNS, N) lookups."""
import os
import sys
from pathlib import Path

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

os.environ["HECTOR_EVAL_CORPUS"] = str(
    Path(SCRIPT_DIR).parent / "ingest_v2" / "output" / "eval_corpus.jsonl"
)
os.environ["HECTOR_EVAL_INDEX"] = "hector"

import run_gold_eval as hg  # noqa: E402

stack = hg.build_stack()
r = stack["retriever"]
index = r._get_section_index()

acts = {}
for act, sec in index:
    acts[act] = acts.get(act, 0) + 1
print("index act distribution:", acts)

bns_keys = sorted(sec for act, sec in index if act == "BNS")[:25]
print("sample BNS keys:", bns_keys)

# What do the BNS 193 / BNS 10 records look like?
for want in ("193", "10", "112"):
    hits = [
        rec for rec in r.records
        if str((rec.get("metadata") or {}).get("section_number", "")).strip()
        == want
    ]
    print(f"\nrecords with section_number={want!r}: {len(hits)}")
    for rec in hits[:4]:
        meta = rec.get("metadata") or {}
        print("   id=", rec["id"][:40], "act=", repr(rec.get("act")),
              "meta.act_name=", repr(meta.get("act_name")),
              "meta.real_act_name=", repr(meta.get("real_act_name")),
              "src=", repr(meta.get("source"))[:40],
              "doc[:60]=", rec["document"][:60].replace("\n", " "))

# total records lacking section_number
missing = sum(
    1 for rec in r.records
    if not str((rec.get("metadata") or {}).get("section_number") or "").strip()
)
print("\nrecords WITHOUT section_number metadata:", missing, "/", len(r.records))
