"""Inspect the tail of BNSS's ARRANGEMENT OF SECTIONS (pages 15-19, 1-based)
to decide whether expected_count=498 is a ToC-parsing cut-off or the source
PDF genuinely lists only 498 sections."""

import os
import sys

import pymupdf

SRC = r"D:\Vs Code\VS code\Hector\hector\backend\ingest_v2\sources\bnss-2023.pdf"
PAGES_1BASED = [15, 16, 17, 18, 19]

doc = pymupdf.open(SRC)
print(f"pages={doc.page_count}", flush=True)
for p in PAGES_1BASED:
    if p > doc.page_count:
        break
    txt = doc[p - 1].get_text() or ""
    print("=" * 70, flush=True)
    print(f"--- page {p} ({len(txt)} chars) ---", flush=True)
    print(txt[:900], flush=True)
    print(f"... tail: {txt[-300:]!r}", flush=True)
doc.close()
