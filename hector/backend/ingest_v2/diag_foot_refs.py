#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""diag_foot_refs.py - read-only diagnostic + prototype for A7b.

Modifies nothing; writes only results/<act_id>_diag_foot_refs.log (V.tee).
Prints: scope boundaries (standalone page-number lines), footnote-group
structure with per-footnote numbers, candidate inline-reference forms found
in kept body lines, and the prototype attached/unattached/ambiguous counts
under the A7b printed-page span rule, plus detail for PDF pages 5 and 7.
"""

import re
import sys
from bisect import bisect_left, bisect_right

import v2_common as V
import v2_scanner as S

ACT = "ipc-1860"
FOOT_HEAD_RE = re.compile(r"^\s*(\d{1,3})\.(?:\s|$)")
REF_PATTERNS = [
    ("num_star_bracket", re.compile(r"(?<!\d)(\d{1,3})\s*\*\[")),
    ("num_stars", re.compile(r"(?<!\d)(\d{1,3})\s*\*{1,4}(?!\*)")),
    ("num_bracket", re.compile(r"(?<!\d)(\d{1,3})\s*\[(?=[A-Za-z\"'(])")),
    ("superscript", re.compile(r"[\u2070\u00b9\u00b2\u00b3\u2074\u2075"
                                r"\u2076\u2077\u2078\u2079]{1,3}")),
]
SUP_MAP = {"\u2070": "0", "\u00b9": "1", "\u00b2": "2", "\u00b3": "3",
           "\u2074": "4", "\u2075": "5", "\u2076": "6", "\u2077": "7",
           "\u2078": "8", "\u2079": "9"}


def sup_to_int(s):
    return int("".join(SUP_MAP[c] for c in s))


def parse_footnotes(group, lines):
    fns = []
    cur = None
    for mi in group["members"]:
        m = FOOT_HEAD_RE.match(lines[mi]["text"])
        if m:
            if cur is not None:
                fns.append(cur)
            cur = {"num": m.group(1), "members": [mi]}
        else:
            if cur is None:
                cur = {"num": None, "members": [mi]}
            else:
                cur["members"].append(mi)
    if cur is not None:
        fns.append(cur)
    return fns


def main():
    V.ensure_dirs()
    V.tee(f"{ACT}_diag_foot_refs")
    print("READ-ONLY A7b diagnostic; nothing modified; no seeds used",
          flush=True)
    registry = V.load_registry()
    act = next(a for a in registry if a["act_id"] == ACT)
    src = V.SOURCES / act["source_file"].split("/")[-1]
    doc = V.fitz.open(str(src))
    scan = S.scan_document(doc)
    lines = scan["lines"]
    markers = scan["markers"]
    groups = scan["groups"]

    # ---- 1. scope boundaries ------------------------------------------
    bounds = [ln["i"] for ln in lines if ln["kind"] == "page_number"]
    print(f"\n=== 1. SCOPE BOUNDARIES (kind==page_number): {len(bounds)} ===")
    per_pdf = {}
    for b in bounds:
        p = lines[b]["page"] + 1
        per_pdf[p] = per_pdf.get(p, 0) + 1
    print(f"  boundaries per PDF page (first 20): "
          f"{dict(sorted(per_pdf.items())[:20])}")
    for b in bounds[:8]:
        before = lines[b - 1]["text"][:70] if b else ""
        after = lines[b + 1]["text"][:70] if b + 1 < len(lines) else ""
        print(f"  i={b} pdf={lines[b]['page'] + 1} val={lines[b]['text']!r}")
        print(f"     before: {before!r}")
        print(f"     after:  {after!r}")

    # ---- 2. groups + per-footnote split --------------------------------
    print(f"\n=== 2. FOOTNOTE GROUPS: {len(groups)} ===")
    all_fns = []
    for g in groups:
        fns = parse_footnotes(g, lines)
        all_fns.append((g, fns))
    print(f"  footnotes after per-footnote split: "
          f"{sum(len(f) for _, f in all_fns)}")
    for g, fns in all_fns[:6]:
        print(f"  group {g['id']} start={g['start']} end={g['end']} "
              f"members={len(g['members'])} nums="
              f"{[f['num'] for f in fns]}")
        for mi in g["members"][:4]:
            print(f"     [{lines[mi]['cls']}] {lines[mi]['text'][:100]!r}")

    # ---- 3. candidate inline refs in kept body lines -------------------
    refs = []
    form_counts = {}
    samples = {}
    for ln in lines:
        if ln["label"] is not None:
            continue
        for name, rx in REF_PATTERNS:
            for m in rx.finditer(ln["text"]):
                num = sup_to_int(m.group(0)) if name == "superscript" \
                    else int(m.group(1))
                refs.append({"line": ln["i"], "num": num, "kind": name,
                             "text": m.group(0),
                             "ctx": ln["text"]})
                form_counts[name] = form_counts.get(name, 0) + 1
                samples.setdefault(name, []).append(
                    (ln["i"], m.group(0), ln["text"][:90]))
    print(f"\n=== 3. CANDIDATE INLINE REFS in kept lines: {len(refs)} ===")
    print(f"  by form: {form_counts}")
    for name, ss in samples.items():
        print(f"  form {name}: first 6")
        for i, mt, ctx in ss[:6]:
            print(f"     line {i}: {mt!r} in {ctx!r}")

    # ---- 4. prototype attachment under the A7b span rule ---------------
    mk_spans = [(m["start"], m["end"], m["number"]) for m in markers]

    def owner_of(li):
        for st, en, num in mk_spans:
            if st <= li < en:
                return num
        return None

    B = bounds
    tot = att = una = amb = 0
    detail = []
    for g, fns in all_fns:
        lo_i = bisect_left(B, g["start"]) - 1
        lo = B[lo_i] if lo_i >= 0 else -1
        hi_i = bisect_right(B, g["end"])
        hi = B[hi_i] if hi_i < len(B) else len(lines)
        span_refs = [r for r in refs if lo < r["line"] < hi]
        for fn in fns:
            tot += 1
            status, own, pick = "ambiguous", None, None
            if fn["num"] is None:
                reason = "number not parseable"
            else:
                fn_num = int(fn["num"])
                cands = [r for r in span_refs if r["num"] == fn_num]
                pref = [r for r in cands if r["line"] < g["start"]]
                if pref:
                    pick = max(pref, key=lambda r: r["line"])
                else:
                    foll = [r for r in cands if r["line"] > g["end"]]
                    pick = min(foll, key=lambda r: r["line"]) if foll else None
                if pick is None:
                    status, reason = "unattached", "no same-number ref in span"
                else:
                    own = owner_of(pick["line"])
                    if own is None:
                        status = "ambiguous"
                        reason = "ref outside any section marker span"
                    else:
                        status, reason = "attached", ""
            if status == "attached":
                att += 1
            elif status == "unattached":
                una += 1
            else:
                amb += 1
            detail.append({"group": g["id"], "num": fn["num"],
                           "status": status, "marker": own,
                           "reason": reason,
                           "ref_line": pick["line"] if pick else None,
                           "ref_text": pick["text"] if pick else None,
                           "pdf_page": lines[fn["members"][0]]["page"] + 1,
                           "members": fn["members"],
                           "text": "\n".join(
                               lines[mi]["text"] for mi in fn["members"])})
    print(f"\n=== 4. PROTOTYPE A7b COUNTS (footnote level) ===")
    print(f"  total footnotes: {tot}")
    print(f"  attached by reference: {att}")
    print(f"  unattached (no ref in span): {una}")
    print(f"  ambiguous (unparseable / no owning section): {amb}")
    print(f"  round-1 audit (group level): 19 by reference, 1 fallback, "
          f"60 ambiguous (80 groups)")
    g_att = sum(1 for g, fns in all_fns
                if fns and all(d["status"] == "attached"
                               for d in detail
                               if d["group"] == g["id"]))
    g_any = sum(1 for g, fns in all_fns
                if any(d["status"] == "attached"
                       for d in detail if d["group"] == g["id"]))
    print(f"  group-level now: all-footnotes-attached={g_att}, "
          f"any-attached={g_any}, groups={len(groups)}")

    print("\n  first 12 non-attached footnotes:")
    shown = 0
    for d in detail:
        if d["status"] != "attached":
            print(f"    group {d['group']} num={d['num']} "
                  f"pdf={d['pdf_page']} {d['status']}: {d['reason']}; "
                  f"text={d['text'][:80]!r}")
            shown += 1
            if shown >= 12:
                break

    # ---- 5. PDF pages 5 and 7 detail -----------------------------------
    for target in (5, 7):
        print(f"\n=== 5. PDF PAGE {target}: footnote groups on this page ===")
        for g, fns in all_fns:
            if not any(lines[mi]["page"] + 1 == target
                       for mi in g["members"]):
                continue
            lo_i = bisect_left(B, g["start"]) - 1
            lo = B[lo_i] if lo_i >= 0 else -1
            hi_i = bisect_right(B, g["end"])
            hi = B[hi_i] if hi_i < len(B) else len(lines)
            folio_lo = lines[lo]["text"] if lo >= 0 else None
            folio_hi = lines[hi]["text"] if hi < len(lines) else None
            print(f"  group {g['id']} span=({lo},{hi}) "
                  f"folios=({folio_lo!r},{folio_hi!r})")
            for d in detail:
                if d["group"] != g["id"]:
                    continue
                ctx = ""
                if d["ref_line"] is not None:
                    t = lines[d["ref_line"]]["text"]
                    pos = t.find(d["ref_text"] or "@@")
                    a = max(0, pos - 40)
                    ctx = t[a:pos + 40 + len(d["ref_text"] or "")]
                print(f"    fn {d['num']}: {d['status']} -> marker "
                      f"{d['marker']} ref_line={d['ref_line']} "
                      f"ctx={ctx!r}")
                print(f"       text: {d['text'][:110]!r}")

    print(f"\n[exit] 0", flush=True)
    doc.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
