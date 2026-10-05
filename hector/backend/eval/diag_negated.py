"""Print the negated mentions that drag citation_grounded_ratio down.

grounding_report() sets grounded = (not negated) and in_sources, so every
mention inside a clause classified as an abstention scores 0 no matter what.
This splits those 49 into:
  neg+in_sources  - clause says "not present" while the section IS present
  neg+absent      - clause says "not present" and it is absent (honest)
"""

import collections
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, r"D:\Vs Code\VS code\Hector\hector\api")

from core.verifier import (  # noqa: E402
    _clause_is_abstention,
    _clause_spans,
    _sentence_spans,
    normalize_spaces,
    section_present_in_text,
)

RAW = r"D:\Vs Code\VS code\Hector\hector\backend\eval\results\iter1\raw_runs.jsonl"
MENTION = re.compile(r"(?:section|\u00a7)\s*[:.\-]?\s*(\d+[a-z]?)", re.IGNORECASE)

rows = [json.loads(l) for l in open(RAW, encoding="utf-8")]
c = collections.Counter()
shown = 0

for row in rows:
    answer = row.get("answer") or ""
    src = normalize_spaces(" ".join(c.get("document", "") for c in row.get("chunks") or []))
    if not answer:
        continue
    for _s1, _s2, sentence in _sentence_spans(normalize_spaces(answer)):
        for _c1, _c2, clause in _clause_spans(sentence):
            if not _clause_is_abstention(clause, sentence):
                continue
            for m in MENTION.finditer(clause):
                sec = m.group(1).lower()
                present = section_present_in_text(sec, src)
                c["negated_in_sources" if present else "negated_absent"] += 1
                if shown < 14:
                    shown += 1
                    flag = "PRESENT" if present else "absent "
                    print(f"[{flag}] {row['qid']:<16} sec={sec:<6} {sentence.strip()[:150]}")

print()
print(json.dumps(c, indent=2))
