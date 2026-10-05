#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""dump BNS body lines that look like section heads, to see the real format."""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import v2_common as V  # noqa: E402
import v2_scanner as S  # noqa: E402

BOOKS_DIR = V.INGEST.parent.parent / "api" / "data" / "Books"
TARGETS = [
    ("BNS", "Bharatiya Nyaya Sanhita-2023.pdf", 8),
    ("BNSS", "Bharatiya Nagarik Suraksha Sanhita-2023.pdf", 170),
    ("BSA", "Bharatiya Sakshya Adhiniyam-2023.pdf", 0),
]

NUM_LINE = re.compile(r"^\s*(\d{1,4}[A-Za-z]{0,2})[.)]?\s+\S")

for label, fn, start in TARGETS:
    path = BOOKS_DIR / fn
    print("=" * 76)
    print(f"{label}  {fn}  start_page={start}")
    doc = V.fitz.open(str(path))
    hits = []
    for pi in range(start, len(doc)):
        _, ls = V.page_lines(doc[pi])
        for l in ls:
            t = l["text"].strip()
            m = NUM_LINE.match(t)
            if m:
                hits.append((pi + 1, t))
    doc.close()
    print(f"  leading-number lines: {len(hits)}")
    print("  --- first 14 ---")
    for p, t in hits[:14]:
        print(f"    p{p:>3} | {t[:110]}")
    print("  --- sample mid ---")
    for p, t in hits[len(hits) // 2:len(hits) // 2 + 6]:
        print(f"    p{p:>3} | {t[:110]}")

    # which of the IPC forms does this satisfy?
    forms = {"NUMHEAD(sole num line)": 0, "NUMDOT(num. text)": 0,
             "RESTATED(num. )": 0, "QUOTE_NUM(num quote)": 0,
             "PAREN(num) text)": 0, "NUM_PAREN(num)": 0, "none": 0}
    for p, t in hits:
        if S.NUMHEAD_RE.match(t):
            forms["NUMHEAD(sole num line)"] += 1
        elif S.NUMDOT_RE.match(t):
            forms["NUMDOT(num. text)"] += 1
        elif S.RESTATED_RE.match(t):
            forms["RESTATED(num. )"] += 1
        elif S.QUOTE_NUM_RE.match(t):
            forms["QUOTE_NUM(num quote)"] += 1
        elif re.match(r"^\s*\d{1,4}[A-Za-z]{0,2}\s*\)", t):
            forms["PAREN(num) text)"] += 1
        elif re.match(r"^\s*\(\d{1,4}[A-Za-z]{0,2}\)", t):
            forms["NUM_PAREN(num)"] += 1
        else:
            forms["none"] += 1
    print(f"  form breakdown: {forms}")
