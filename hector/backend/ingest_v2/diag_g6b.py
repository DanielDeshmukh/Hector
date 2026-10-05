#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""diag_g6b.py - compare G6 window rates: default raw vs sort=True raw."""

import json
import sys

import v2_common as V
import v2_scanner as S
from step6_validate import norm_raw, chunks60

ACT = sys.argv[1] if len(sys.argv) > 1 else "ipc-1860"
V.tee(f"{ACT}_diag_g6b")

registry = V.load_registry()
act = next(a for a in registry if a["act_id"] == ACT)
src = V.SOURCES / act["source_file"].split("/")[-1]
doc = V.fitz.open(str(src))
records = [json.loads(ln) for ln in
           (V.OUTPUT / f"{ACT}.jsonl").read_text(encoding="utf-8").splitlines()
           if ln]
raw_default = [doc[i].get_text("text") for i in range(len(doc))]
raw_sorted = [doc[i].get_text("text", sort=True) for i in range(len(doc))]

print("re-scanning ...", flush=True)
scan = S.scan_document(doc)
lines = scan["lines"]
mk_by_num = {m["number"]: m for m in scan["markers"]}


def part_lines(rec):
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
    return parts[rec["part_index"]]


def run(raw_pages, tag):
    cache = {}
    tot = found = 0
    fails = []
    for rec in records:
        kept_rec = part_lines(rec)
        p0, p1 = rec["page_start"], rec["page_end"]
        if (p0, p1) not in cache:
            cache[(p0, p1)] = norm_raw("\n".join(raw_pages[p0 - 1:p1]))
        rawn = cache[(p0, p1)]
        frags, cur = [], []
        for k in kept_rec:
            if cur and k != cur[-1] + 1:
                frags.append(cur)
                cur = []
            cur.append(k)
        if cur:
            frags.append(cur)
        miss = 0
        for g in frags:
            ft, _, _, _ = S.assemble_text(lines, g)
            for w in chunks60(V.norm_ws(ft)):
                tot += 1
                if w in rawn:
                    found += 1
                else:
                    miss += 1
                    if len(fails) < 6:
                        fails.append((rec["id"], w, rawn, p0, p1))
        if miss:
            fails.append((rec["id"], None, None, p0, p1, miss))
    print(f"\n[{tag}] windows {found}/{tot} = {found/tot:.4%}", flush=True)
    shown = 0
    for f in fails:
        if len(f) == 6:
            print(f"  {f[0]}: {f[5]} missing (pages {f[3]}-{f[4]})", flush=True)
        elif shown < 5:
            shown += 1
            print(f"  {f[0]} missing: {f[1]!r}", flush=True)
    return found, tot


run(raw_default, "default get_text")
run(raw_sorted, "sort=True get_text")
doc.close()
