#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""step5_records.py - STEP 5 of the ingest_v2 pilot: build the 27-key
section records (one JSON object per line) from clean + segments output.

Usage: python step5_records.py --act <act_id>

Log: results/<act_id>_step5_records.log (tee'd by this script).
Writes: output/<act_id>.jsonl            (27-key records, one per line)
        results/<act_id>_flags.json      (record-level flags)
        results/<act_id>_assembly.json   (A1 page-join continuity evidence)

A1 test: prints the first 5 records whose page_start != page_end, showing the
text around every page join (fragment boundary) to prove the section text
resumes across removed footnote zones / separators.
"""

import argparse
import hashlib
import json
import re
import sys

import v2_common as V

KEYS = [
    "id", "act_id", "act_name", "act_short", "unit_type", "number", "title",
    "chapter", "hierarchy_path", "text", "embedding_text", "has_proviso",
    "has_explanation", "has_exception", "has_illustration", "parent_id",
    "part_index", "part_count", "source_file", "source_type", "page_start",
    "page_end", "status", "repealed_on", "replaced_by", "amendment_notes",
    "content_hash",
]


def make_record(act, number, chapter, title, part, part_index, part_count,
                notes, form, status_hint):
    if form == "R" or status_hint == "omitted":
        status = "omitted"
        repealed_on = None
        replaced_by = None
    else:
        status = act.get("status")
        repealed_on = act.get("repealed_on")
        replaced_by = act.get("replaced_by")
    text = part["text"]
    num_l = number.lower()
    parent = f"{act['act_id']}:s:{num_l}"
    rid = f"{parent}:{part_index}"
    hier = " > ".join(x for x in
                      [act["act_short"], chapter, f"Section {number}"] if x)
    head = [f"{act['act_short']} {act['year']}"]
    if chapter:
        head.append(chapter)
    head.append(f"Section {number}: {title or ''}")
    header = " | ".join(head)
    if part_count > 1:
        header += f" (part {part_index + 1}/{part_count})"
    embedding = f"{header}\n{text}"
    rec = {
        "id": rid,
        "act_id": act["act_id"],
        "act_name": act["act_name"],
        "act_short": act["act_short"],
        "unit_type": "section",
        "number": number,
        "title": title,
        "chapter": chapter,
        "hierarchy_path": hier,
        "text": text,
        "embedding_text": embedding,
        "has_proviso": bool(re.search(r"\bProvided (further )?that\b", text)),
        "has_explanation": any(ln.lstrip().startswith("Explanation")
                               for ln in text.split("\n")),
        "has_exception": any(ln.lstrip().startswith("Exception")
                             for ln in text.split("\n")),
        "has_illustration": any(ln.lstrip().startswith("Illustration")
                                for ln in text.split("\n")),
        "parent_id": parent,
        "part_index": part_index,
        "part_count": part_count,
        "source_file": act["source_file"],
        "source_type": act.get("source_type", "bare_act"),
        "page_start": part["page_start"],
        "page_end": part["page_end"],
        "status": status,
        "repealed_on": repealed_on,
        "replaced_by": replaced_by,
        "amendment_notes": notes,
        "content_hash": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }
    assert list(rec.keys()) == KEYS, f"schema order mismatch: {list(rec.keys())}"
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--act", required=True, help="act_id from act_registry.yaml")
    args = ap.parse_args()

    V.ensure_dirs()
    act_id = args.act
    V.tee(f"{act_id}_step5_records")
    print("seeds used: none (step5 has no randomness; the A1 join test uses "
          "the first 5 page-spanning records)", flush=True)
    registry = V.load_registry()
    act = next((a for a in registry if a["act_id"] == act_id), None)
    if act is None:
        print(f"FATAL: act_id {act_id!r} not in {V.REGISTRY_PATH}", flush=True)
        return 2

    clean_path = V.RESULTS / f"{act_id}_clean.json"
    seg_path = V.RESULTS / f"{act_id}_segments.json"
    mk_path = V.RESULTS / f"{act_id}_markers.json"
    for p in (clean_path, seg_path, mk_path):
        if not p.exists():
            print(f"FATAL: {p} missing - run the earlier steps first",
                  flush=True)
            return 2
    clean = json.loads(clean_path.read_text(encoding="utf-8"))
    segs = json.loads(seg_path.read_text(encoding="utf-8"))
    markers = json.loads(mk_path.read_text(encoding="utf-8"))
    mk_by_num = {m["number"]: m for m in markers}
    clean_by_num = {s["number"]: s for s in clean["sections"]}

    print("\n" + "=" * 76, flush=True)
    print(f"STEP 5 RECORDS {act_id}  ({act['act_name']})", flush=True)
    print("=" * 76, flush=True)

    records = []
    flags = {"long_unsplit": [], "null_titles": [], "split_sections": []}
    status_counts = {}
    for ssec in segs["sections"]:
        number = ssec["number"]
        csec = clean_by_num[number]
        mk = mk_by_num.get(number, {})
        title = csec["title"]
        if title is None:
            flags["null_titles"].append(number)
        if ssec["part_count"] > 1:
            flags["split_sections"].append(
                {"number": number, "part_count": ssec["part_count"]})
        for part in ssec["parts"]:
            if part["flags"]:
                flags["long_unsplit"].append(
                    {"number": number, "part_index": part["part_index"],
                     "flags": part["flags"], "chars": len(part["text"])})
            rec = make_record(
                act, number, csec["chapter"], title, part,
                part["part_index"], ssec["part_count"],
                csec["amendment_notes"], mk.get("form", "M"),
                mk.get("status_hint", "normal"))
            records.append(rec)
            status_counts[rec["status"]] = status_counts.get(rec["status"], 0) + 1

    out_path = V.OUTPUT / f"{act_id}.jsonl"
    prev_count = 0
    if out_path.exists():
        prev_count = sum(1 for ln in
                         out_path.read_text(encoding="utf-8").splitlines()
                         if ln.strip())
    with open(out_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    ids = [r["id"] for r in records]
    dup_ids = sorted({i for i in ids if ids.count(i) > 1})
    print(f"records before: {prev_count}; after: {len(records)}; "
          f"delta: {len(records) - prev_count:+d}", flush=True)
    print(f"status counts (A3): {status_counts}", flush=True)
    print(f"unique ids: {len(set(ids))}/{len(ids)}; duplicates: {dup_ids or 'none'}",
          flush=True)
    print(f"parts with flags: {flags['long_unsplit'] or 'none'}", flush=True)
    print(f"records with null title: {flags['null_titles'] or 'none'}",
          flush=True)
    print(f"empty texts (must be []): "
          f"{[r['id'] for r in records if not r['text'].strip()]}", flush=True)

    # ---- A1 join test: first 5 page-spanning records --------------------
    spanning = [c for c in clean["sections"]
                if c["page_start"] is not None and c["page_end"] is not None
                and c["page_start"] != c["page_end"]]
    print(f"\nA1 PAGE-SPANNING RECORDS: {len(spanning)} total; showing first "
          f"5 with join context:", flush=True)
    assembly = []
    for c in spanning[:5]:
        entry = {"number": c["number"], "page_start": c["page_start"],
                 "page_end": c["page_end"], "joins": []}
        print(f"  {c['number']} p{c['page_start']}-p{c['page_end']} "
              f"fragments={len(c['fragments'])}", flush=True)
        for a, b in zip(c["fragments"], c["fragments"][1:]):
            tail = a["text"][-140:]
            head = b["text"][:140]
            removed = [r for r in c["removals"]
                       if a["last_line"] < r["line"] < b["first_line"]]
            labels = sorted({r["label"] for r in removed})
            print(f"    join p{a['page_end']}->p{b['page_start']} "
                  f"(removed between: {labels})", flush=True)
            print(f"      ...{tail!r}", flush=True)
            print(f"      ...{head!r}", flush=True)
            entry["joins"].append({
                "from_page": a["page_end"], "to_page": b["page_start"],
                "removed_labels": labels,
                "before_tail": tail, "after_head": head})
        assembly.append(entry)

    flags["page_spanning_records"] = len(spanning)
    flags["a1_shown"] = [c["number"] for c in spanning[:5]]
    V.write_json(V.RESULTS / f"{act_id}_flags.json", flags)
    V.write_json(V.RESULTS / f"{act_id}_assembly.json",
                 {"act_id": act_id, "page_spanning_total": len(spanning),
                  "shown": assembly})
    # ---- A9 range aliases ---------------------------------------------
    rec_by_number = {r["number"]: r["id"] for r in records
                     if r["part_index"] == 0}
    own_numbers = {m["number"] for m in markers}
    range_map = {}
    for m in markers:
        mm = re.match(r"^(\d{1,4})\s+to\s+(\d{1,4}[A-Za-z]{0,2})$",
                      m["number"])
        if not mm:
            continue
        rid = rec_by_number.get(m["number"])
        if rid is None:
            continue
        b1 = int(mm.group(1))
        tok2 = mm.group(2)
        b2 = int(re.sub(r"\D", "", tok2))
        nums = [str(n) for n in range(b1, b2 + 1)]
        suf = re.sub(r"[0-9]+", "", tok2)
        if suf:
            nums.append(tok2)
        for n in nums:
            if n in own_numbers:
                continue
            range_map[n] = rid
    aliases = {"act_id": act_id,
               "rule": "each plain base of a range marker maps to the range "
                       "record id; a suffixed endpoint token maps too, "
                       "unless it has its own accepted marker",
               "aliases": range_map}
    V.write_json(V.OUTPUT / f"{act_id}_aliases.json", aliases)
    print(f"\nA9 RANGE ALIASES ({len(range_map)}) -> "
          f"output/{act_id}_aliases.json:", flush=True)
    for n in sorted(range_map, key=lambda x: (int(re.sub(r"\D", "", x)), x)):
        print(f"  {n} -> {range_map[n]}", flush=True)

    print(f"\nCHECKPOINT step5_records done -> output/{act_id}.jsonl "
          f"(+ flags.json, assembly.json, aliases.json)", flush=True)
    print("[exit] 0", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
