"""Diagnose citation_grounded_ratio failures on iter1.

For every mention the harness counted as UNGROUNDED, classify the cause:
  A source-present  - the section number IS in the retrieved text, but the
                      strict matcher (needs literal "section N" / "N." at
                      line start) missed it  -> matcher limitation
  B absent          - the section number appears nowhere in the retrieved
                      text -> genuine retrieval / model-citation failure
  C negated         - clause read as an abstention/negation by the harness
Counts are reported per cause so the 0.907 gate miss can be attributed.
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
print(f"rows={len(rows)}")

tot = collections.Counter()
loose = collections.Counter()
examples = collections.defaultdict(list)

for row in rows:
    answer = row.get("answer") or ""
    src = " ".join(c.get("document", "") for c in row.get("chunks") or [])
    if not answer:
        continue
    src_norm = normalize_spaces(src)
    src_loose = src_norm.lower()
    for _s1, _s2, sentence in _sentence_spans(normalize_spaces(answer)):
        for _c1, _c2, clause in _clause_spans(sentence):
            negated = _clause_is_abstention(clause, sentence)
            for m in MENTION.finditer(clause):
                sec = m.group(1).lower()
                strict = section_present_in_text(sec, src_norm)
                grounded = (not negated) and strict
                tot["mentions"] += 1
                if grounded:
                    tot["grounded"] += 1
                    continue
                if negated:
                    tot["negated"] += 1
                    continue
                # ungrounded, assertive: is the number simply in the text?
                token = re.search(
                    rf"(?:section\s*[:.\-]?\s*|§\s*){re.escape(sec)}\b", src_loose
                ) or re.search(rf"(?:^|[\s(]){re.escape(sec)}\.\s", src_loose)
                if token:
                    tot["A_source_present_matcher_missed"] += 1
                    if len(examples["A"]) < 12:
                        examples["A"].append((row["qid"], sec, sentence[:120]))
                elif re.search(rf"\b{re.escape(sec)}\b", src_loose):
                    tot["B_number_only_no_section"] += 1
                    if len(examples["B"]) < 12:
                        examples["B"].append((row["qid"], sec, sentence[:120]))
                else:
                    tot["C_absent_from_retrieved"] += 1
                    if len(examples["C"]) < 12:
                        examples["C"].append((row["qid"], sec, sentence[:120]))

print(json.dumps(tot, indent=2))
n = tot["mentions"] or 1
print(f"\nreproduced grounded ratio = {tot['grounded'] / n:.4f} "
      f"(n_mentions={tot['mentions']})")
print("\nfailed-mention breakdown (assertive only):")
for k in ("A_source_present_matcher_missed", "B_number_only_no_section",
          "C_absent_from_retrieved", "negated"):
    print(f"  {k:32} {tot[k]}")
for k in ("A", "B", "C"):
    if examples[k]:
        print(f"\nexamples [{k}]:")
        for qid, sec, sent in examples[k][:5]:
            print(f"  {qid} sec={sec} | {sent}")
