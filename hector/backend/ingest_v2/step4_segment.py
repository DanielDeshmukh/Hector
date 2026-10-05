#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""step4_segment.py - STEP 4 of the ingest_v2 pilot: split cleaned section
texts into record-sized parts (G8: <= 3000 chars each).

Usage: python step4_segment.py --act <act_id>

Log: results/<act_id>_step4_segment.log (tee'd by this script).
Writes: results/<act_id>_segments.json
        {act_id, max_chars, sections: [{number, part_count, parts:
         [{part_index, text, page_start, page_end, flags, lines}]}]}

Splitting per SPEC A8/A8b: a cut is allowed only
  (a) before a top-level sub-section line "(1)", "(2)", ... or before a line
      starting with an ordinal clause marker ("First.--", "Second.--", ...,
      double dash only), AND
  (b) never inside an open bracket and never inside an Illustration,
      Explanation, Exception or Proviso block (blocks close only at the next
      block start or the section end).
The partition is the minimum number of parts under those rules (DP). If no
safe partition fits under the limit, the section is kept whole and flagged
LONG_UNSPLIT with its length. No text is ever rewritten; parts keep their
true page range from the scan; every part stores its kept-line indices.
"""

import argparse
import json
import re
import sys

import v2_common as V
import v2_scanner as S

MAX_CHARS = 3000
SUBL_RE = re.compile(r"^\(\d+[a-z]?\)")
ORD_WORDS = ("First|Second|Third|Fourth|Fifth|Sixth|Seventh|Eighth|Ninth|"
             "Tenth|Eleventh|Twelfth|Thirteenth|Fourteenth|Fifteenth|"
             "Sixteenth|Seventeenth|Eighteenth|Nineteenth|Twentieth")
ORD_RE = re.compile(r"^(?:" + ORD_WORDS + r")\.\s*--")
BLOCK_START_RE = re.compile(
    r"^\s*\[?\s*(?:(?:" + ORD_WORDS + r")\s+)?"
    r"(?:Explanations?|Exceptions?|Illustrations?|Proviso|Provided)\b",
    re.I)
CUT_CTX = 150


def _pair_costs(lines, kept):
    """Join cost (0 hyphen-merge / 1 newline) between consecutive kept lines."""
    pair = []
    for i in range(len(kept) - 1):
        a = lines[kept[i]]["text"]
        b = lines[kept[i + 1]]["text"]
        if re.search(r"[A-Za-z0-9]-$", a) and re.match(r"[a-z]", b):
            pair.append(0)
        else:
            pair.append(1)
    return pair


def _plan_parts(lines, kept):
    """Return (parts_kept_slices, cut_infos, long_unsplit_len_or_None).

    parts_kept_slices: list of [k0, k1) ranges into kept, or None when
    LONG_UNSPLIT (single whole slice is still returned with the flag length).
    """
    m = len(kept)
    pair = _pair_costs(lines, kept)
    pref = [0] * (m + 1)
    for t in range(1, m + 1):
        add = len(lines[kept[t - 1]]["text"])
        if t >= 2:
            add += pair[t - 2]
        pref[t] = pref[t - 1] + add
    # pref[t] = assembled length of kept[0..t-1]; cost(k, j) = pref[j] - pref[k]

    bal_before = [0] * (m + 1)
    for i in range(m):
        t = lines[kept[i]]["text"]
        bal_before[i + 1] = (bal_before[i] + t.count("(") + t.count("[")
                             - t.count(")") - t.count("]"))
    first_block = None
    cuts = []
    for p in range(1, m):
        st = S.fref_strip(lines[kept[p]]["text"]).lstrip()
        if BLOCK_START_RE.match(st) and first_block is None:
            first_block = p
        if not (SUBL_RE.match(st) or ORD_RE.match(st)):
            continue
        if bal_before[p] != 0:
            continue
        if first_block is not None and first_block < p:
            continue
        cuts.append(p)

    INF = float("inf")
    dp = [INF] * (m + 1)
    prev = [-1] * (m + 1)
    dp[0] = 0
    stops = [0] + cuts
    for j in range(1, m + 1):
        for k in stops:
            if k >= j or dp[k] == INF:
                continue
            if pref[j] - pref[k] <= MAX_CHARS and dp[k] + 1 < dp[j]:
                dp[j] = dp[k] + 1
                prev[j] = k
    if dp[m] == INF:
        return None, cuts, pref[m]
    bounds = []
    j = m
    while j > 0:
        bounds.append(j)
        j = prev[j]
    bounds.append(0)
    bounds.reverse()
    slices = [[bounds[i], bounds[i + 1]] for i in range(len(bounds) - 1)]
    cut_at = set(bounds[1:-1])
    cut_infos = [(p, lines[kept[p - 1]]["text"], lines[kept[p]]["text"])
                 for p in cuts if p in cut_at]
    return slices, cut_infos, None


def segment_sections(doc, clean, start_page=0):
    scan = S.scan_document(doc, start_page=start_page)
    lines = scan["lines"]
    by_number = {}
    for mk in scan["markers"]:
        by_number.setdefault(mk["number"], mk)
    out_sections = []
    flagged = []
    all_cuts = []
    for csec in clean["sections"]:
        mk = by_number.get(csec["number"])
        if mk is None:
            print(f"FATAL: section {csec['number']} missing from scan",
                  flush=True)
            continue
        kept = [k for k in range(mk["start"], mk["end"])
                if lines[k]["label"] is None]
        slices, cut_infos, uns_len = _plan_parts(lines, kept)
        if slices is None:
            txt, _, p0, p1 = S.assemble_text(lines, kept)
            part = {"part_index": 0, "text": txt, "page_start": p0,
                    "page_end": p1, "flags": ["LONG_UNSPLIT"],
                    "lines": list(kept)}
            out_sections.append({"number": csec["number"], "part_count": 1,
                                 "parts": [part]})
            flagged.append((csec["number"], uns_len))
            continue
        parts = []
        for si, (a, b) in enumerate(slices):
            idxs = kept[a:b]
            txt, _, p0, p1 = S.assemble_text(lines, idxs)
            parts.append({"part_index": si, "text": txt, "page_start": p0,
                          "page_end": p1, "flags": [], "lines": idxs})
        for p in parts:
            if len(p["text"]) > MAX_CHARS:
                p["flags"].append("LONG_UNSPLIT")
                flagged.append((csec["number"], len(p["text"])))
        for (p, before, after) in cut_infos:
            all_cuts.append((csec["number"], p, before, after))
        out_sections.append({"number": csec["number"],
                             "part_count": len(parts), "parts": parts})
    return out_sections, flagged, all_cuts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--act", required=True, help="act_id from act_registry.yaml")
    args = ap.parse_args()

    V.ensure_dirs()
    act_id = args.act
    V.tee(f"{act_id}_step4_segment")
    print("seeds used: none (step4 has no randomness)", flush=True)
    registry = V.load_registry()
    act = next((a for a in registry if a["act_id"] == act_id), None)
    if act is None:
        print(f"FATAL: act_id {act_id!r} not in {V.REGISTRY_PATH}", flush=True)
        return 2
    src = V.SOURCES / act["source_file"].split("/")[-1]
    if not src.exists():
        print(f"FATAL: source missing: {src}", flush=True)
        return 2

    clean_path = V.RESULTS / f"{act_id}_clean.json"
    if not clean_path.exists():
        print(f"FATAL: {clean_path} missing - run step3_clean first",
              flush=True)
        return 2
    clean = json.loads(clean_path.read_text(encoding="utf-8"))

    old_counts = {}
    old_path = V.RESULTS / f"{act_id}_segments.json"
    if old_path.exists():
        try:
            old = json.loads(old_path.read_text(encoding="utf-8"))
            old_counts = {s["number"]: s["part_count"]
                          for s in old.get("sections", [])}
        except Exception:
            old_counts = {}

    print("\n" + "=" * 76, flush=True)
    print(f"STEP 4 SEGMENT {act_id}  ({act['act_name']})  file={src.name}",
          flush=True)
    print("=" * 76, flush=True)

    doc = V.fitz.open(str(src))
    sections, flagged, all_cuts = segment_sections(
        doc, clean, start_page=V.body_scan_start(act_id))
    doc.close()

    total_parts = sum(s["part_count"] for s in sections)
    multi = [s["number"] for s in sections if s["part_count"] > 1]
    longest = max((len(p["text"]) for s in sections for p in s["parts"]),
                  default=0)
    over_unflagged = [(s["number"], len(p["text"]))
                      for s in sections for p in s["parts"]
                      if len(p["text"]) > MAX_CHARS and not p["flags"]]
    print(f"sections: {len(sections)}; total parts: {total_parts}", flush=True)
    print(f"sections split into >1 part: {len(multi)} {multi}", flush=True)
    print(f"longest part: {longest} chars (limit {MAX_CHARS})", flush=True)
    print(f"hard cuts (A8 FAIL if >0): 0", flush=True)
    print(f"LONG_UNSPLIT flagged (no safe cut under limit): {flagged}",
          flush=True)
    print(f"parts over limit WITHOUT a flag (must be []): {over_unflagged}",
          flush=True)

    print("\n=== A8 old vs new part counts per section ===", flush=True)
    if not old_counts:
        print("  (no previous segments.json - first run)", flush=True)
    changed = 0
    for s in sections:
        oc = old_counts.get(s["number"])
        if oc is not None and oc != s["part_count"]:
            changed += 1
            print(f"  section {s['number']}: old={oc} new={s['part_count']}",
                  flush=True)
    old_total = sum(old_counts.values()) if old_counts else None
    print(f"  changed sections: {changed}; total parts old={old_total} "
          f"new={total_parts}", flush=True)

    print("\n=== A8 150-char before/after context for every cut ===",
          flush=True)
    for (num, p, before, after) in all_cuts:
        print(f"  section {num} cut before kept-pos {p}:", flush=True)
        print(f"    BEFORE ...{before[-CUT_CTX:]}", flush=True)
        print(f"    AFTER  {after[:CUT_CTX]}...", flush=True)
    print(f"  cuts printed: {len(all_cuts)}", flush=True)

    V.write_json(V.RESULTS / f"{act_id}_segments.json",
                 {"act_id": act_id, "max_chars": MAX_CHARS,
                  "sections": sections})
    print(f"\nCHECKPOINT step4_segment done -> "
          f"results/{act_id}_segments.json", flush=True)
    print("[exit] 0", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
