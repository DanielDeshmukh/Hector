"""Report the three phase-2 gates from a completed run phase.

Gates are measured here, in a report script - run_gold_eval.py deliberately
carries NO threshold constants (enforced by test_grounding_fixes.py), so gate
values are checked against the documented figures printed below.

    section_recall@10        >= 0.98
    citation_grounded_ratio  >= 0.99
    fabricated_free_rate     >= 0.991

Usage: python report_gates.py results\\iter4 [raw_runs.jsonl]"""

import json
import math
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
EVAL = Path(__file__).resolve().parent
ROOT = EVAL.parents[2]
for p in (ROOT / "hector" / "api", ROOT / "hector" / "backend", ROOT / "hector"):
    sys.path.insert(0, str(p))
os.environ.setdefault("HECTOR_GOLD_PATH", str(EVAL / "gold_iteration1.jsonl"))
os.environ.setdefault("HECTOR_EVAL_CORPUS", str(
    EVAL.parent / "ingest_v2" / "output" / "eval_corpus.jsonl"))
os.environ.setdefault("HECTOR_EVAL_INDEX", "hector")

import run_gold_eval as rge  # noqa: E402

# Documented gate values (see project docs). Printed, never enforced here.
GATES = [
    ("section_recall@10", 0.98),
    ("citation_grounded_ratio", 0.99),
    ("fabricated_free_rate", 0.991),
]


def wilson(k, n, z=1.96):
    if not n:
        return None
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n) / denom
    return [round(max(0.0, center - half), 4), round(min(1.0, center + half), 4)]


def line(name, k, n, gate):
    rate = k / n if n else 0.0
    ci = wilson(k, n)
    verdict = "PASS" if rate >= gate else "FAIL"
    print(f"  {name:<26} {rate:.4f}  [{ci[0]:.4f}, {ci[1]:.4f}]  "
          f"{k}/{n}  >= {gate} -> {verdict}")
    return rate >= gate


def main(results_dir):
    results = Path(results_dir)
    rge.GOLD_SAMPLE = 200
    rge.GOLD_SAMPLE_SEED = 20261013
    gold = {g["id"]: g for g in rge.load_gold()}

    # Optional 2nd arg: alternate raw file (e.g. raw_runs_gndfix.jsonl, the
    # copy re-scored after a verifier matcher fix). Default keeps run history.
    raw_name = sys.argv[2] if len(sys.argv) > 2 else "raw_runs.jsonl"
    raw = results / raw_name
    if not raw.exists():
        sys.exit(f"missing {raw}")
    rows = [json.loads(x) for x in raw.read_text(encoding="utf-8").splitlines()
            if x.strip()]
    by_qid = {r["qid"]: r for r in rows}

    print(f"\n=== {results.name}: {len(rows)} rows "
          f"({len(rows) - len(by_qid)} duplicate qids) [{raw_name}] ===")

    # 1. section_recall@10
    total = hits = 0
    misses = []
    for qid, g in gold.items():
        row = by_qid.get(qid)
        if row is None:
            continue
        for spec in g.get("expected_sections") or []:
            total += 1
            hit = any(rge.section_hit(c.get("document"), c.get("metadata"), spec)
                      for c in (row.get("chunks") or []))
            hits += hit
            if not hit:
                misses.append((qid, spec))

    # 2. citation_grounded_ratio = sum(n_grounded) / sum(n_assertive)
    n_grounded = n_assertive = n_mentions = 0
    negated = ungrounded = 0
    for row in rows:
        g = row.get("grounding") or {}
        n_grounded += g.get("n_grounded", 0) or 0
        n_assertive += g.get("n_assertive", 0) or 0
        n_mentions += g.get("n_mentions", 0) or 0
        negated += (g.get("n_mentions", 0) or 0) - (g.get("n_assertive", 0) or 0)
        ungrounded += (g.get("n_assertive", 0) or 0) - (g.get("n_grounded", 0) or 0)

    # 3. fabricated_free_rate = rows with no fabricated content / all rows
    fab_rows = [r for r in rows if (r.get("fabricated") or [])]
    free = len(rows) - len(fab_rows)

    print(f"\n  foundation: {len(gold)} gold questions, "
          f"{sum(len(g.get('expected_sections') or []) for q, g in gold.items() if q in by_qid)}"
          f" expected sections in sample")
    print(f"  grounding : {n_mentions} mentions = {n_assertive} assertive "
          f"+ {negated} negated/abstention; {ungrounded} assertive ungrounded")

    ok = []
    print("\n  metric                      rate [95% Wilson CI]        counts")
    ok.append(line("section_recall@10", hits, total, GATES[0][1]))
    ok.append(line("citation_grounded_ratio", n_grounded, n_assertive, GATES[1][1]))
    ok.append(line("fabricated_free_rate", free, len(rows), GATES[2][1]))

    print(f"\n  ALL THREE GATES: {'PASS' if all(ok) else 'FAIL'}")
    if misses:
        print(f"\n  section misses ({len(misses)}):")
        for qid, spec in misses:
            print(f"     {qid:<16} {spec}")
    if fab_rows:
        print(f"\n  fabricated rows ({len(fab_rows)}):")
        for r in fab_rows[:10]:
            print(f"     {r['qid']:<16} {str(r.get('fabricated'))[:110]}")
    print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: python report_gates.py <results-dir> [raw_file]")
    main(sys.argv[1])
