"""What act code do records carry vs what the query resolves to?

If record["act"] != legal_query["acts"], the existing act-match boost in
_legal_boost never fires on this corpus, and any act-aware floor built on
the same comparison would silently do nothing."""

import json
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
EVAL = Path(__file__).resolve().parent
ROOT = EVAL.parents[2]
for p in (ROOT / "hector" / "api", ROOT / "hector" / "backend", ROOT / "hector"):
    sys.path.insert(0, str(p))
for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
    s = line.strip()
    if s and not s.startswith("#") and "=" in s:
        k, _, v = s.partition("=")
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
os.environ["HECTOR_EVAL_CORPUS"] = str(
    EVAL.parent / "ingest_v2" / "output" / "eval_corpus.jsonl")
os.environ["HECTOR_EVAL_INDEX"] = "hector"

import run_gold_eval as rge  # noqa: E402


def main():
    stack = rge.build_stack()
    ret = stack["retriever"]
    dist = {}
    for r in ret.records:
        dist[r.get("act")] = dist.get(r.get("act"), 0) + 1
    print("record['act'] distribution:", json.dumps(dist, ensure_ascii=False))

    for q in ["What does Section 275 of the Indian Penal Code provide?",
              "What treatment does the Indian Penal Code provide for murder?",
              "Under the Bharatiya Nyaya Sanhita, what is the law on theft?"]:
        lq = ret._parse_query(q)
        print(f"query acts={lq['acts']!r}  query_sections={lq['section_numbers']}"
              f"  <- {q[:58]!r}")

    # does the boost actually fire?
    rec = next(r for r in ret.records if "275" in str((r.get("citation") or {}).get("section")))
    lq = ret._parse_query("What does Section 275 of the Indian Penal Code provide?")
    print("\nsample record act:", repr(rec.get("act")),
          "citation:", rec.get("citation"))
    print("act-match boost fires:",
          bool(lq["acts"] and rec.get("act") in lq["acts"]),
          "| reasons sample:", rec.get("reasons"))


if __name__ == "__main__":
    main()
