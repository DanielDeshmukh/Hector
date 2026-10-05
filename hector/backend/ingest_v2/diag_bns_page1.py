"""Print page 1 (0-based 0) and the first Contents pages of the BNS-family
PDFs, so act_registry.yaml can carry the exact official title that step6 G1
verifies. IPC's G1 already FAILs on page-1 title, so do not guess."""

import os
import sys

import fitz

BOOKS = r"D:\Vs Code\VS code\Hector\hector\api\data\Books"
FILES = [
    "Bharatiya Nyaya Sanhita-2023.pdf",
    "Bharatiya Nagarik Suraksha Sanhita-2023.pdf",
    "Bharatiya Sakshya Adhiniyam-2023.pdf",
]

for name in FILES:
    path = os.path.join(BOOKS, name)
    doc = fitz.open(path)
    print("=" * 78)
    print(f"{name}  pages={doc.page_count}")
    for pno in (0, 1, 2):
        if pno >= doc.page_count:
            break
        txt = doc[pno].get_text() or ""
        print(f"--- page {pno + 1} (0-based {pno}) first 500 chars ---")
        print(txt[:500].replace("\n\n", "\n"))
    doc.close()
    sys.stdout.flush()
