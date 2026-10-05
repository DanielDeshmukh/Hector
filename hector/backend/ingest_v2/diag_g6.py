#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""diag_g6.py - trace the G6 failing windows (no gate, prints only)."""

import json
import re
import sys

import v2_common as V
import v2_scanner as S
from step6_validate import norm_raw, chunks60, WINDOW

ACT = sys.argv[1] if len(sys.argv) > 1 else "ipc-1860"
V.tee(f"{ACT}_diag_g6")

registry = V.load_registry()
act = next(a for a in registry if a["act_id"] == ACT)
src = V.SOURCES / act["source_file"].split("/")[-1]
doc = V.fitz.open(str(src))
markers = json.loads((V.RESULTS / f"{ACT}_markers.json").read_text(
    encoding="utf-8"))
segj = json.loads((V.RESULTS / f"{ACT}_segments.json").read_text(
    encoding="utf-8"))
records = [json.loads(ln) for ln in
           (V.OUTPUT / f"{ACT}.jsonl").read_text(encoding="utf-8").splitlines()
           if ln]
raw_pages = [doc[i].get_text("text") for i in range(len(doc))]

print("re-scanning ...", flush=True)
scan = S.scan_document(doc)
lines = scan["lines"]
mk_by_num = {m["number"]: m for m in scan["markers"]}
seg_by_num = {s["number"]: s for s in segj["sections"]}

HYPHEN_MERGE_RE = re.compile(r"(?<=[A-Za-z0-9])-\n(?=[a-z])")

n_missing = 0
n_missing_hyphen = 0
n_missing_nearjoin = 0
examples = []
for rec in records:
    mk = mk_by_num[rec["number"]]
    kept = [k for k in range(mk["start"], mk["end"])
            if lines[k]["label"] is None]
    parts, cur, cur_len = [], [], 0
    for k in kept:
        t = lines[k]["text"]
        add = len(t) + (1 if cur else 0)
        if cur and cur_len + add > 3000:
            parts.append(cur)
            cur, cur_len = [], 0
            add = len(t)
        cur.append(k)
        cur_len += add
    if cur:
        parts.append(cur)
    kept_rec = parts[rec["part_index"]]
    p0, p1 = rec["page_start"], rec["page_end"]
    rawn = norm_raw("\n".join(raw_pages[p0 - 1:p1]))
    frags, cur = [], []
    for k in kept_rec:
        if cur and k != cur[-1] + 1:
            frags.append(cur)
            cur = []
        cur.append(k)
    if cur:
        frags.append(cur)
    # page boundary line ids inside this record (join candidate points)
    page_starts = set()
    for k in kept_rec:
        if lines[k]["page"] != lines[k - 1]["page"] if k else False:
            page_starts.add(k)
    for g in frags:
        ft, _, _, _ = S.assemble_text(lines, g)
        fn = V.norm_ws(ft)
        pos = 0
        for w in chunks60(fn):
            if w not in rawn:
                n_missing += 1
                is_hyphen = "-" in w and not HYPHEN_MERGE_RE.search(w)
                # locate the window in the fragment -> line index & page
                i = fn.find(w)
                near_join = False
                where = None
                if i >= 0:
                    prefix = fn[:i]
                    approx_char = len(prefix)
                    # map fragment char offset to line
                    acc = 0
                    for gi in g:
                        acc += len(V.norm_ws(lines[gi]["text"])) + 1
                        if acc >= approx_char:
                            where = lines[gi]["page"] + 1
                            near_join = acc - approx_char < 65
                            break
                if is_hyphen:
                    n_missing_hyphen += 1
                if near_join:
                    n_missing_nearjoin += 1
                if len(examples) < 8:
                    # find where the chunk should be: first 25 chars in raw
                    probe = w[:25]
                    j = rawn.find(probe)
                    ctx = rawn[max(0, j - 60): j + 110] if j >= 0 else \
                        "<25-char probe not in raw>"
                    examples.append((rec["id"], where, near_join, is_hyphen,
                                     w, ctx))
            pos += 1

print(f"\nmissing windows total: {n_missing}")
print(f"  containing '-' (suspected hyphen-merge mismatch): {n_missing_hyphen}")
print(f"  within 65 chars of a line's end (page/join vicinity): "
      f"{n_missing_nearjoin}")
print("\nEXAMPLES:")
for eid, where, near, hyp, w, ctx in examples:
    print(f"\n{eid}  page_of_window~{where} near_join={near} hyphen={hyp}")
    print(f"  MISSING: {w!r}")
    print(f"  RAW around probe: {ctx!r}")
doc.close()
