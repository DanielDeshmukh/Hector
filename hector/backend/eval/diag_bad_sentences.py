"""Dump the FULL sentence behind every ungrounded (BAD) mention, from both
A/B runs, to see whether the model is (a) inventing sections or (b) honestly
saying "not in the retrieved context" - in which case the verifier's negation
detector (_clause_is_abstention) is the thing that failed, which is a matcher
bug the rules allow us to fix."""

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = Path(__file__).resolve().parent / "results"
RUNS = [
    ("ultra-550b", BASE / "iter2" / "raw_runs.jsonl"),
    ("nano-omni", BASE / "iter2_nano_probe" / "raw_runs.jsonl"),
]

for name, path in RUNS:
    if not path.exists():
        continue
    rows = [json.loads(x) for x in
            path.read_text(encoding="utf-8").splitlines() if x.strip()]
    bad = []
    for r in rows:
        g = r.get("grounding") or {}
        for m in g.get("mentions") or []:
            if not m.get("grounded"):
                bad.append((r["qid"], m))
    print("=" * 78)
    print(f"{name}: rows={len(rows)}  ungrounded mentions={len(bad)}")
    negated = sum(1 for _q, m in bad if m.get("negated"))
    print(f"  of which flagged negated=True: {negated}  "
          f"(negated mentions are excluded from the ratio by the metric code)")
    print(f"  assertive-but-ungrounded (what actually lowers the ratio): "
          f"{len(bad) - negated}")
    for qid, m in bad[:10]:
        print("-" * 78)
        print(f"  {qid}  section={m.get('section')}  negated={m.get('negated')}"
              f"  in_sources={m.get('in_sources')}")
        print(f"  sentence: {m.get('sentence')}")
print("=" * 78)
