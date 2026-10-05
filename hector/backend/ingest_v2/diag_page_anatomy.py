#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""diag_page_anatomy.py - evidence: y positions of page numbers, separators,
footnote blocks and markers on sample pages, to set cleaning rules honestly.

Usage: python diag_page_anatomy.py --act ipc-1860 --pages 3,4,5,21,52
Log: results/<act_id>_diag_anatomy.log
"""

import argparse
import re
import sys

import v2_common as V

NUM_ONLY_RE = re.compile(r"^\s*\d{1,4}[A-Za-z]{0,2}\.\s*$")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--act", required=True)
    ap.add_argument("--pages", default="3,4,5,21,52")
    args = ap.parse_args()
    V.ensure_dirs()
    act_id = args.act
    V.tee(f"{act_id}_diag_anatomy")
    print("seeds used: none (diagnostic)", flush=True)

    registry = V.load_registry()
    act = next(a for a in registry if a["act_id"] == act_id)
    src = V.SOURCES / act["source_file"].split("/")[-1]
    doc = V.fitz.open(str(src))

    for p in [int(x) for x in args.pages.split(",")]:
        pg = doc[p - 1]
        _, lines = V.page_lines(pg)
        H = pg.rect.height
        print("\n" + "=" * 74, flush=True)
        print(f"PAGE {p} (H={H:.0f}) - block order lines with y_norm:", flush=True)
        for k, l in enumerate(lines):
            t = l["text"].rstrip()
            if not t.strip():
                continue
            yn = l["y"] / H
            flags = []
            if V.PAGE_NUM_RE.match(t.strip()):
                flags.append("PAGENUM")
            if V.is_separator(t):
                flags.append("SEP")
            if NUM_ONLY_RE.match(t.strip()):
                flags.append("NUMONLY")
            if yn >= 0.75:
                flags.append("LOW")
            print(f"  {k:3d} y={yn:.3f} {' '.join(flags):24s} {t.strip()[:80]!r}",
                  flush=True)

    # global: FOOT_RE-like note lines y distribution
    print("\n" + "=" * 74, flush=True)
    print("global y_norm stats for NUMONLY lines (footnote markers?):", flush=True)
    hist = {}
    total = 0
    for pg in doc:
        _, lines = V.page_lines(pg)
        H = pg.rect.height
        for l in lines:
            t = l["text"].strip()
            if NUM_ONLY_RE.match(t):
                yn = round(l["y"] / H, 1)
                hist[yn] = hist.get(yn, 0) + 1
                total += 1
    for k in sorted(hist):
        print(f"  y_norm {k:.1f}: {hist[k]}", flush=True)
    print(f"  total NUMONLY lines: {total}", flush=True)

    # global: PAGENUM lines y distribution
    print("\nglobal y_norm stats for standalone number lines (page numbers):",
          flush=True)
    hist2 = {}
    for pg in doc:
        _, lines = V.page_lines(pg)
        H = pg.rect.height
        for l in lines:
            t = l["text"].strip()
            if V.PAGE_NUM_RE.match(t):
                yn = round(l["y"] / H, 1)
                hist2[yn] = hist2.get(yn, 0) + 1
    for k in sorted(hist2):
        print(f"  y_norm {k:.1f}: {hist2[k]}", flush=True)

    # SEP lines: y + whether followed by NUMONLY on same page
    print("\nSEP lines (y_norm, has NUMONLY after on same page):", flush=True)
    seps = 0
    for i, pg in enumerate(doc):
        _, lines = V.page_lines(pg)
        H = pg.rect.height
        for k, l in enumerate(lines):
            if V.is_separator(l["text"]):
                yn = l["y"] / H
                after = any(NUM_ONLY_RE.match(x["text"].strip())
                            for x in lines[k + 1:])
                print(f"  p{i + 1} y={yn:.3f} after_numonly={after}", flush=True)
                seps += 1
    print(f"  total SEP lines: {seps}", flush=True)

    doc.close()
    print("\n[diag] complete", flush=True)
    return 0


if __name__ == "__main__":
    try:
        rc = main()
    except SystemExit:
        raise
    except Exception:
        import traceback
        print("FATAL unhandled error in diag_page_anatomy.py", flush=True)
        traceback.print_exc(file=sys.stdout)
        rc = 2
    print(f"[exit] {rc}", flush=True)
    sys.exit(rc)
