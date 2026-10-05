#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""diag_ipc_lines.py - evidence dump: how IPC section markers actually appear
in line form, to design the SEQUENCE_ONLY scanner honestly (no guessing).

Usage: python diag_ipc_lines.py --act ipc-1860
Log: results/<act_id>_diag_lines.log
"""

import argparse
import re
import sys

import v2_common as V

NUM_ONLY_RE = re.compile(r"^\s*(\d{1,4}[A-Za-z]{0,2})\.\s*$")
NUM_TITLE_RE = re.compile(r"^\s*(\d{1,4}[A-Za-z]{0,2})\.\s+(\S.*)$")
DASH_RE = re.compile(r"\.\s*(?:--|-|\u2013|\u2014)")
BRACKET_RE = re.compile(r"^\s*\[.*\]\s*(Rep\.|Repealed|Omitted|Subs\.|Ins\.)",
                        re.I)


def collect(doc):
    out = []
    for i, pg in enumerate(doc):
        _, lines = V.page_lines(pg)
        for lidx, l in enumerate(lines):
            out.append((i + 1, lidx, l["text"].rstrip()))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--act", required=True)
    args = ap.parse_args()
    V.ensure_dirs()
    act_id = args.act
    V.tee(f"{act_id}_diag_lines")
    print("seeds used: none (diagnostic)", flush=True)

    registry = V.load_registry()
    act = next(a for a in registry if a["act_id"] == act_id)
    src = V.SOURCES / act["source_file"].split("/")[-1]
    doc = V.fitz.open(str(src))
    lines = collect(doc)
    print(f"pages={len(doc)} lines={len(lines)}", flush=True)

    num_only, num_title_no_dash, num_title_dash, bracket = [], [], [], []
    for p, li, t in lines:
        if not t.strip():
            continue
        m1 = NUM_ONLY_RE.match(t)
        if m1:
            num_only.append((p, li, m1.group(1)))
            continue
        m2 = NUM_TITLE_RE.match(t)
        if m2:
            if DASH_RE.search(m2.group(2)):
                num_title_dash.append((p, li, m2.group(1), t))
            else:
                num_title_no_dash.append((p, li, m2.group(1), t))
            continue
        if BRACKET_RE.match(t):
            bracket.append((p, li, t))

    print("\n=== CATEGORY COUNTS ===", flush=True)
    print(f"NUM_ONLY ('N.' alone): {len(num_only)}", flush=True)
    print(f"NUM_TITLE with dash ('N. Title.--...'): {len(num_title_dash)}",
          flush=True)
    print(f"NUM_TITLE without dash ('N. Title...' no marker dash): "
          f"{len(num_title_no_dash)}", flush=True)
    print(f"BRACKET '[...] Rep./Omitted...': {len(bracket)}", flush=True)

    print("\n=== NUM_ONLY: what follows each (up to 4 non-empty lines) ===",
          flush=True)
    by_pos = {}
    for idx, (p, li, t) in enumerate(lines):
        by_pos[(p, li)] = idx
    shown = 0
    for p, li, num in num_only:
        idx = by_pos[(p, li)]
        following = []
        j = idx + 1
        while j < len(lines) and len(following) < 4:
            txt = lines[j][2].strip()
            if txt:
                following.append((lines[j][0], txt))
            j += 1
        has_marker = any(
            NUM_TITLE_RE.match(t2) and DASH_RE.search(NUM_TITLE_RE.match(t2).group(2))
            and NUM_TITLE_RE.match(t2).group(1) == num
            for _, t2 in following)
        has_bracket = any(BRACKET_RE.match(t2) for _, t2 in following)
        tag = "FULL_MARKER_IN_4" if has_marker else (
            "BRACKET" if has_bracket else "???")
        if shown < 40 or tag != "FULL_MARKER_IN_4":
            print(f"  [{tag}] p{p} '{num}.' ->", flush=True)
            for fp, ft in following:
                print(f"        p{fp}: {ft[:95]!r}", flush=True)
            shown += 1
            if shown > 60:
                print("  ...(stopped after 60 dumps)", flush=True)
                break

    print("\n=== NUM_TITLE WITHOUT DASH: examples (first 25) ===", flush=True)
    for p, li, num, t in num_title_no_dash[:25]:
        idx = by_pos[(p, li)]
        following = []
        j = idx + 1
        while j < len(lines) and len(following) < 3:
            txt = lines[j][2].strip()
            if txt:
                following.append((lines[j][0], txt))
            j += 1
        print(f"  p{p} {t[:95]!r}", flush=True)
        for fp, ft in following:
            print(f"        -> p{fp}: {ft[:95]!r}", flush=True)

    print("\n=== BRACKET (omitted/repealed) examples (first 25) ===", flush=True)
    for p, li, t in bracket[:25]:
        # the number line should be just above
        prev = ""
        for k in range(idx - 1 if False else 0, 0):
            pass
        idx = by_pos[(p, li)]
        for back in range(1, 4):
            pp, pli, pt = lines[idx - back]
            if NUM_ONLY_RE.match(pt.strip()):
                prev = pt.strip()
                break
        print(f"  p{p} number-line={prev!r} text={t[:95]!r}", flush=True)

    print("\n=== LAST 40 LINES OF DOCUMENT (sections 505-511?) ===", flush=True)
    for p, li, t in lines[-40:]:
        if t.strip():
            print(f"  p{p}: {t.strip()[:110]!r}", flush=True)

    print("\n=== LINES CONTAINING '511' or '510.' ===", flush=True)
    for p, li, t in lines:
        if re.search(r"\b511\.|\b510\.", t):
            print(f"  p{p}: {t.strip()[:110]!r}", flush=True)

    print("\n=== RAW PAGE 2 (wrapped-title evidence) ===", flush=True)
    print(doc[1].get_text("text"), flush=True, end="")

    print("\n=== RAW PAGE 52 (115-121 / 120A-120B evidence) ===", flush=True)
    print(doc[51].get_text("text"), flush=True, end="")

    print("\n=== RAW PAGE 6 (sections ~19-23) ===", flush=True)
    print(doc[5].get_text("text"), flush=True, end="")

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
        print("FATAL unhandled error in diag_ipc_lines.py", flush=True)
        traceback.print_exc(file=sys.stdout)
        rc = 2
    print(f"[exit] {rc}", flush=True)
    sys.exit(rc)
