#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""sweep start_page to separate 'regex does not match' from 'wrong ToC start'.

If some start_page yields a clean 1..N run at density ~1.0, the IPC regex is
fine and only the front-matter detection needs work.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import v2_common as V  # noqa: E402
import v2_scanner as S  # noqa: E402

BOOKS_DIR = V.INGEST.parent.parent / "api" / "data" / "Books"
TARGETS = [
    ("BNSS", "Bharatiya Nagarik Suraksha Sanhita-2023.pdf", range(0, 46)),
]

for label, fn, pages in TARGETS:
    path = BOOKS_DIR / fn
    print("=" * 78)
    print(f"{label}: {fn}")
    print(f"  {'start':>5} {'markers':>8} {'span':>12} {'density':>8} "
          f"{'viol':>5} {'miss':>6} {'rejected':>9}")
    best = None
    for sp in pages:
        doc = V.fitz.open(str(path))
        try:
            scan = S.scan_document(doc, start_page=sp)
        except Exception as exc:
            print(f"  {sp:>5} RAISED {type(exc).__name__}: {exc}")
            doc.close()
            continue
        doc.close()
        mk = scan["markers"]
        st = scan["stats"]
        if not mk:
            print(f"  {sp:>5} {0:>8} {'-':>12} {'-':>8} {'-':>5} {'-':>6} {st['rejected']:>9}")
            continue
        bases = [m["base"] for m in mk]
        lo, hi = min(bases), max(bases)
        cov = set(bases)
        miss = hi - lo + 1 - len(cov)
        dens = len(cov) / (hi - lo + 1)
        viol = sum(1 for i in range(1, len(bases)) if bases[i] < bases[i - 1])
        print(f"  {sp:>5} {len(mk):>8} {str(lo) + '..' + str(hi):>12} {dens:8.3f} "
              f"{viol:>5} {miss:>6} {st['rejected']:>9}")
        if best is None or dens > best[1]:
            best = (sp, dens, len(mk), miss, viol)
    if best:
        print(f"  BEST start_page={best[0]} density={best[1]:.3f} markers={best[2]} "
              f"missing={best[3]} viol={best[4]}")
