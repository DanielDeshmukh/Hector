#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""check_currency.py - A10 read-only source currency check (report only).

Usage: python check_currency.py --act <act_id>

Log: results/<act_id>_currency.log (tee'd by this script).

Reports:
  1. PDF metadata creation/modification dates.
  2. Any "as amended up to" text on the first pages.
  3. From the footnote lines: every "Act N of YYYY" / "Act YYYY" reference,
     the HIGHEST year found, and the 10 most recent amending acts named.
  4. External anchor (user-supplied, NOT an authority): presence/absence of
     sections 326A, 326B, 354A, 354B, 354C, 354D, 370A, 376AB, 376DA,
     376DB, 376E (2013 / 2018 criminal law amendments).
  5. Plain verdict when anchor sections are absent.

Read-only: opens the PDF and reads existing result files; writes only the log.
"""

import argparse
import json
import re
import sys

import v2_common as V
import v2_scanner as S

ACT_REF_RE = re.compile(r"Act\s+(?:(\d{1,3})\s+of\s+(\d{4})|(\d{4}))")
AMENDED_RE = re.compile(r"as amended\s+up\s*to[^\n.]*", re.IGNORECASE)
ANCHOR_SECTIONS = ["326A", "326B", "354A", "354B", "354C", "354D", "370A",
                   "376AB", "376DA", "376DB", "376E"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--act", required=True, help="act_id from act_registry.yaml")
    args = ap.parse_args()

    V.ensure_dirs()
    act_id = args.act
    V.tee(f"{act_id}_currency")
    print("seeds used: none (A10 is deterministic, read-only)", flush=True)
    registry = V.load_registry()
    act = next((a for a in registry if a["act_id"] == act_id), None)
    if act is None:
        print(f"FATAL: act_id {act_id!r} not in {V.REGISTRY_PATH}", flush=True)
        return 2

    print("\n" + "=" * 76, flush=True)
    print(f"A10 SOURCE CURRENCY CHECK {act_id}  ({act['act_name']})",
          flush=True)
    print("=" * 76, flush=True)

    src = V.SOURCES / act["source_file"].split("/")[-1]
    doc = V.fitz.open(str(src))

    md = doc.metadata or {}
    print("\n1. PDF metadata:", flush=True)
    for key in ("creationDate", "modDate", "producer", "creator", "format"):
        print(f"   {key}: {md.get(key)!r}", flush=True)

    print("\n2. 'as amended up to' text on the first pages:", flush=True)
    amended_hits = []
    for i in range(min(12, len(doc))):
        txt = doc[i].get_text("text")
        for m in AMENDED_RE.finditer(txt):
            amended_hits.append((i + 1, re.sub(r"\s+", " ", m.group(0)).strip()))
    if amended_hits:
        for page, hit in amended_hits:
            print(f"   PDF page {page}: {hit!r}", flush=True)
    else:
        print("   (none found on pages 1-12)", flush=True)

    print("\n3. Act references in the footnote lines "
          "(scanner footnote blocks):", flush=True)
    scan = S.scan_document(doc, start_page=V.body_scan_start(act_id))
    fblocks = [f["text"] for f in scan["footnotes"]]
    refs = []
    for g in fblocks:
        flat = re.sub(r"\s+", " ", g)
        for m in ACT_REF_RE.finditer(flat):
            year = int(m.group(2) or m.group(3))
            refs.append((year, m.group(0).strip()))
    years = sorted({y for y, _ in refs})
    print(f"   footnote blocks: {len(fblocks)}", flush=True)
    print(f"   total matches: {len(refs)}; distinct years: "
          f"{years if years else 'none'}", flush=True)
    if years:
        print(f"   HIGHEST YEAR FOUND: {years[-1]}", flush=True)
    else:
        print("   HIGHEST YEAR FOUND: none", flush=True)
    seen = set()
    recent = []
    for y, t in sorted(refs, key=lambda r: (-r[0], r[1])):
        key = t.lower()
        if key in seen:
            continue
        seen.add(key)
        recent.append((y, t))
        if len(recent) == 10:
            break
    print("   10 most recent amending acts named:", flush=True)
    if recent:
        for y, t in recent:
            count = sum(1 for _, tt in refs if tt == t)
            print(f"     {y}: {t!r} ({count}x)", flush=True)
    else:
        print("     (none)", flush=True)

    mk_path = V.RESULTS / f"{act_id}_markers.json"
    markers = json.loads(mk_path.read_text(encoding="utf-8"))
    nums = {m["number"] for m in markers}
    present = [s for s in ANCHOR_SECTIONS if s in nums]
    absent = [s for s in ANCHOR_SECTIONS if s not in nums]
    print("\n4. External anchor sections (2013/2018 amendments, user-supplied "
          "NOT an authority):", flush=True)
    print(f"   present: {present or 'none'}", flush=True)
    print(f"   absent:  {absent or 'none'}", flush=True)

    print("\n5. verdict:", flush=True)
    if absent:
        print("   These sections are absent: this PDF predates the 2013 and "
              "2018 criminal law amendments and must be replaced with the "
              "official India Code copy.", flush=True)
    else:
        print("   All anchor sections present: the source includes the 2013 "
              "and 2018 criminal law amendments.", flush=True)

    doc.close()
    print(f"\nCHECKPOINT check_currency done -> results/{act_id}_currency.log",
          flush=True)
    print("[exit] 0", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
