#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""diag_a7b_check.py - read-only A7b/A7c status diagnosis (no writes).

Prints every unattached/ambiguous footnote with span + folio bounds and all
same-number refs in the document, plus the chapter notes. Tee -> results log.
"""

import v2_common as V
import v2_scanner as S


def main():
    V.ensure_dirs()
    V.tee("ipc-1860_diag_a7b")
    print("seeds used: none (read-only diagnostic)", flush=True)
    registry = V.load_registry()
    act = next(a for a in registry if a["act_id"] == "ipc-1860")
    src = V.SOURCES / act["source_file"].split("/")[-1]
    doc = V.fitz.open(str(src))
    scan = S.scan_document(doc)
    doc.close()
    lines = scan["lines"]
    foots = scan["footnotes"]
    bounds = scan["scope_boundaries"]
    st = scan["stats"]
    print("stats:", st["footnotes_total"], st["footnotes_attached"],
          st["footnotes_unattached"], st["footnotes_ambiguous"],
          "bounds", st["scope_boundaries"], "chapters",
          st["chapter_notes"], flush=True)
    print("groups", len(scan["groups"]), "markers", len(scan["markers"]),
          flush=True)

    all_refs = {}
    for ln in lines:
        for rx in S.INLINE_REF_RES:
            for m in rx.finditer(ln["text"]):
                n = int(m.group(1))
                all_refs.setdefault(n, []).append(
                    (ln["i"], ln["label"], m.group(0),
                     ln["text"][max(0, m.start() - 30):m.start() + 45]))

    def folio(bi):
        if 0 <= bi < len(lines):
            return lines[bi]["text"][:30]
        return "<none>"

    bad = [f for f in foots if f["status"] != "attached"]
    print("== non-attached footnotes:", len(bad), flush=True)
    for f in bad:
        lo, hi = f["span"]
        print(f"group {f['group']} num={f['num']} status={f['status']} "
              f"reason={f['reason']!r} span=({lo},{hi}) "
              f"folio_lo={folio(lo)!r} folio_hi={folio(hi)!r} "
              f"pdf_page={f['pdf_page']}", flush=True)
        print("  text:", repr(f["text"][:150]), flush=True)
        n = int(f["num"]) if f["num"] and f["num"].isdigit() else None
        if n is not None:
            for r in all_refs.get(n, [])[:8]:
                inspan = "IN-SPAN" if lo < r[0] < hi else "out"
                print(f"  ref line={r[0]} label={r[1]} form={r[2]!r} "
                      f"{inspan} ctx={r[3]!r}", flush=True)

    print("== chapter notes:", flush=True)
    for f in scan["chapter_notes"]:
        print(f"group {f['group']} num={f['num']} owners={f['owner_numbers']} "
              f"text={f['text'][:100]!r}", flush=True)
        for r in f["refs"]:
            if r["chapter_note"]:
                print(f"  chapref line={r['line']} ctx={r['ctx']!r}",
                      flush=True)

    # group-level owner summary vs old round-1 audit (19/1/60)
    owned = sum(1 for g in scan["groups"] if g["owner"] is not None)
    print("== groups with owner:", owned, "without:",
          len(scan["groups"]) - owned, flush=True)
    print("[exit] 0", flush=True)
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
