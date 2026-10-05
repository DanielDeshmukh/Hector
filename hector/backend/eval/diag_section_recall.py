"""Compute section_recall@10 straight from raw_runs.jsonl + the gold file,
so the third gate is known without waiting for the judge phase.

Reuses run_gold_eval's own section_hit/ACT_ALIASES so the number is identical
to what metrics.json will report (no re-implementation drift)."""

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
EVAL = Path(__file__).resolve().parent
sys.path.insert(0, str(EVAL))

import run_gold_eval as rge  # noqa: E402


def gold_map():
    path = EVAL / "gold_iteration1.jsonl"
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rec = json.loads(line)
            out[rec["id"]] = rec
    return out


def recall(raw_path, gold):
    rows = [json.loads(x) for x in
            Path(raw_path).read_text(encoding="utf-8").splitlines() if x.strip()]
    hit = tot = 0
    missing_gold = 0
    for row in rows:
        g = gold.get(row["qid"])
        if g is None:
            missing_gold += 1
            continue
        for spec in g.get("expected_sections") or []:
            tot += 1
            if any(rge.section_hit(c.get("document"), c.get("metadata"), spec)
                   for c in row.get("chunks") or []):
                hit += 1
    return hit, tot, len(rows), missing_gold


def main():
    gold = gold_map()
    print(f"gold entries: {len(gold)}\n")
    for label, raw in [
        ("iter1 baseline (IPC-only index)", EVAL / "results" / "iter1" / "raw_runs.jsonl"),
        ("iter2 baseline 200q", EVAL / "results" / "iter2" / "raw_runs.jsonl"),
        ("iter3 60q (3 fixes + prompt v2)", EVAL / "results" / "iter3_fix60" / "raw_runs.jsonl"),
    ]:
        if not raw.exists():
            print(f"{label}: not found")
            continue
        hit, tot, nrows, miss = recall(raw, gold)
        v = hit / tot if tot else 0.0
        print(f"{label}")
        print(f"   rows={nrows} (no gold match: {miss})")
        print(f"   section_recall@10 = {hit}/{tot} = {v:.4f}  "
              f"[{'PASS' if v >= 0.98 else 'FAIL'}]   (threshold 0.98)")
        print()


if __name__ == "__main__":
    main()
