#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""results/ipc_audit.py - READ-ONLY audit of the IPC pilot.

Does NOT modify the pipeline or any existing output. New files created by this
script: results/ipc_audit.log (tee) and results/visual/*.png only.

Usage (external cmd window): python -u ingest_v2/results/ipc_audit.py
"""

import json
import random
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))  # ingest_v2/ for v2_common/v2_scanner

import v2_common as V          # noqa: E402
import v2_scanner as S         # noqa: E402

ACT = "ipc-1860"
FOOT_SEED = 20261013
CTX = 150


def load(name):
    return json.loads((V.RESULTS / name).read_text(encoding="utf-8"))


def hdr(title):
    print("\n" + "=" * 76, flush=True)
    print(title, flush=True)
    print("=" * 76, flush=True)


def section1_lettered(records):
    hdr("1. LETTERED SECTIONS (number contains a letter)")
    parents = {}
    for r in records:
        if re.search(r"[A-Za-z]", r["number"]):
            parents.setdefault(r["number"], []).append(r)
    ordered = sorted(parents.items(),
                     key=lambda kv: (len(kv[1][0]["number"]), kv[1][0]["id"]))
    count = 0
    for num, recs in ordered:
        count += 1
        r0 = next(r for r in recs if r["part_index"] == 0)
        ids = ", ".join(r["id"] for r in sorted(recs, key=lambda x: x["part_index"]))
        print(f"  {count:>2}. number={num!r} title={r0['title']!r} "
              f"page={r0['page_start']} record_id={ids}", flush=True)
    print(f"COUNT: {count} lettered sections", flush=True)


def section2_fields(records):
    hdr("2. FIELD COVERAGE (over all records)")
    n = len(records)
    null_title = [r["id"] for r in records if r["title"] is None]
    null_chapter = [r["id"] for r in records if r["chapter"] is None]
    st = {}
    rows = []
    for key in ("has_proviso", "has_explanation", "has_exception",
                "has_illustration"):
        c = sum(1 for r in records if r[key])
        rows.append((key, c))
    for r in records:
        st[r["status"]] = st.get(r["status"], 0) + 1
    print(f"records: {n}", flush=True)
    print(f"null title: {len(null_title)} -> {null_title}", flush=True)
    print(f"null chapter: {len(null_chapter)} -> {null_chapter}", flush=True)
    for key, c in rows:
        print(f"{key}: {c}", flush=True)
    print(f"status counts: {st}", flush=True)


STRUCT_START = re.compile(
    r"(?m)^[ \t]*(Explanation|Exception|Illustration)s?[.\s]|"
    r"\bProvided (further )?that\b")


def section3_splits(records, segs, clean):
    hdr("3. SPLIT SECTIONS (parts > 1)")
    by_parent = {}
    for r in records:
        by_parent.setdefault(r["number"], []).append(r)
    extra = 0
    total_cuts = 0
    inside_hits = []
    separate_hits = []
    for s in segs["sections"]:
        if s["part_count"] <= 1:
            continue
        num = s["number"]
        extra += s["part_count"] - 1
        recs = sorted((r for r in records if r["number"] == num),
                      key=lambda r: r["part_index"])
        csec = next(c for c in clean["sections"] if c["number"] == num)
        parts = s["parts"]
        sizes = [len(p["text"]) for p in parts]
        joined = "\n".join(p["text"] for p in parts)
        ok = (joined == csec["text"])
        print(f"\n  section {num}: parts={s['part_count']} sizes={sizes} "
              f"reconstruct==section_text: {ok}", flush=True)
        for r in recs:
            print(f"    part {r['part_index']}: id={r['id']} "
                  f"chars={len(r['text'])} pages {r['page_start']}-"
                  f"{r['page_end']}", flush=True)
        if not ok:
            print(f"    !! reconstruction MISMATCH (len {len(joined)} vs "
                  f"{len(csec['text'])}) - contexts below use the joined "
                  f"parts", flush=True)
        ref = joined if not ok else csec["text"]
        cut = 0
        for p in parts[:-1]:
            cut += len(p["text"])
            total_cuts += 1
            before = ref[max(0, cut - CTX):cut]
            after = ref[cut:cut + CTX]
            # analysis
            starts = [(m.start(), m.group(0).strip()[:40])
                      for m in STRUCT_START.finditer(ref)]
            last_before = None
            first_after = None
            for pos, lab in starts:
                if pos <= cut:
                    last_before = (pos, lab)
                elif first_after is None:
                    first_after = (pos, lab)
            last_txt = ref[:cut].rstrip()[-1:]
            terminal = last_txt in ".;:!?)]\"'"
            d_after = (first_after[0] - cut) if first_after else None
            d_before = (cut - last_before[0]) if last_before else None
            parens_unclosed = ref[:cut].count("(") - ref[:cut].count(")")
            brackets_unclosed = ref[:cut].count("[") - ref[:cut].count("]")
            quote_odd = (ref[:cut].count('"') % 2 == 1)
            flags = []
            if first_after is not None and d_after <= 40:
                flags.append(f"SEPARATES_BLOCK(start '{first_after[1]}' "
                             f"{d_after}ch after cut)")
                separate_hits.append((num, cut, first_after[1]))
            if last_before is not None and not terminal and d_before <= 800:
                flags.append(f"LIKELY_INSIDE_BLOCK(last start "
                             f"'{last_before[1]}' {d_before}ch before cut, "
                             f"cut not at sentence end)")
                inside_hits.append((num, cut, last_before[1]))
            if parens_unclosed or brackets_unclosed or quote_odd:
                flags.append(f"UNBALANCED_AT_CUT(parens_unclosed="
                             f"{parens_unclosed}, brackets_unclosed="
                             f"{brackets_unclosed}, quote_odd={quote_odd})")
            print(f"    cut at char {cut} (between part boundaries)", flush=True)
            print(f"      before[{CTX}]: ...{before!r}", flush=True)
            print(f"      after [{CTX}]: {after!r}...", flush=True)
            print(f"      structural markers: last before = "
                  f"{last_before}, first after = {first_after}", flush=True)
            print(f"      flags: {flags or ['none']}", flush=True)
    print(f"\n  SUMMARY: sections split=10, extra parts={extra} "
          f"(expected 13), cuts examined={total_cuts}", flush=True)
    print(f"  cuts flagged LIKELY_INSIDE a Proviso/Explanation/Exception/"
          f"Illustration: {len(inside_hits)} -> {inside_hits}", flush=True)
    print(f"  cuts flagged SEPARATING a block from surrounding text: "
          f"{len(separate_hits)} -> {separate_hits}", flush=True)
    print("  (flags are heuristics over the printed contexts - see section 9)",
          flush=True)


def ref_num_of(group_text):
    m = re.match(r"\s*(\d{1,3})\s*[.*]", group_text)
    return m.group(1) if m else None


def section4_footnotes(records, scan, markers):
    hdr("4. FOOTNOTES (attachment audit, seed %d)" % FOOT_SEED)
    print("pipeline fact: v2_scanner.py attaches each footnote group "
          "positionally (owner = last accepted marker at group start, "
          "v2_scanner.py:201); there is NO reference-marker matching in the "
          "pipeline. This audit re-classifies the 80 groups independently:",
          flush=True)
    print("  by_reference = footnote number N has an inline ref N* in the "
          "OWNER section text; fallback = positional only; ambiguous = "
          "unparseable number OR ref for N exists in another section but not "
          "in owner", flush=True)
    by_num_owner = {}
    for r in records:
        by_num_owner.setdefault(r["number"], []).append(r)
    section_text = {}
    for num, recs in by_num_owner.items():
        recs = sorted(recs, key=lambda r: r["part_index"])
        section_text[num] = "\n".join(r["text"] for r in recs)
    owner_num = {m["id"]: m["number"] for m in markers}
    groups = scan["groups"]
    lines = scan["lines"]
    counts = {"by_reference": 0, "fallback": 0, "ambiguous": 0}
    rows = []
    for g in groups:
        text = "\n".join(lines[gi]["text"] for gi in g["members"])
        num = ref_num_of(text)
        owner = owner_num.get(g["owner"])
        cls = None
        matched = None
        reason = None
        if num is None:
            cls = "ambiguous"
            reason = "number not parseable from first line"
        else:
            pat = re.compile(rf"(?<!\d){num}\s*\*+|(?<!\d)\[{num}\]")
            own = section_text.get(owner, "")
            mm = pat.search(own)
            if mm:
                cls = "by_reference"
                s0 = max(0, mm.start() - 30)
                matched = own[s0:mm.end() + 30]
            else:
                elsewhere = None
                for n2, t2 in section_text.items():
                    if n2 != owner and pat.search(t2):
                        elsewhere = n2
                        break
                if elsewhere is not None:
                    cls = "ambiguous"
                    reason = (f"no ref in owner {owner}; ref for {num} found "
                              f"in section {elsewhere}")
                else:
                    cls = "fallback"
                    reason = "positional attach; no inline ref anywhere"
        counts[cls] += 1
        rows.append((cls, num, owner, text, matched, reason))
    print(f"\n  TOTAL groups: {len(groups)}", flush=True)
    print(f"  attached by reference marker: {counts['by_reference']}",
          flush=True)
    print(f"  attached by fallback rule (positional only): "
          f"{counts['fallback']}", flush=True)
    print(f"  ambiguous: {counts['ambiguous']}", flush=True)
    rng = random.Random(FOOT_SEED)
    sample = rng.sample(rows, 15)
    print(f"\n  15 RANDOM ATTACHMENTS (seed {FOOT_SEED}):", flush=True)
    for i, (cls, num, owner, text, matched, reason) in enumerate(sample, 1):
        rid = f"{ACT}:s:{(owner or '?').lower()}"
        print(f"  {i:>2}. class={cls} number={num} owner={owner} "
              f"record_id={rid}", flush=True)
        print(f"      footnote text: {text[:300]!r}"
              f"{'...' if len(text) > 300 else ''}", flush=True)
        if matched:
            print(f"      matched marker in section text: {matched!r}",
                  flush=True)
        else:
            print(f"      matched marker: (none) - {reason}", flush=True)


def full_record(r, verify_embed=True):
    print(f"    id={r['id']} number={r['number']!r} title={r['title']!r} "
          f"chapter={r['chapter']!r}", flush=True)
    print(f"    hierarchy_path={r['hierarchy_path']!r} pages "
          f"{r['page_start']}-{r['page_end']} status={r['status']} "
          f"repealed_on={r['repealed_on']!r} replaced_by={r['replaced_by']!r}",
          flush=True)
    print(f"    has: proviso={r['has_proviso']} "
          f"explanation={r['has_explanation']} exception={r['has_exception']} "
          f"illustration={r['has_illustration']}", flush=True)
    print(f"    parts {r['part_index'] + 1}/{r['part_count']} "
          f"source_file={r['source_file']} source_type={r['source_type']} "
          f"unit_type={r['unit_type']} act={r['act_short']} "
          f"parent_id={r['parent_id']}", flush=True)
    print(f"    amendment_notes ({len(r['amendment_notes'])}):", flush=True)
    for a in r["amendment_notes"]:
        print(f"      - {a[:160]}{'...' if len(a) > 160 else ''}", flush=True)
    print(f"    content_hash={r['content_hash']}", flush=True)
    hdr_line = r["embedding_text"].split("\n", 1)[0]
    if verify_embed:
        ok = r["embedding_text"] == hdr_line + "\n" + r["text"]
        print(f"    embedding_text header: {hdr_line!r} "
              f"(body==text: {ok})", flush=True)
    print(f"    --- text ({len(r['text'])} chars) ---", flush=True)
    print(r["text"], flush=True)
    print(f"    --- end text ---", flush=True)


def section5_omitted(records):
    hdr("5. OMITTED RECORDS (status=omitted, A3 R-form) - ALL IN FULL")
    om = [r for r in records if r["status"] == "omitted"]
    print(f"count: {len(om)}", flush=True)
    for r in om:
        full_record(r)


def section6_whole(records):
    hdr("6. WHOLE RECORDS - full text and metadata")
    by_num = {}
    for r in records:
        by_num.setdefault(r["number"], []).append(r)
    picks = []
    for num in ["302", "300", "304A", "124A", "376", "498A", "34"]:
        if num in by_num:
            picks.append((f"section {num}", num))
        else:
            print(f"section {num}: DOES NOT EXIST in records", flush=True)
    if "376AB" in by_num:
        picks.append(("section 376AB", "376AB"))
    else:
        print("section 376AB: DOES NOT EXIST in records (checked)", flush=True)
    first_ill = next((r for r in records if r["has_illustration"]), None)
    first_exc = next((r for r in records if r["has_exception"]), None)
    longest = max(records, key=lambda r: len(r["text"]))
    extra = []
    if first_ill:
        extra.append(("first has_illustration", first_ill))
    if first_exc:
        extra.append(("first has_exception", first_exc))
    extra.append(("longest record", longest))
    shown_ids = set()
    for label, num in picks:
        print(f"\n>>> {label}", flush=True)
        for r in sorted(by_num[num], key=lambda x: x["part_index"]):
            if len(by_num[num]) > 1:
                print(f"  (split section: part {r['part_index'] + 1}/"
                      f"{r['part_count']})", flush=True)
            full_record(r)
            shown_ids.add(r["id"])
    for label, r in extra:
        print(f"\n>>> {label}: {r['id']}", flush=True)
        if r["id"] in shown_ids:
            print("  (already printed above - metadata only below)", flush=True)
            print(f"  number={r['number']} chars={len(r['text'])} pages "
                  f"{r['page_start']}-{r['page_end']} title={r['title']!r}",
                  flush=True)
        else:
            full_record(r)


def section7_visual(records, registry_act):
    hdr("7. VISUAL CHECK (PNG, 150 dpi, fitz get_pixmap)")
    vdir = V.RESULTS / "visual"
    vdir.mkdir(parents=True, exist_ok=True)
    by_num = {}
    for r in records:
        by_num.setdefault(r["number"], []).append(r)
    om = next(r for r in records if r["status"] == "omitted")
    split = next((r for r in records if r["part_count"] > 1
                  and r["number"] not in {"302", "300", "304A", "498A"}))
    targets = [("302", "302"), ("300", "300"), ("304A", "304A"),
               ("498A", "498A"), (om["number"], "omitted"),
               (split["number"], "split")]
    src = V.SOURCES / registry_act["source_file"].split("/")[-1]
    doc = V.fitz.open(str(src))
    seen = set()
    for number, why in targets:
        if number in seen:
            continue
        seen.add(number)
        rec = next(r for r in by_num[number] if r["part_index"] == 0)
        page = rec["page_start"]
        fname = f"ipc_{number}_p{page}.png"
        path = vdir / fname
        pix = doc[page - 1].get_pixmap(dpi=150)
        pix.save(str(path))
        print(f"\n{fname}  ({why}; {pix.width}x{pix.height}px, 150 dpi)",
              flush=True)
        print(f"  record id: {rec['id']}", flush=True)
        print(f"  --- record text ({len(rec['text'])} chars) ---", flush=True)
        print(rec["text"], flush=True)
        print(f"  --- end record text ---", flush=True)
    doc.close()
    print(f"\nPNGs written under results/visual/ ({len(seen)} files)",
          flush=True)


def section8_g6():
    hdr("8. G6 REFERENCE CHANGE")
    print("exact BEFORE (step6_validate.py main(), pre-fix):", flush=True)
    print("    raw_pages = [doc[i].get_text(\"text\") for i in range(n)]",
          flush=True)
    print("exact AFTER (current step6_validate.py):", flush=True)
    print("    # G6 raw reference: raw page text in the page's own line "
          "reading order", flush=True)
    print("    # (sort=True); default block-index order has a "
          "ghost-whitespace-block", flush=True)
    print("    # artifact documented in SPEC ASSUMPTIONS (see also "
          "diag_g6b.log).", flush=True)
    print("    raw_pages = [doc[i].get_text(\"text\", sort=True) for i in "
          "range(n)]", flush=True)
    print("note: the file is untracked in git (no history to diff); the "
          "before/after lines above are quoted exactly from the edit made in "
          "the pilot session.", flush=True)
    print("\nlog evidence (results/ipc-1860_diag_g6b.log):", flush=True)
    for name in ("ipc-1860_diag_g6b.log", "ipc-1860_diag_g6.log"):
        p = V.RESULTS / name
        if not p.exists():
            print(f"  MISSING {name}", flush=True)
            continue
        for ln in p.read_text(encoding="utf-8").splitlines():
            if ("windows" in ln and "%" in ln) or "missing windows total" in ln \
                    or ln.startswith("[default") or ln.startswith("[sort"):
                print(f"  {name}: {ln}", flush=True)
    spec = (V.INGEST / "SPEC.md").read_text(encoding="utf-8")
    print("\nSPEC ASSUMPTIONS lines (verbatim):", flush=True)
    in_block = False
    for ln in spec.splitlines():
        if ln.startswith("- G6 raw reference"):
            in_block = True
        elif in_block and ln.startswith("- "):
            break
        if in_block:
            print(f"  {ln}", flush=True)
    print("\n3 ghost-block examples with coordinates (default block order):",
          flush=True)
    registry = V.load_registry()
    act = next(a for a in registry if a["act_id"] == ACT)
    src = V.SOURCES / act["source_file"].split("/")[-1]
    doc = V.fitz.open(str(src))
    shown = 0
    for pno in (2, 8, 15):
        page = doc[pno - 1]
        blocks = [b for b in page.get_text("blocks") if len(b) >= 7
                  and b[6] == 0]
        for bi, b in enumerate(blocks):
            txt = str(b[4])
            ws_only = txt.strip() == "" and len(txt) > 3
            rule = bool(txt.strip()) and set(txt.strip()) <= set("-") \
                and len(txt.strip()) >= 5
            if (ws_only or rule) and shown < 3:
                shown += 1
                kind = "WHITESPACE-ONLY" if ws_only else "DASH-RULE"
                print(f"  example {shown}: page {pno}, block index {bi}, "
                      f"kind={kind}", flush=True)
                print(f"    bbox=({b[0]:.1f}, {b[1]:.1f}, {b[2]:.1f}, "
                      f"{b[3]:.1f}) text={txt[:60]!r}", flush=True)
        dflt = page.get_text("text")
        srtd = page.get_text("text", sort=True)
        if dflt != srtd:
            i1, i2 = dflt.find("---"), srtd.find("---")
            print(f"    page {pno}: dash-rule pos default={i1} "
                  f"sorted={i2}; strings differ: True", flush=True)
    if shown < 3:
        print(f"  (only {shown} whitespace/rule blocks found on pages "
              f"2/8/15; page 2 example verified in the session log "
              f"ipc-1860_diag_lines_15_40.log)", flush=True)
    doc.close()


def section9_limits():
    hdr("9. WHAT THIS AUDIT COULD NOT VERIFY")
    for i, t in enumerate([
        "Titles and section coverage cannot be cross-checked: the IPC PDF "
        "has no ToC, so G2 stays SEQUENCE_ONLY (a listing, not an external "
        "proof of completeness).",
        "Footnote attachment classes (by_reference / fallback / ambiguous) "
        "are this audit's operational re-classification using inline N* "
        "regexes; the pipeline itself attaches only positionally (owner = "
        "last marker). No ground truth for correct attachment exists.",
        "'Inside Proviso/Explanation/Exception/Illustration' and 'separates "
        "from text it modifies' flags for split cuts are heuristics "
        "(structural-start distances, sentence terminals, bracket/quote "
        "balance) printed next to full 150-char contexts; they need human "
        "confirmation, they are not a legal-structure parse.",
        "status=omitted comes from printed Rep./bracketed text patterns "
        "(R-form); not verified against official statute/repeal records. "
        "repealed_on/replaced_by come from act_registry.yaml (BNS mapping), "
        "not from the PDF.",
        "304A exists in this parse; 376AB does not. Not cross-checked "
        "against an official IPC section list (which itself varies by "
        "edition/amendment date).",
        "Verbatim proof is the G6 window method (60-char windows, >=99% "
        "required; achieved 100% against sorted raw text). It is not a "
        "formal character-for-character diff of every section against the "
        "Gazette original; the G6 reference change (default -> sort=True "
        "raw) was justified in-session but is still an interpretation of "
        "'RAW page text'.",
        "The PDF's fidelity to the official Gazette edition (OCR/digital "
        "origin, completeness of pages) was not verified.",
        "amendment_notes completeness: notes are exactly the footnotes "
        "positionally attached to each section; not checked against "
        "official amendment histories.",
        "G6 before/after code lines are quoted from session edit history "
        "(file is untracked; no git diff available).",
        "Visual PNGs are rendered from the source PDF at 150 dpi; this "
        "audit prints them but does not pixel-compare them with record "
        "text (spot-check only).",
        "embedding_text correctness is verified structurally "
        "(header + newline + text) only, not against an embedding run "
        "(no embeddings were computed - out of scope).",
        "No statement about Consumer Protection 2019: it was not "
        "inspected (paused at checkpoint 1).",
    ], 1):
        print(f"  {i}. {t}", flush=True)


def main():
    V.tee("ipc_audit")
    print("READ-ONLY AUDIT of IPC pilot - seeds used: footnote sample "
          f"{FOOT_SEED} (this audit only; pipeline seeds untouched)",
          flush=True)
    print("no pipeline file or existing output is modified by this script; "
          "new files: results/ipc_audit.log, results/visual/*.png",
          flush=True)
    records = [json.loads(ln) for ln in
               (V.OUTPUT / f"{ACT}.jsonl").read_text(encoding="utf-8")
               .splitlines() if ln]
    clean = load(f"{ACT}_clean.json")
    segs = load(f"{ACT}_segments.json")
    markers = load(f"{ACT}_markers.json")
    registry = V.load_registry()
    act = next(a for a in registry if a["act_id"] == ACT)

    section1_lettered(records)
    section2_fields(records)
    section3_splits(records, segs, clean)

    print("\nre-scanning document read-only for footnote groups ...",
          flush=True)
    doc = V.fitz.open(str(V.SOURCES / act["source_file"].split("/")[-1]))
    scan = S.scan_document(doc)
    doc.close()
    section4_footnotes(records, scan, markers)
    section5_omitted(records)
    section6_whole(records)
    section7_visual(records, act)
    section8_g6()
    section9_limits()
    print("\n[audit] done - [exit] 0", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
