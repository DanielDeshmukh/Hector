"""Verify all PDFs in data/Books/ contain real, extractable text."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pypdf import PdfReader

books_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "Books"
)
results = []

for f in sorted(os.listdir(books_dir)):
    if not f.endswith(".pdf"):
        continue
    path = os.path.join(books_dir, f)
    try:
        reader = PdfReader(path)
        pages = len(reader.pages)
        text = ""
        for page in reader.pages[:3]:
            t = page.extract_text() or ""
            text += t
        chars = len(text.strip())
        words = len(text.split())
        lower = text.lower()
        has_section = "section" in lower
        has_act = "act" in lower
        if chars > 200 and has_section:
            quality = "GOOD"
        elif chars > 50:
            quality = "PARTIAL"
        else:
            quality = "BAD"
        results.append((f, pages, chars, words, quality, has_section, has_act))
    except Exception as e:
        results.append((f, 0, 0, 0, "ERROR: " + str(e)[:60], False, False))

hdr = f"{'File':<55} {'Pg':>4} {'Chars':>6} {'Words':>5} {'Quality':>8} {'Sec':>3} {'Act':>3}"
print(hdr)
print("-" * len(hdr))
for name, pages, chars, words, quality, has_sec, has_act in results:
    sec_mark = "Y" if has_sec else "N"
    act_mark = "Y" if has_act else "N"
    print(
        f"{name:<55} {pages:>4} {chars:>6} {words:>5} {quality:>8} {sec_mark:>3} {act_mark:>3}"
    )

bad = [r for r in results if r[4] not in ("GOOD",)]
print(f"\nTotal: {len(results)} files, {len(bad)} problematic")
for r in bad:
    print(f"  ISSUE: {r[0]} -> {r[4]}")
