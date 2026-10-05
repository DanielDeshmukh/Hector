"""Pre-flight: can every row of the combined IPC+BNS corpus be scored by the
eval's section_hit()? It needs (a) the act alias somewhere in document or
act_name metadata, and (b) a 'section <n>' form in document. Counts only -
no hardcoding of expected values."""

import json
import re
import sys

sys.path.insert(0, r"..\eval")
import run_gold_eval as E  # noqa: E402

rows = [json.loads(l) for l in open("output/eval_corpus.jsonl", encoding="utf-8")
        if l.strip()]
by = {}
for r in rows:
    a = "IPC" if r["id"].startswith("ipc") else "BNS"
    by.setdefault(a, []).append(r)

for act, rs in sorted(by.items()):
    aliases = E.ACT_ALIASES[act]
    alias_ok = 0
    sec_ok = 0
    both = 0
    for r in rs:
        hay = (r["document"] + " " + str(r["metadata"].get("act_name") or "")
               ).lower()
        a_hit = any(x in hay for x in aliases)
        s_hit = bool(re.search(r"section\s+\d+", r["document"], re.I))
        alias_ok += a_hit
        sec_ok += s_hit
        both += (a_hit and s_hit)
    print(f"{act}: rows={len(rs)} alias_in_haystack={alias_ok} "
          f"section_n_in_document={sec_ok} both={both}")
    if both != len(rs):
        bad = [r["id"] for r in rs
               if not (any(x in ((r['document'] + ' ' +
                                  str(r['metadata'].get('act_name') or '')).lower())
                            for x in aliases)
                       and re.search(r"section\s+\d+", r["document"], re.I))][:5]
        print(f"  unscoreable sample: {bad}")
