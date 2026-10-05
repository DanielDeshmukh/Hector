#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""diag_order_diff.py - evidence: where raw get_text('text') line order differs
from block (y,x) reading order, and which one is the true reading order.

Usage: python diag_order_diff.py --act ipc-1860
Log: results/<act_id>_diag_order.log
"""

import argparse
import difflib
import re
import sys

import v2_common as V


def raw_lines(page):
    out = []
    for ln in page.get_text("text").splitlines():
        s = ln.strip()
        if s:
            out.append(s)
    return out


def block_lines(page):
    _, lines = V.page_lines(page)
    return [l["text"].strip() for l in lines if l["text"].strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--act", required=True)
    ap.add_argument("--pages", default="2,3,5,13")
    args = ap.parse_args()
    V.ensure_dirs()
    act_id = args.act
    V.tee(f"{act_id}_diag_order")
    print("seeds used: none (diagnostic)", flush=True)

    registry = V.load_registry()
    act = next(a for a in registry if a["act_id"] == act_id)
    src = V.SOURCES / act["source_file"].split("/")[-1]
    doc = V.fitz.open(str(src))

    want = [int(x) for x in args.pages.split(",")]
    # classify all pages: equal / differ, and how many differ after
    # whitespace-only normalization
    diff_pages = []
    for i, pg in enumerate(doc):
        r, b = raw_lines(pg), block_lines(pg)
        if r != b:
            diff_pages.append(i + 1)
    print(f"pages where stripped raw lines != block lines: "
          f"{len(diff_pages)}/{len(doc)}", flush=True)
    print(f"first 30 diff pages: {diff_pages[:30]}", flush=True)

    for p in want:
        if p > len(doc):
            continue
        pg = doc[p - 1]
        r, b = raw_lines(pg), block_lines(pg)
        print("\n" + "=" * 70, flush=True)
        print(f"PAGE {p}: raw_lines={len(r)} block_lines={len(b)} "
              f"mode={V.reading_order(pg)[0]}", flush=True)
        sm = difflib.SequenceMatcher(None, r, b, autojunk=False)
        ops = [op for op in sm.get_opcodes() if op[0] != "equal"]
        print(f"diff hunks: {len(ops)}", flush=True)
        for tag, i1, i2, j1, j2 in ops[:6]:
            print(f"  [{tag}] raw[{i1}:{i2}] vs block[{j1}:{j2}]", flush=True)
            for k in range(i1, min(i2, i1 + 4)):
                print(f"      RAW   : {r[k][:95]!r}", flush=True)
            for k in range(j1, min(j2, j1 + 4)):
                print(f"      BLOCK : {b[k][:95]!r}", flush=True)

    # focused: is the marker sequence 'N.' -> title -> restated marker
    # preserved by block order on page 2?
    print("\n" + "=" * 70, flush=True)
    print("PAGE 2 full block order (non-empty lines):", flush=True)
    for k, ln in enumerate(block_lines(doc[1])):
        print(f"  {k:3d}: {ln[:100]!r}", flush=True)

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
        print("FATAL unhandled error in diag_order_diff.py", flush=True)
        traceback.print_exc(file=sys.stdout)
        rc = 2
    print(f"[exit] {rc}", flush=True)
    sys.exit(rc)
