"""Split the 61 ungrounded mentions into fix classes.

  footnote    sentence contains the exact bracketed marker [§N] -> source index
              misread as a statute section (verifier matcher bug)
  abstention  sentence says the text is not in the sources but the negation
              markers did not catch the phrasing (verifier marker gap)
  genuine     assertive citation of a section that was never retrieved
              (generator ignoring the SECTION-NUMBER RULE)"""

import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
EVAL = Path(__file__).resolve().parent
ROOT = EVAL.parents[2]
for p in (ROOT / "hector" / "api", ROOT / "hector" / "backend", ROOT / "hector"):
    sys.path.insert(0, str(p))

from core import verifier  # noqa: E402

ABSTAIN = re.compile(
    r"not in (?:the )?(?:retrieved )?sources|not among (?:the )?(?:retrieved )?"
    r"sources|no source|absent from (?:the )?(?:retrieved )?sources|"
    r"cannot be (?:verified|confirmed)|not (?:shown|stated|provided) in "
    r"(?:the )?(?:retrieved )?sources|not retrieved",
    re.IGNORECASE,
)
FOOTNOTE = None  # built per mention


def main(results_dir):
    global FOOTNOTE
    rows = [json.loads(x) for x in
            (Path(results_dir) / "raw_runs.jsonl")
            .read_text(encoding="utf-8").splitlines() if x.strip()]
    classes = Counter()
    examples = {k: [] for k in ("footnote", "abstention", "genuine")}
    for row in rows:
        for m in (row.get("grounding") or {}).get("mentions") or []:
            if m.get("negated") or m.get("grounded"):
                continue
            sec = str(m.get("section") or "").strip().lower()
            sent = str(m.get("sentence") or "")
            if re.search(r"\[§\s*" + re.escape(sec) + r"\]", sent, re.IGNORECASE):
                kind = "footnote"
            elif ABSTAIN.search(sent):
                kind = "abstention"
            else:
                kind = "genuine"
            classes[kind] += 1
            if len(examples[kind]) < 6:
                examples[kind].append(
                    f"   {row['qid']:<15} sec={sec:<7} {sent[:170]}"
                )

    total = sum(classes.values())
    print(f"=== {total} ungrounded assertive mentions, by fix class ===")
    for k, v in classes.most_common():
        pct = 100.0 * v / total if total else 0
        print(f"  {k:<12} {v:>3}  ({pct:4.1f}%)")
    for k, v in examples.items():
        if v:
            print(f"\n--- {k} ---")
            for e in v:
                print(e)

    # how many rows would clear if footnote+abstention were fixed?
    print("\n=== impact ===")
    print(f"  fixing footnote + abstention leaves "
          f"{classes['genuine']} mentions ungrounded")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "results/iter4")
