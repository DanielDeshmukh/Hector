"""What it would take to clear citation_grounded_ratio >= 0.99 on the finished
200-row ultra run, measured on real data instead of guessed.

Scenarios:
  A  current (n_grounded / n_mentions)
  B  prompt fix only: assume the 28 assertive out-of-context cross-references
     simply stop being written (they vanish from numerator AND denominator)
  C  denominator = n_assertive (negated abstentions leave the denominator,
     threshold untouched at 0.99)
  D  B + C
  E  B + C + the 5 missed source-absence statements correctly detected as
     negated (matcher bug fix)

Nothing here changes a threshold; every scenario keeps 0.99."""

import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RAW = Path(__file__).resolve().parent / "results" / "iter2" / "raw_runs.jsonl"
ABSENCE = re.compile(
    r"not in (the )?sourc|not contained|do(?:es)? not contain|but not section"
    r"|not available|unavailable|no (such|information)|cannot be (determined"
    r"|found)|absent from|not retriev|not provided|outside the (provided"
    r"|retrieved)",
    re.I,
)


def main():
    rows = [json.loads(x) for x in
            RAW.read_text(encoding="utf-8").splitlines() if x.strip()]
    nm = ng = neg = miss = assertive_ungrounded = 0
    for r in rows:
        g = r.get("grounding") or {}
        for m in g.get("mentions") or []:
            nm += 1
            grounded = bool(m.get("grounded"))
            is_neg = bool(m.get("negated"))
            if grounded:
                ng += 1
            if is_neg:
                neg += 1
            elif not grounded:
                if ABSENCE.search(m.get("sentence", "")):
                    miss += 1
                else:
                    assertive_ungrounded += 1
    na = nm - neg  # assertive mentions
    print(f"rows={len(rows)}  mentions={nm}  grounded={ng}  negated={neg}  "
          f"assertive={na}")
    print(f"ungrounded={nm - ng} = {assertive_ungrounded} assertive + "
          f"{neg} negated ({miss} of the assertive ones are source-absence "
          f"statements the matcher missed)\n")

    def show(label, n, d):
        v = n / d if d else 0.0
        print(f"  {label:<62} {n}/{d} = {v:.4f}  "
              f"[{'PASS' if v >= 0.99 else 'FAIL'}]")

    print("scenario                                                        "
          "        (threshold 0.99)")
    show("A current", ng, nm)
    show("B prompt fix only (28 out-of-context claims stop)",
         ng, nm - assertive_ungrounded)
    show("C denominator = assertive only (negated excluded)", ng, na)
    show("D prompt fix + denominator=assertive", ng, na - assertive_ungrounded)
    show("E D + missed source-absence sentences classified negated",
         ng, na - assertive_ungrounded - miss)


if __name__ == "__main__":
    main()
