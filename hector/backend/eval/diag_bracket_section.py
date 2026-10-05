"""How is the bracketed [§...] form actually used in the answers?

Decides whether bracketed forms can be treated as source footnotes:

  counts [§X] by shape (pure integer vs letters) and shows surrounding text,
  so the rule is set from evidence rather than guessed."""

import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BRACKET = re.compile(r"\[§([^\]]{1,8})\]")
PURE_INT = re.compile(r"^\d+$")


def main(results_dir):
    rows = [json.loads(x) for x in
            (Path(results_dir) / "raw_runs.jsonl")
            .read_text(encoding="utf-8").splitlines() if x.strip()]
    shapes = Counter()
    ctx_pure = []
    ctx_alnum = []
    for row in rows:
        ans = str(row.get("answer") or "")
        for m in BRACKET.finditer(ans):
            token = m.group(1).strip()
            if PURE_INT.match(token):
                shapes["pure_integer"] += 1
                if len(ctx_pure) < 8:
                    ctx_pure.append((row["qid"], ans[max(0, m.start() - 70):
                                                     m.end() + 40]))
            else:
                shapes[f"has_letter:{token[:4]}"] += 1
                if len(ctx_alnum) < 8:
                    ctx_alnum.append((row["qid"], ans[max(0, m.start() - 70):
                                                      m.end() + 40]))

    print("=== [§X] shapes ===")
    for k, v in shapes.most_common():
        print(f"  {k:<24} {v}")

    print("\n=== pure-integer examples (footnote candidates) ===")
    for qid, c in ctx_pure:
        print(f"  {qid:<15} ...{c}...".replace("\n", " "))

    print("\n=== lettered examples (would be real citations) ===")
    for qid, c in ctx_alnum:
        print(f"  {qid:<15} ...{c}...".replace("\n", " "))

    # do real citations ever appear UNbracketed as bare §N?
    bare = Counter()
    for row in rows:
        ans = str(row.get("answer") or "")
        for m in re.finditer(r"(?<!\[)§\s*(\d+[a-z]?)", ans):
            bare[m.group(1).lower()] += 1
    print(f"\n=== bare '§ N' citations outside brackets: "
          f"{sum(bare.values())} total ===")
    for k, v in bare.most_common(12):
        print(f"  §{k:<8} {v}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "results/iter4")
