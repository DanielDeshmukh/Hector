#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""diag_a7c.py - read-only diagnostic for AMENDMENT A7c.

Modifies nothing; writes results/<act_id>_diag_a7c.log (V.tee).
Prints: chapter-heading lines and how they classify; marker spans + inline
refs + footnote groups for the A7c verification sections; the 498/498A line
run; page-number/footnote context inside 498A, 300, 304; and raw source-typo
occurrences ("Jutsice", "he likely", ". or").
"""

import re
import sys
from bisect import bisect_left, bisect_right

import v2_common as V
import v2_scanner as S

ACT = "ipc-1860"
CHAP_LOOSE_RE = re.compile(r"^\s*\[?\s*CHAPTER\s+[IVXLCDM]{1,8}[A-Z]?\b", re.I)
FOOT_HEAD_RE = re.compile(r"^\s*(\d{1,3})\.(?:\s|$)")
REF_PATTERNS = [
    ("num_star_bracket", re.compile(r"(?<!\d)(\d{1,3})\s*\*\[")),
    ("num_stars", re.compile(r"(?<!\d)(\d{1,3})\s*\*{1,4}(?!\*)")),
    ("num_bracket", re.compile(r"(?<!\d)(\d{1,3})\s*\[(?=[A-Za-z\"'(])")),
]
TYPOS = ["Jutsice", "he likely", ". or"]


def refs_in(lines):
    out = []
    for ln in lines:
        if ln["label"] is not None:
            continue
        for name, rx in REF_PATTERNS:
            for m in rx.finditer(ln["text"]):
                out.append({"line": ln["i"], "num": int(m.group(1)),
                            "kind": name, "text": m.group(0),
                            "ctx": ln["text"]})
    return out


def main():
    V.ensure_dirs()
    V.tee(f"{ACT}_diag_a7c")
    print("READ-ONLY A7c diagnostic; nothing modified; no seeds used",
          flush=True)
    registry = V.load_registry()
    act = next(a for a in registry if a["act_id"] == ACT)
    src = V.SOURCES / act["source_file"].split("/")[-1]
    doc = V.fitz.open(str(src))
    scan = S.scan_document(doc)
    lines = scan["lines"]
    markers = scan["markers"]
    groups = scan["groups"]
    by_num = {m["number"]: m for m in markers}

    # ---- 1. chapter headings ------------------------------------------
    print("\n=== 1. CHAPTER HEADING LINES (loose match, any position) ===")
    for ln in lines:
        t = ln["text"]
        stripped = S.fref_strip(t).lstrip()
        if stripped.startswith("["):
            stripped2 = stripped[1:].lstrip()
        else:
            stripped2 = stripped
        if CHAP_LOOSE_RE.match(t) or CHAP_LOOSE_RE.match(stripped) \
                or CHAP_LOOSE_RE.match(stripped2):
            print(f"  i={ln['i']} pdf={ln['page']+1} kind={ln['kind']} "
                  f"label={ln['label']} cls={ln['cls']}")
            print(f"     text={t[:110]!r}")
            cm = V.CHAPTER_RE.match(stripped2)
            print(f"     V.CHAPTER_RE(stripped)={'HIT '+str(cm.groups()) if cm else 'MISS'}")

    # ---- 2. marker spans for the verification sections ------------------
    want = ["13", "19", "20", "21", "300", "302", "303", "304", "304A",
            "304B", "498", "498A"]
    print("\n=== 2. MARKER SPANS + REFS + GROUPS ===")
    B = [ln["i"] for ln in lines if ln["kind"] == "page_number"]
    print(f"scope boundaries: {len(B)}")

    def span_of(li):
        lo_i = bisect_left(B, li) - 1
        lo = B[lo_i] if lo_i >= 0 else -1
        hi_i = bisect_right(B, li)
        hi = B[hi_i] if hi_i < len(B) else len(lines)
        return lo, hi

    all_refs = refs_in(lines)
    for num in want:
        mk = by_num.get(num)
        if mk is None:
            print(f"  {num}: NOT FOUND")
            continue
        lo, hi = span_of(mk["line"])
        g_in = [g["id"] for g in groups if lo < g["start"] < hi]
        print(f"  {num}: marker line={mk['line']} span=[{mk['start']},"
              f"{mk['end']}) pdf={mk['page_1based']} chapter={mk['chapter']!r} "
              f"scope=({lo},{hi}) groups_in_scope={g_in}")
        refs_here = [r for r in all_refs
                     if mk["start"] <= r["line"] < mk["end"]]
        for r in refs_here:
            print(f"      ref {r['text']!r} num={r['num']} line={r['line']} "
                  f"ctx={r['ctx'][:80]!r}")

    # ---- 3. groups in the 302-304B and 19-21 regions --------------------
    print("\n=== 3. FOOTNOTE GROUPS + PER-FOOTNOTE DETAIL (all groups) ===")
    for g in groups:
        lo, hi = span_of(g["start"])
        fns = []
        cur = None
        for mi in g["members"]:
            m = FOOT_HEAD_RE.match(lines[mi]["text"])
            if m:
                if cur:
                    fns.append(cur)
                cur = {"num": m.group(1), "members": [mi]}
            elif cur is None:
                cur = {"num": None, "members": [mi]}
            else:
                cur["members"].append(mi)
        if cur:
            fns.append(cur)
        # owners per A7c: every section with a same-number ref in scope
        scope_refs = [r for r in all_refs if lo < r["line"] < hi]
        owners_desc = []
        for fn in fns:
            if fn["num"] is None:
                owners_desc.append(("?", "unparseable"))
                continue
            n = int(fn["num"])
            own = []
            for r in scope_refs:
                if r["num"] != n:
                    continue
                for mk in markers:
                    if mk["start"] <= r["line"] < mk["end"]:
                        if mk["number"] not in own:
                            own.append(mk["number"])
                        break
            owners_desc.append((fn["num"], own))
        head = "\n".join(lines[mi]["text"] for mi in g["members"][:3])
        print(f"  group {g['id']} lines[{g['start']},{g['end']}) "
              f"pdf={lines[g['start']]['page']+1} scope=({lo},{hi}) "
              f"folios=({lines[lo]['text'] if lo>=0 else None!r},"
              f"{lines[hi]['text'] if hi<len(lines) else None!r})")
        print(f"     footnotes->owners: {owners_desc}")
        print(f"     head: {head[:140]!r}")

    # ---- 4. line runs for 498/498A and the mid-section removals ---------
    for num in ("498", "498A", "300", "304"):
        mk = by_num.get(num)
        if mk is None:
            continue
        if num in ("498", "498A"):
            a = max(0, mk["line"] - (6 if num == "498" else 0))
            b = min(len(lines), mk["end"] + (40 if num == "498" else 60))
            show = set(range(a, b))
        else:
            show = set()
            for i in range(mk["start"], mk["end"]):
                if lines[i]["kind"] == "page_number":
                    show.update(range(max(mk["start"], i - 5),
                                      min(mk["end"], i + 6)))
                if i + 1 < mk["end"] and lines[i]["page"] != lines[i + 1]["page"]:
                    show.update(range(max(mk["start"], i - 4),
                                      min(mk["end"], i + 5)))
        print(f"\n=== 4. LINE RUN {num} ({len(show)} lines shown) ===")
        for i in sorted(show):
            ln = lines[i]
            mark = ""
            if ln["kind"] == "page_number":
                mark = " <<PAGE_NUMBER>>"
            if ln["label"] == "footnote":
                mark += " [footnote]"
            print(f"  i={i} p{ln['page']+1} k={ln['kind']} "
                  f"l={ln['label']} c={ln['cls']}{mark}: "
                  f"{ln['text'][:95]!r}")

    # ---- 5. source typos ------------------------------------------------
    print("\n=== 5. SOURCE TYPOS (raw page text, verbatim) ===")
    for typ in TYPOS:
        hits = []
        for pi, pg in enumerate(doc):
            txt = pg.get_text("text", sort=True)
            for m in re.finditer(re.escape(typ), txt):
                a = max(0, m.start() - 55)
                hits.append((pi + 1, txt[a:m.end() + 55].replace("\n", "|")))
        print(f"  {typ!r}: {len(hits)} occurrence(s)")
        for p, ctx in hits[:8]:
            print(f"    pdf p{p}: ...{ctx!r}...")

    print("\n[exit] 0", flush=True)
    doc.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
