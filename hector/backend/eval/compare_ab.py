"""A/B: nano-omni-30b probe (40q) vs the in-flight ultra-550b run.

Reports the numbers that decide the swap:
  - citation_grounded_ratio (THE gate, >=0.99) = sum(n_grounded)/sum(n_mentions)
  - latency (gen_ms / total_ms), since the 2-5s retrieval budget is separate
    but end-to-end iteration time is what a model swap actually buys
  - fabricated-free rate (gate >=0.991)

Deliberately recomputes from raw_runs.jsonl rather than trusting metrics.json,
because the run-phase `claims_total/claims_supported` fields are a DIFFERENT
metric (claim_support) and summing those yields ~0.83 - a trap that makes a
passing model look failing."""

import json
import statistics as st
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = Path(__file__).resolve().parent / "results"
TARGETS = [
    ("nano-omni-30b (probe, 40q)", BASE / "iter2_nano_probe" / "raw_runs.jsonl"),
    ("ultra-550b (main run)", BASE / "iter2" / "raw_runs.jsonl"),
]


def load(path):
    if not path.exists():
        return []
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines()
            if x.strip()]


def pct(v, p):
    if not v:
        return 0.0
    s = sorted(v)
    i = min(len(s) - 1, int(round((p / 100) * (len(s) - 1))))
    return s[i]


def report(name, rows):
    if not rows:
        print(f"{name}: no rows yet")
        return
    nm = sum((r.get("grounding") or {}).get("n_mentions") or 0 for r in rows)
    ng = sum((r.get("grounding") or {}).get("n_grounded") or 0 for r in rows)
    ct = sum(r.get("claims_total") or 0 for r in rows)
    cs = sum(r.get("claims_supported") or 0 for r in rows)
    fab = sum(1 for r in rows if r.get("fabricated"))
    gen = [r["gen_ms"] for r in rows if isinstance(r.get("gen_ms"), (int, float))]
    tot = [r["total_ms"] for r in rows if isinstance(r.get("total_ms"), (int, float))]
    ret = [r["retrieve_ms"] for r in rows
           if isinstance(r.get("retrieve_ms"), (int, float))]
    errs = sum(1 for r in rows if r.get("gen_error"))
    ratio = ng / nm if nm else 0.0
    gate = "PASS" if ratio >= 0.99 else "FAIL"
    print("=" * 74)
    print(f"{name}   rows={len(rows)}   gen_errors={errs}")
    print(f"  GATE citation_grounded_ratio = {ng}/{nm} = {ratio:.4f}  [{gate}]"
          f"   (threshold 0.99)")
    print(f"  other claim_support metric   = {cs}/{ct} = "
          f"{cs / ct if ct else 0:.4f}  <- not a gate, do not quote")
    print(f"  GATE fabricated_free_rate    = {len(rows) - fab}/{len(rows)} = "
          f"{(len(rows) - fab) / len(rows):.4f}   (threshold 0.991)")
    if gen:
        print(f"  gen   p50={pct(gen, 50):.0f}ms  mean={st.mean(gen):.0f}ms  "
              f"p95={pct(gen, 95):.0f}ms  max={max(gen):.0f}ms")
    if ret:
        print(f"  retr  p50={pct(ret, 50):.0f}ms  mean={st.mean(ret):.0f}ms")
    if tot:
        print(f"  total p50={pct(tot, 50):.0f}ms  mean={st.mean(tot):.0f}ms  "
              f"-> 200q would take ~{st.mean(tot) * 200 / 60:.0f} min")


for name, path in TARGETS:
    report(name, load(path))
print("=" * 74)
