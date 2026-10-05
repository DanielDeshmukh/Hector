"""What are the 61 ungrounded assertive mentions in iter4?

For every mention the verifier marked (not negated) and (not in_sources), print
the sentence, the section it cites, and whether that section's text is among
the retrieved chunks at all - which separates:

  A. section text WAS retrieved, verifier failed to match   -> matcher bug
  B. section text was NOT retrieved, generator cited anyway -> prompt rule
  C. negation/abstention misclassified                       -> verifier bug"""

import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
EVAL = Path(__file__).resolve().parent
ROOT = EVAL.parents[2]
for p in (ROOT / "hector" / "api", ROOT / "hector" / "backend", ROOT / "hector"):
    sys.path.insert(0, str(p))
import os  # noqa: E402
os.environ.setdefault("HECTOR_GOLD_PATH", str(EVAL / "gold_iteration1.jsonl"))

import run_gold_eval as rge  # noqa: E402


def main(results_dir):
    rows = [json.loads(x) for x in
            (Path(results_dir) / "raw_runs.jsonl")
            .read_text(encoding="utf-8").splitlines() if x.strip()]

    buckets = Counter()
    lines = []
    per_qid = Counter()
    for row in rows:
        g = row.get("grounding") or {}
        retrieved = set()
        for c in (row.get("chunks") or []):
            md = c.get("metadata") or {}
            sn = str(md.get("section_number") or "").strip().lower()
            if sn:
                retrieved.add(sn)
        for m in g.get("mentions") or []:
            if m.get("negated") or m.get("grounded"):
                continue
            sec = str(m.get("section") or "").strip().lower()
            present = sec in retrieved
            kind = "B_retrieved_but_no_match" if present else "C_not_retrieved"
            buckets[kind] += 1
            per_qid[row["qid"]] += 1
            if len(lines) < 40:
                lines.append(
                    f"  {kind}  {row['qid']:<16} sec={sec:<8} "
                    f"retrieved_secs={sorted(retrieved)[:6]}\n"
                    f"        {str(m.get('sentence'))[:190]}"
                )

    print(f"=== ungrounded assertive mentions: {sum(buckets.values())} ===")
    for k, v in buckets.most_common():
        print(f"  {k:<28} {v}")
    print(f"\n  questions affected: {len(per_qid)} of {len(rows)}")
    for qid, n in per_qid.most_common(15):
        print(f"     {qid:<16} {n}")
    print("\n=== samples ===")
    for s in lines[:24]:
        print(s)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "results/iter4")
