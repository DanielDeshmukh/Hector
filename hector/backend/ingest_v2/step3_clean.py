#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""step3_clean.py - STEP 3 of the ingest_v2 pilot: per-section text cleaner.

Usage: python step3_clean.py --act <act_id>

Log: results/<act_id>_step3_clean.log (tee'd by this script).
Writes: results/<act_id>_clean.json
        {act_id, label_counts, unlabeled_removals, scan_stats,
         sections: [{number, title, chapter, marker_line, start, end,
                     page_start, page_end, text, fragments, removals,
                     amendment_notes}]}

Removals: only lines that carry a rule label (page_number, separator,
footnote, header, boilerplate) are dropped - SPEC AMENDMENTS A1/A2. Join
points for the A2 fragment check are the fragment boundaries stored per
section. A section never ends at the first footnote or separator: its text
resumes on the following lines (A1).
"""

import argparse
import sys

import v2_common as V
import v2_scanner as S


def group_fragments(idxs):
    groups = []
    cur = []
    for k in idxs:
        if cur and k != cur[-1] + 1:
            groups.append(cur)
            cur = []
        cur.append(k)
    if cur:
        groups.append(cur)
    return groups


def clean_sections(doc, start_page=0):
    scan = S.scan_document(doc, start_page=start_page)
    lines = scan["lines"]
    sections = []
    label_counts = {}
    unlabeled = 0
    span_lines = 0
    page_spanning = 0
    for mk in scan["markers"]:
        kept = []
        removals = []
        for k in range(mk["start"], mk["end"]):
            span_lines += 1
            lab = lines[k]["label"]
            if lab is None:
                kept.append(k)
            else:
                label_counts[lab] = label_counts.get(lab, 0) + 1
                removals.append({"line": k, "label": lab,
                                 "text": lines[k]["text"][:200]})
        text, _all_frags, p0, p1 = S.assemble_text(lines, kept)
        fragments = []
        for g in group_fragments(kept):
            ft, _, gp0, gp1 = S.assemble_text(lines, g)
            fragments.append({"first_line": g[0], "last_line": g[-1],
                              "page_start": gp0, "page_end": gp1, "text": ft})
        notes = [lines[k]["text"].strip() for k in kept
                 if S.REP_RE.search(lines[k]["text"])]
        notes += mk.get("footnote_texts", [])
        if p0 is not None and p1 is not None and p1 != p0:
            page_spanning += 1
        sections.append({
            "number": mk["number"], "title": mk["title"],
            "chapter": mk["chapter"], "marker_line": mk["line"],
            "start": mk["start"], "end": mk["end"],
            "page_start": p0, "page_end": p1,
            "text": text, "fragments": fragments, "removals": removals,
            "amendment_notes": notes,
        })
        kept_plus_removed = len(kept) + len(removals)
        if kept_plus_removed != mk["end"] - mk["start"]:
            unlabeled += (mk["end"] - mk["start"]) - kept_plus_removed
    return {
        "sections": sections,
        "label_counts": label_counts,
        "unlabeled_removals": unlabeled,
        "scan_stats": scan["stats"],
        "unknowns": scan["unknowns"],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--act", required=True, help="act_id from act_registry.yaml")
    args = ap.parse_args()

    V.ensure_dirs()
    act_id = args.act
    V.tee(f"{act_id}_step3_clean")
    print("seeds used: none (step3 has no randomness)", flush=True)
    registry = V.load_registry()
    act = next((a for a in registry if a["act_id"] == act_id), None)
    if act is None:
        print(f"FATAL: act_id {act_id!r} not in {V.REGISTRY_PATH}", flush=True)
        return 2
    src = V.SOURCES / act["source_file"].split("/")[-1]
    if not src.exists():
        print(f"FATAL: source missing: {src}", flush=True)
        return 2
    print("\n" + "=" * 76, flush=True)
    print(f"STEP 3 CLEAN {act_id}  ({act['act_name']})  file={src.name}",
          flush=True)
    print("=" * 76, flush=True)

    doc = V.fitz.open(str(src))
    result = clean_sections(doc, start_page=V.body_scan_start(act_id))
    doc.close()

    secs = result["sections"]
    print(f"sections cleaned: {len(secs)}", flush=True)
    st = result["scan_stats"]
    print(f"A7b footnotes: total={st.get('footnotes_total')} "
          f"attached={st.get('footnotes_attached')} "
          f"unattached={st.get('footnotes_unattached')} "
          f"ambiguous={st.get('footnotes_ambiguous')}", flush=True)
    print(f"A7b scope boundaries: {st.get('scope_boundaries')}  "
          f"A7c chapter notes: {st.get('chapter_notes')}", flush=True)
    print(f"removals by label: {result['label_counts']}", flush=True)
    print(f"unlabeled removals (must be 0): {result['unlabeled_removals']}",
          flush=True)
    empty = [s["number"] for s in secs if not s["text"].strip()]
    print(f"empty texts (must be []): {empty}", flush=True)
    spans = [s["number"] for s in secs
             if s["page_start"] is not None and s["page_end"] is not None
             and s["page_start"] != s["page_end"]]
    print(f"page-spanning sections (A1, text resumes): {len(spans)} "
          f"{spans[:10]}{'...' if len(spans) > 10 else ''}", flush=True)
    multi = [s["number"] for s in secs if len(s["fragments"]) > 1]
    print(f"sections with >1 fragment (join points): {len(multi)} "
          f"{multi[:10]}{'...' if len(multi) > 10 else ''}", flush=True)
    maxlen = max((len(s["text"]) for s in secs), default=0)
    print(f"longest cleaned text: {maxlen} chars", flush=True)
    print("first section preview:", flush=True)
    if secs:
        s0 = secs[0]
        print(f"  {s0['number']} p{s0['page_start']}-{s0['page_end']}: "
              f"{s0['text'][:160]!r}", flush=True)

    out = {"act_id": act_id}
    out.update(result)
    V.write_json(V.RESULTS / f"{act_id}_clean.json", out)
    print(f"\nCHECKPOINT step3_clean done -> "
          f"results/{act_id}_clean.json", flush=True)
    print("[exit] 0", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
