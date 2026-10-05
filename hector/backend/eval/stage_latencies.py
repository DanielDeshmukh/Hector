"""Per-stage latency breakdown for a completed run.

    python stage_latencies.py results\\iter4

Shows where retrieve/gen time actually goes before anyone optimizes."""

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def pct(v, p):
    v = sorted(v)
    return v[min(int(len(v) * p), len(v) - 1)] if v else 0.0


def main(results_dir):
    rows = [json.loads(x) for x in (Path(results_dir) / "raw_runs.jsonl")
            .read_text(encoding="utf-8").splitlines() if x.strip()]
    print(f"n = {len(rows)}\n")

    keys = set()
    for r in rows:
        keys |= set((r.get("stages") or {}).keys())
        keys |= set(((r.get("stages") or {}).get("timings_ms") or {}).keys())

    print("stages / timings_ms:")
    print(f"{'stage':<34}{'p50':>9}{'p95':>9}{'max':>9}{'n':>6}")
    for k in sorted(keys):
        v = []
        for r in rows:
            s = r.get("stages") or {}
            x = (s.get("timings_ms") or {}).get(k, s.get(k))
            if isinstance(x, (int, float)) and x > 0:
                v.append(x)
        if not v:
            continue
        print(f"{k:<34}{pct(v, .5):>9.0f}{pct(v, .95):>9.0f}{max(v):>9.0f}{len(v):>6}")

    print("\nrow-level (ms):")
    print(f"{'field':<34}{'p50':>9}{'p95':>9}{'max':>9}{'n':>6}")
    for k in ("expand_ms", "retrieve_ms", "verify_ms", "gen_ms", "total_ms"):
        v = [r.get(k) for r in rows]
        v = [x for x in v if isinstance(x, (int, float))]
        if v:
            print(f"{k:<34}{pct(v, .5):>9.0f}{pct(v, .95):>9.0f}{max(v):>9.0f}{len(v):>6}")

    slow = sorted(rows, key=lambda r: -(r.get("retrieve_ms") or 0))[:8]
    print("\nslowest retrieval (timings_ms):")
    for r in slow:
        t = (r.get("stages") or {}).get("timings_ms") or {}
        keep = {k: round(t[k]) for k in ("bm25_ms", "dense_ms", "rerank_ms",
                                         "score_ms", "total_ms") if k in t}
        print(f"  {r['qid']:<15} retrieve={r.get('retrieve_ms'):.0f} {keep}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "results/iter4")
