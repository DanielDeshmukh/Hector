#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""diag_bns_regex.py - do the IPC-adapted regexes parse the BNS family?

Runs the *unmodified* v2_scanner (the NUMHEAD/NUMDOT/RESTATED/QUOTE_NUM/RANGE/
FREF/INLINE_REF regexes tuned for ipc-1860) over the BNS-family bare acts.

Each book is scanned twice:

  raw        start_page=0 - includes the Contents/Arrangement pages, which are
             numbered lists and therefore fire the section regex on purpose.
  body       start_page after the front matter - the real section run.

The body start comes from V.body_scan_start() when <act>_toc_meta.json exists
(ipc-1860), otherwise from a data-driven estimate: walk forward while pages
keep carrying >=6 markers (a Contents page), stop at the first lull.

Diagnostic only - not a gate. It answers "does this book's numbering style
match the regex we used for IPC, or does it need its own formula?"

Usage:
  python diag_bns_regex.py
  python diag_bns_regex.py --books bns bnss
  python diag_bns_regex.py --pdf "C:/path/any.pdf"
"""
from __future__ import annotations

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import v2_common as V  # noqa: E402
import v2_scanner as S  # noqa: E402

BOOKS_DIR = V.INGEST.parent.parent / "api" / "data" / "Books"

BOOKS = {
    "ipc": ("THE INDIAN PENAL CODE-1860-45.pdf", "IPC baseline (regex tuned here)", "ipc-1860"),
    "bns": ("Bharatiya Nyaya Sanhita-2023.pdf", "BNS 2023 - IPC successor", "bns-2023"),
    "bnss": ("Bharatiya Nagarik Suraksha Sanhita-2023.pdf", "BNSS 2023 - CrPC successor", "bnss-2023"),
    "bsa": ("Bharatiya Sakshya Adhiniyam-2023.pdf", "BSA 2023 - Evidence successor", "bsa-2023"),
}

DENSE_PAGE = 6  # markers/page that smells like a Contents entry line


def scan_range(path, start_page, label):
    doc = V.fitz.open(path)
    try:
        scan = S.scan_document(doc, start_page=start_page)
    except Exception as exc:
        print(f"  [{label}] SCAN RAISED: {type(exc).__name__}: {exc}")
        return None
    finally:
        doc.close()
    return scan


def report(label, scan, start_page):
    st = scan["stats"]
    markers = scan["markers"]
    nums = [m["number"] for m in markers]
    bases = [m["base"] for m in markers]

    print(f"  --- {label} (start_page={start_page}) ---")
    print(f"      lines={st['lines']} markers={st['markers']} rejected={st['rejected']} "
          f"forms={st['forms']}")
    print(f"      gaps={len(st['gaps'])} lettered={len(st['lettered'])} "
          f"labels={st['labels']}")
    if not nums:
        print("      >>> ZERO MARKERS - regex recognised no section heads")
        return None

    per_page = {}
    for m in markers:
        per_page[m["page_1based"]] = per_page.get(m["page_1based"], 0) + 1
    hot = sorted(per_page.items(), key=lambda kv: -kv[1])[:6]
    print(f"      markers/page hottest6={hot}")

    viol = [(i, nums[i - 1], nums[i]) for i in range(1, len(bases))
            if bases[i] < bases[i - 1]]
    print(f"      order violations={len(viol)}" + (f" e.g. {viol[:4]}" if viol else ""))
    print(f"      first8={nums[:8]}")
    print(f"      last8 ={nums[-8:]}")

    lo, hi = min(bases), max(bases)
    covered = set(bases)
    missing = [n for n in range(lo, hi + 1) if n not in covered]
    dens = len(covered) / (hi - lo + 1)
    print(f"      span={lo}..{hi} distinct={len(covered)} density={dens:.3f} "
          f"missing={len(missing)}"
          + (f" -> {missing[:14]}{'...' if len(missing) > 14 else ''}" if missing else ""))

    verdict = "PARSEABLE" if dens >= 0.95 and len(viol) <= 3 else "NEEDS REVIEW"
    print(f"      >>> {verdict}")
    return {"markers": st["markers"], "density": dens, "viol": len(viol),
            "span": (lo, hi), "missing": len(missing), "verdict": verdict,
            "nums": nums, "per_page": per_page}


def estimate_body_start(per_page):
    """Pages carrying >= DENSE_PAGE markers at the head of the book = Contents.
    Returns 0-based first body page."""
    if not per_page:
        return 0
    dense = {p for p, c in per_page.items() if c >= DENSE_PAGE}
    if not dense:
        return 0
    front_end = 0
    for p in sorted(per_page):
        if p in dense:
            front_end = p
        elif p > front_end + 1:
            break
    return front_end  # 1-based page -> 0-based next page index


def analyse(label, path, act_id, forced_start=None):
    print("=" * 76)
    print(f"{label}")
    print(f"  file={os.path.basename(path)}")
    if not os.path.exists(path):
        print("  MISSING FILE")
        return None

    raw = scan_range(path, 0, "raw")
    if raw is None:
        return None
    raw_res = report("RAW (start_page=0, includes Contents)", raw, 0)

    body_start = forced_start
    src = "explicit"
    if body_start is None:
        body_start = V.body_scan_start(act_id)
        src = "toc_meta" if body_start else "estimate"
        if not body_start and raw_res:
            body_start = estimate_body_start(raw_res["per_page"])
    print(f"  body start = {body_start}  (source: {src})")

    if body_start:
        body = scan_range(path, body_start, "body")
        body_res = report("BODY (front matter excluded)", body, body_start) if body else None
    else:
        body_res = raw_res

    return {"raw": raw_res, "body": body_res, "body_start": body_start}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--books", nargs="*", default=["ipc", "bns", "bnss", "bsa"])
    ap.add_argument("--pdf", help="test a single arbitrary PDF instead")
    ap.add_argument("--start-page", type=int, default=None)
    args = ap.parse_args()

    print("regex set under test: v2_scanner.py (IPC-tuned, unmodified)")
    for n in ("NUMHEAD_RE", "NUMDOT_RE", "RESTATED_RE", "QUOTE_NUM_RE",
              "RANGE_RE", "FREF_RE"):
        print(f"  {n:12} {getattr(S, n).pattern}")
    print()

    results = {}
    if args.pdf:
        results["custom"] = analyse(os.path.basename(args.pdf), args.pdf, "custom",
                                    forced_start=args.start_page)
    else:
        for key in args.books:
            if key not in BOOKS:
                print(f"unknown book '{key}' (known: {list(BOOKS)})")
                continue
            fn, desc, act_id = BOOKS[key]
            results[key] = analyse(f"{key.upper()} - {desc}", str(BOOKS_DIR / fn),
                                   act_id, forced_start=args.start_page)

    print("=" * 76)
    print("SUMMARY  (body pass)")
    print(f"  {'book':8} {'markers':>8} {'span':>10} {'density':>8} "
          f"{'viol':>5} {'missing':>8}  verdict")
    for k, v in results.items():
        if not v or not v.get("body"):
            print(f"  {k:8} {'FAILED/0':>8}")
            continue
        b = v["body"]
        print(f"  {k:8} {b['markers']:8d} {str(b['span'][0]) + '..' + str(b['span'][1]):>10} "
              f"{b['density']:8.3f} {b['viol']:5d} {b['missing']:8d}  {b['verdict']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
