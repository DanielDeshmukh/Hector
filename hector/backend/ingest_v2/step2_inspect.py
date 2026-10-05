#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""step2_inspect.py - STEP 2 of the ingest_v2 pilot: inspect a PDF, find the
ToC, extract the expected section list (the authority for segmentation).

Usage: python step2_inspect.py --act <act_id>

Log: results/<act_id>_step2_inspect.log (tee'd by this script).
Writes: results/<act_id>_expected.json      ([{number, title}])
        results/<act_id>_expected_meta.json ({expected_source, mode, ...})
        results/<act_id>_toc_meta.json      (header page + ToC page range)
        results/<act_id>_markers.json       (scan markers, forms, pages)
        results/<act_id>_numlines.json      (A4 classification log)
        results/block_order_counter.json    (global cross-act counter)

No ToC found -> STOP with NO_TOC, unless the registry entry has
sequence_only_fallback: true (user-authorized SEQUENCE_ONLY mode: the expected
list is then derived from the body's own "N. Title.--" markers in strictly
increasing order, and reported as SEQUENCE_ONLY everywhere - never as PASS).
"""

import argparse
import random
import re
import sys

import v2_common as V
import v2_scanner as S

SEEDS = "seeds used: none (step2 has no randomness, except seed 20261012 for the A4 footnote-classification sample)"
DASH_MARK_RE = re.compile(r"\.\s*(?:--|-|\u2013|\u2014)")
ANCHOR_NOTE = ("IPC highest plain section should be 511 (user-supplied external "
               "anchor, NOT the authority)")


def raw_text(page):
    return page.get_text("text")


def fitz_open(path):
    return V.fitz.open(str(path))


def is_continuation(s, entries):
    if not entries:
        return False
    if V.ENTRY_RE.match(s):
        return False
    if re.match(r"^(CHAPTER|PART|SCHEDULE|SUB-SCHEDULE|APPENDIX|PREAMBLE|"
                r"ARRANGEMENT|CONTENTS|SECTIONS|FIRST SCHEDULE|SECOND SCHEDULE|"
                r"THIRD SCHEDULE|FOURTH SCHEDULE|FIFTH SCHEDULE|SIXTH SCHEDULE|"
                r"SEVENTH SCHEDULE|EIGHTH SCHEDULE|NINTH SCHEDULE|"
                r"TENTH SCHEDULE|THE SCHEDULE)\b", s, re.I):
        return False
    if s.isupper() and len(s) > 3:
        return False
    if s.startswith("("):
        return False
    if len(s) > 130:
        return False
    if not re.search(r"[A-Za-z]", s):
        return False
    return True


HEADER_RE = re.compile(
    r"ARRANGEMENT\s+OF\s+(THE\s+)?SECTIONS|TABLE\s+OF\s+CONTENTS|"
    r"^\s*CONTENTS\s*$", re.I | re.M)
# number-only ToC line (e.g. "1." on its own line, title on the next)
BARE_NUM_RE = re.compile(r"^(\d{1,3}[A-Z]*)\.\s*$")


def find_header_page(doc):
    for i in range(min(15, len(doc))):
        if HEADER_RE.search(raw_text(doc[i])):
            return i
    return None


def header_diagnostics(doc):
    """Evidence printed when no header was found - never used to guess."""
    print("\nHEADER DIAGNOSTICS (first 15 pages) - lines containing "
          "arrangement/contents/sections/index:", flush=True)
    for i in range(min(15, len(doc))):
        hits = [l.strip() for l in raw_text(doc[i]).splitlines()
                if re.search(r"arrangement|contents|sections|index", l, re.I)]
        if hits:
            print(f"  p{i + 1}:", flush=True)
            for h in hits[:5]:
                print(f"      {h[:110]!r}", flush=True)
    print("entry-density per page 1..15 (page, lines, entries, density):",
          flush=True)
    for i in range(min(15, len(doc))):
        _, lines = V.page_lines(doc[i])
        texts = [l["text"].strip() for l in lines if l["text"].strip()]
        ents = sum(1 for s in texts
                   if V.ENTRY_RE.match(s) and not V.FOOT_RE.match(s))
        print(f"  p{i + 1}: lines={len(texts):4d} entries={ents:4d} "
              f"density={ents / max(1, len(texts)):.2f}", flush=True)
    print(f"\nFULL-DOCUMENT scan of all {len(doc)} pages for a ToC header "
          f"(word-boundary match, evidence only - not used to guess):",
          flush=True)
    hits_all = 0
    for i in range(len(doc)):
        for ln in raw_text(doc[i]).splitlines():
            if re.search(r"\bARRANGEMENT\b|\bCONTENTS\b|TABLE OF CONTENTS",
                         ln, re.I):
                hits_all += 1
                print(f"  p{i + 1}: {ln.strip()[:110]!r}", flush=True)
    if hits_all == 0:
        print("  no page in the whole document contains 'ARRANGEMENT' or "
              "'CONTENTS'.", flush=True)


def collect_entries(doc, header_page):
    entries = []
    pages_used = []
    page_log = []
    started = False
    max_base = None
    # No fixed page window here: the ToC length is a property of the book.
    # BNSS's ARRANGEMENT OF SECTIONS runs pages 3..17 (15 pages, sections
    # 1..531); the previous `header_page + 14` cut it at page 16, so
    # expected_count came out 498 while the body held 531 (G2 anchor_ok
    # false, and G6 because the missing ToC tail left the last record
    # absorbing the schedules). The termination is decided by the
    # data-driven checks below: density < 0.25 marks the first body page,
    # a backward numbering step marks a restart, and 700 entries caps the
    # pathological case.
    for i in range(header_page, len(doc)):
        mode, lines = V.page_lines(doc[i])
        texts = [l["text"].strip() for l in lines if l["text"].strip()]
        mark = len(entries)
        cont = False
        for s in texts:
            m = V.ENTRY_RE.match(s)
            bare = BARE_NUM_RE.match(s)
            if m and not V.FOOT_RE.match(s):
                title = re.sub(r"\.{2,}\s*\d{1,3}\s*$", "", m.group(2)).strip()
                entries.append([m.group(1), title])
                cont = True
            elif bare and not V.FOOT_RE.match(s):
                entries.append([bare.group(1), ""])
                cont = True
            elif cont and is_continuation(s, entries):
                entries[-1][1] = (entries[-1][1] + " " + s).strip()
            else:
                cont = False
        n_entries = len(entries) - mark
        density = n_entries / max(1, len(texts))
        page_log.append((i + 1, mode, len(texts), n_entries, density))
        if not started and density >= 0.25:
            started = True
        page_bases = [int(re.sub(r"[A-Za-z]+", "", e[0]))
                      for e in entries[mark:]]
        if started and page_bases and max_base is not None \
                and min(page_bases) < max_base:
            # the arrangement lists numbers in one increasing pass; a page
            # whose entry numbers go BACKWARD restarts (body page) -> stop
            # and drop that page's entries (body is scanned separately)
            del entries[mark:]
            break
        if started and density < 0.25:
            # first page at/after start below threshold is the body page:
            # its entries were already collected above - take them back out
            del entries[mark:]
            break
        if page_bases:
            mb = max(page_bases)
            max_base = mb if max_base is None else max(max_base, mb)
        if started:
            pages_used.append(i + 1)
        if started and len(entries) >= 700:
            break
    return entries, pages_used, page_log, started


def gaps_of(numbers):
    ints = sorted({int(re.sub(r"[A-Za-z]+", "", n)) for n in numbers})
    if not ints:
        return []
    lo, hi = ints[0], ints[-1]
    have = set(ints)
    return [n for n in range(lo, hi + 1) if n not in have]


# ---------------------------------------------------------- SEQUENCE_ONLY
def a4_report(act_id, scan, seed=20261012):
    """A4 classification log: counts, 20 sampled footnotes, all UNKNOWNs."""
    st = scan["stats"]
    cls = st["classes"]
    print("\nA4 CLASSIFICATION LOG (every number-and-dot/head line):", flush=True)
    print(f"  counts per class: {cls}", flush=True)
    print(f"  labels on removed lines: {st['labels']}", flush=True)
    print(f"  unlabeled removals (must be 0): {st['unlabeled_removed']}",
          flush=True)
    pool = scan["footnote_pool"]
    rng = random.Random(seed)
    sample = rng.sample(pool, min(20, len(pool)))
    lines = scan["lines"]
    print(f"  20 sampled footnote classifications (seed {seed} "
          f"from {len(pool)}):", flush=True)
    for li in sample:
        ln = lines[li]
        print(f"    p{ln['page'] + 1} line {li}: {ln['text'][:90]!r} "
              f"-> {ln['cls']}", flush=True)
    un = scan["unknowns"]
    print(f"  UNKNOWN lines: {len(un)}", flush=True)
    for u in un:
        print(f"    p{u['page']} line {u['line']}: {u['text']!r}", flush=True)
        for c in u["context"]:
            print(f"        ctx: {c!r}", flush=True)
    V.write_json(V.RESULTS / f"{act_id}_numlines.json", {
        "seed": seed,
        "counts": cls,
        "labels": st["labels"],
        "unlabeled_removed": st["unlabeled_removed"],
        "unknowns": un,
        "footnote_sample": [
            {"line": li, "page": lines[li]["page"] + 1,
             "text": lines[li]["text"][:160], "cls": lines[li]["cls"]}
            for li in sample],
        "lines": [
            {"line": ln["i"], "page": ln["page"] + 1,
             "text": ln["text"][:160], "cls": ln["cls"],
             "label": ln["label"]}
            for ln in lines
            if S.NUMDOT_RE.match(ln["text"]) or S.NUMHEAD_RE.match(ln["text"])],
    })


def a5_report(st):
    print("\nA5 LOOKAHEAD:", flush=True)
    print(f"  LOOKAHEAD_LINES constant = {st['lookahead_constant']}; "
          f"longest actually used = {st['max_lookahead_used']}", flush=True)
    far = st["restated_more_than_2_pages"]
    print(f"  sections whose restated marker is >2 pages after margin: "
          f"{len(far)} {far}", flush=True)


def print_gap_context(scan, entries, gaps, max_gaps=8):
    """For each gap: text around where the missing section should be."""
    lines = scan["lines"]
    for g in gaps[:max_gaps]:
        prev = None
        nxt = None
        for e in entries:
            if e["base"] < g and (prev is None or e["base"] > prev["base"]):
                prev = e
            if e["base"] > g and (nxt is None or e["base"] < nxt["base"]):
                nxt = e
        print(f"\n  GAP {g}: between "
              f"{prev['number'] if prev else '-'} "
              f"(p{prev['page_1based'] if prev else '?'}) "
              f"and {nxt['number'] if nxt else '-'} "
              f"(p{nxt['page_1based'] if nxt else '?'}) - text around there:",
              flush=True)
        if prev:
            start = prev["line"]
            for k in range(start, min(start + 8, len(lines))):
                print(f"      p{lines[k]['page'] + 1}: "
                      f"{lines[k]['text'].strip()[:100]!r}", flush=True)
        else:
            print("      (no preceding marker)", flush=True)
        if nxt:
            s2 = max(0, nxt["line"] - 4)
            for k in range(s2, min(nxt["line"] + 4, len(lines))):
                print(f"      p{lines[k]['page'] + 1}: "
                      f"{lines[k]['text'].strip()[:100]!r}", flush=True)
    if len(gaps) > max_gaps:
        print(f"\n  ({len(gaps) - max_gaps} more gaps not shown here; full list "
              f"in results - see G2 in step6)", flush=True)


# ------------------------------------------------------ block-order counter
def update_block_order_counter(act_id, n_pages, diff_pages, modes, hyp):
    path = V.RESULTS / "block_order_counter.json"
    try:
        data = json_load(path)
    except Exception:
        data = {"acts": {}, "totals": {"pages": 0, "diff_pages": 0}}
    data["acts"][act_id] = {
        "pages": n_pages,
        "diff_page_count": len(diff_pages),
        "diff_pages": diff_pages,
        "modes": modes,
        "hyphen_line_breaks": hyp,
    }
    tot = {"pages": 0, "diff_pages": 0}
    for a in data["acts"].values():
        tot["pages"] += a["pages"]
        tot["diff_pages"] += a["diff_page_count"]
    data["totals"] = tot
    V.write_json(path, data)
    return data


def json_load(path):
    import json
    return json.loads(V.Path(path).read_text(encoding="utf-8"))


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--act", required=True, help="act_id from act_registry.yaml")
    args = ap.parse_args()

    V.ensure_dirs()
    act_id = args.act
    V.tee(f"{act_id}_step2_inspect")
    print(SEEDS, flush=True)
    registry = V.load_registry()
    act = next((a for a in registry if a["act_id"] == act_id), None)
    if act is None:
        print(f"FATAL: act_id {act_id!r} not in {V.REGISTRY_PATH}", flush=True)
        return 2
    if act.get("status_pending"):
        print(f"NOTE: registry status_pending={act['status_pending']!r} for "
              f"{act_id}; running because it was explicitly requested.",
              flush=True)

    src = V.SOURCES / act["source_file"].split("/")[-1]
    if not src.exists():
        print(f"FATAL: source missing: {src}", flush=True)
        return 2
    print("\n" + "=" * 76, flush=True)
    print(f"ACT {act_id}  ({act['act_name']})  file={src.name}", flush=True)
    print("=" * 76, flush=True)
    doc = fitz_open(src)
    n = len(doc)
    print(f"page count: {n}", flush=True)

    # --- hyphen census + raw-vs-block-order divergence (G4/G6 evidence)
    hyp = 0
    diff_pages = []
    for i, pg in enumerate(doc):
        rt = raw_text(pg)
        hyp += len(V.HYPHEN_BREAK_RE.findall(rt))
        mode, lines = V.page_lines(pg)
        ordered = V.norm_ws("\n".join(l["text"] for l in lines))
        if ordered and V.norm_ws(rt) != ordered:
            diff_pages.append(i + 1)
    print(f"hyphen line-breaks in raw text (word-\\nword): {hyp}", flush=True)
    print(f"pages where block reading-order differs from raw "
          f"get_text('text'): {len(diff_pages)}/{n}"
          f" {diff_pages[:12]}{'...' if len(diff_pages) > 12 else ''}",
          flush=True)

    # --- page 1 raw
    print("\n--- RAW get_text('text') of PAGE 1 ---", flush=True)
    print(raw_text(doc[0]), flush=True, end="")

    # --- find ToC
    header = find_header_page(doc)
    if header is None:
        header_diagnostics(doc)
        if not act.get("sequence_only_fallback"):
            print("\nNO_TOC: 'ARRANGEMENT OF SECTIONS' / 'CONTENTS' not found "
                  "in the first 15 pages. STOP.", flush=True)
            doc.close()
            return 3
        print("\nNO_TOC - but registry has sequence_only_fallback: true "
              "(user-authorized SEQUENCE_ONLY mode). Scanning body markers.",
              flush=True)
        scan = S.scan_document(doc)
        entries = [{"number": m["number"], "title": m["title"],
                    "page_1based": m["page_1based"], "base": m["base"],
                    "line": m["line"], "form": m["form"]}
                   for m in scan["markers"]]
        if not entries:
            print("NO_TOC + SEQUENCE_ONLY found 0 markers. STOP.", flush=True)
            doc.close()
            return 3
        rejected = scan["rejected"]
        lettered = scan["stats"]["lettered"]
        n_cand = len(entries) + len(rejected)
        gaps = scan["stats"]["gaps"]
        max_plain = max(e["base"] for e in entries if not
                        re.sub(r"[0-9]+", "", e["number"]))
        print("\nSEQUENCE_ONLY evidence:", flush=True)
        print(f"  marker forms found (M=margin+restated, D=direct dash, "
              f"R=Rep/omitted): {scan['stats']['forms']}", flush=True)
        print(f"  candidates tried: {n_cand}; accepted: {len(entries)}; "
              f"lettered: {lettered}; rejected: {len(rejected)}", flush=True)
        print(f"  accepted in strictly increasing order; first 10:", flush=True)
        for e in entries[:10]:
            print(f"    {e['number']}. {e['title']}  (p{e['page_1based']})",
                  flush=True)
        print(f"  last 10:", flush=True)
        for e in entries[-10:]:
            print(f"    {e['number']}. {e['title']}  (p{e['page_1based']})",
                  flush=True)
        print(f"  gaps in 1..{max_plain}: {gaps if len(gaps) <= 60 else str(gaps[:60]) + '...'} "
              f"(total {len(gaps)})", flush=True)
        print("  rejected candidates (first 15) - each proves the increasing "
              "rule filtered non-sections:", flush=True)
        for r in rejected[:15]:
            print(f"    p{r[0]}: {r[1]!r} -> {r[2]}", flush=True)
        anchor_ok = (max_plain == 511)
        anchor_msg = ("OK" if anchor_ok else
                      "MISMATCH -> WARNING: the sequence list may be "
                      "incomplete; see gaps below")
        print(f"\n  ANCHOR CHECK (external, not authority): highest plain "
              f"section = {max_plain}; expected by user = 511. {anchor_msg}",
              flush=True)
        a4_report(act_id, scan)
        a5_report(scan["stats"])
        if gaps:
            print(f"\n  GAPS in 1..{max_plain}: {len(gaps)} -> G2 = FAIL "
                  f"(A4: any gap in the accepted sequence is a FAIL for G2)",
                  flush=True)
            print("\n  gap contexts (judge each yourself):", flush=True)
            print_gap_context(scan, entries, gaps)
        else:
            print("\n  no gaps in the accepted plain sequence "
                  "(G2 stays SEQUENCE_ONLY, never PASS)", flush=True)
        V.write_json(V.RESULTS / f"{act_id}_markers.json", scan["markers"])
        V.write_json(V.RESULTS / f"{act_id}_expected.json",
                     [{"number": e["number"], "title": e["title"]}
                      for e in entries])
        V.write_json(V.RESULTS / f"{act_id}_expected_meta.json", {
            "expected_source": "sequence_only",
            "mode": "sequence_only",
            "anchor_note": ANCHOR_NOTE,
            "anchor_value": 511,
            "anchor_max_plain_seen": max_plain,
            "anchor_ok": bool(max_plain == 511),
            "expected_count": len(entries),
            "lettered": lettered,
            "gaps": gaps,
            "rejected_count": len(rejected),
        })
        V.write_json(V.RESULTS / f"{act_id}_toc_meta.json", {
            "header_page_1based": None,
            "toc_pages_1based": [],
            "mode": "sequence_only",
            "expected_count": len(entries),
            "gaps": gaps,
            "raw_vs_block_order_diff_pages": diff_pages,
            "hyphen_line_breaks": hyp,
        })
        block_order_evidence(doc, n, diff_pages, hyp)
        update_block_order_counter(act_id, n, diff_pages,
                                   count_modes(doc), hyp)
        doc.close()
        print("\nSTEP 2 CHECKPOINT 1 complete (SEQUENCE_ONLY).", flush=True)
        return 0

    print(f"\nToC header found on page {header + 1} "
          f"(0-based index {header})", flush=True)

    entries, pages_used, page_log, started = collect_entries(doc, header)
    print("\nToC page entry-density table "
          "(page, block-mode, lines, entries, density):", flush=True)
    for row in page_log:
        print("  p%-4d %-14s lines=%-4d entries=%-4d density=%.2f"
              % (row[0], row[1], row[2], row[3], row[4]), flush=True)
    if not started or not entries:
        print("NO_TOC: header found but no page with entry density >=0.25. "
              "STOP (would have to guess).", flush=True)
        doc.close()
        return 3

    # --- raw of first ToC page + middle page
    print(f"\n--- RAW get_text('text') of first ToC page "
          f"p{header + 1} ---", flush=True)
    print(raw_text(doc[header]), flush=True, end="")
    mid = n // 2
    print(f"\n--- RAW get_text('text') of MIDDLE page p{mid + 1} "
          f"({n} pages) ---", flush=True)
    print(raw_text(doc[mid]), flush=True, end="")

    # --- blocks of middle page
    print(f"\n--- get_text('blocks') of MIDDLE page p{mid + 1} "
          f"(x0,y0,x1,y1 | first 60 chars) in raw block order ---",
          flush=True)
    for b in doc[mid].get_text("blocks"):
        if len(b) >= 7 and b[6] == 0:
            txt = " ".join(str(b[4]).split())
            print(f"  ({b[0]:7.1f},{b[1]:7.1f},{b[2]:7.1f},{b[3]:7.1f}) | "
                  f"{txt[:60]!r}", flush=True)
        elif len(b) >= 7:
            print(f"  (image/other block type {b[6]}) x0={b[0]:.1f} "
                  f"y0={b[1]:.1f}", flush=True)

    # --- reading-order evidence: ordered lines of the middle page
    mmode, mlines = V.page_lines(doc[mid])
    print(f"\n--- reading-order lines of MIDDLE page p{mid + 1} "
          f"(mode={mmode}, first 40 lines) ---", flush=True)
    for l in mlines[:40]:
        print(f"  y={l['y']:6.1f} x0={l['x0']:6.1f} | "
              f"{l['text'].strip()[:90]!r}", flush=True)

    block_order_evidence(doc, n, diff_pages, hyp)
    modes = count_modes(doc)
    print(f"\nblock reading-order mode per page: {modes}", flush=True)
    update_block_order_counter(act_id, n, diff_pages, modes, hyp)

    # --- expected list checks
    nums = [e[0] for e in entries]
    gaps = gaps_of(nums)
    dup = sorted({x for x in nums if nums.count(x) > 1})
    print(f"\nexpected count: {len(entries)}", flush=True)
    print("first 10:", flush=True)
    for e in entries[:10]:
        print(f"  {e[0]}. {e[1]}", flush=True)
    print("last 10:", flush=True)
    for e in entries[-10:]:
        print(f"  {e[0]}. {e[1]}", flush=True)
    print(f"gaps in number sequence (missing integers): "
          f"{gaps if len(gaps) <= 60 else str(gaps[:60]) + '...'} "
          f"(total {len(gaps)})", flush=True)
    print(f"duplicate numbers in expected list: "
          f"{dup if dup else 'none'}", flush=True)

    # dedupe first-wins: ToC pages come before body pages, so arrangement
    # entries win over later body-page duplicates (footnote lines etc.)
    seen = set()
    deduped = []
    for n_, t in entries:
        if n_ in seen:
            continue
        seen.add(n_)
        deduped.append([n_, t])
    dropped = len(entries) - len(deduped)
    entries = deduped
    nums = [e[0] for e in entries]
    gaps = gaps_of(nums)
    print(f"deduped expected (first-wins): {len(entries)} unique of "
          f"{len(entries) + dropped} collected (dropped {dropped})",
          flush=True)
    max_plain_toc = max((int(x) for x in nums if x.isdigit()), default=None)
    print(f"  ANCHOR CHECK (external, not authority): highest plain section "
          f"in ToC = {max_plain_toc}; expected by user = 511. "
          f"{'OK' if max_plain_toc == 511 else 'MISMATCH -> WARNING'}",
          flush=True)

    # --- body marker scan (the records source for steps 3-7) --------------
    print("\n--- body marker scan (forward scanner) ---", flush=True)
    body_start = max(pages_used) if pages_used else 0
    print(f"  scanning body pages {body_start + 1}..{n} "
          f"(arrangement pages 1..{body_start} excluded)", flush=True)
    scan = S.scan_document(doc, start_page=body_start)
    b_entries = [{"number": m["number"], "title": m["title"],
                  "page_1based": m["page_1based"], "base": m["base"],
                  "line": m["line"], "form": m["form"]}
                 for m in scan["markers"]]
    if not b_entries:
        print("ToC found but body scan accepted 0 markers. STOP.", flush=True)
        doc.close()
        return 3
    b_rejected = scan["rejected"]
    b_gaps = scan["stats"]["gaps"]
    b_max = max((e["base"] for e in b_entries if
                 not re.sub(r"[0-9]+", "", e["number"])), default=None)
    print(f"  marker forms found (M=margin+restated, D=direct dash, "
          f"R=Rep/omitted): {scan['stats']['forms']}", flush=True)
    print(f"  accepted: {len(b_entries)}; lettered: "
          f"{len(scan['stats']['lettered'])}; rejected: {len(b_rejected)}",
          flush=True)
    print("  first 10:", flush=True)
    for e in b_entries[:10]:
        print(f"    {e['number']}. {e['title'][:70]}  (p{e['page_1based']})",
              flush=True)
    print("  last 10:", flush=True)
    for e in b_entries[-10:]:
        print(f"    {e['number']}. {e['title'][:70]}  (p{e['page_1based']})",
              flush=True)
    print(f"  gaps in body accepted sequence: "
          f"{b_gaps if len(b_gaps) <= 60 else str(b_gaps[:60]) + '...'} "
          f"(total {len(b_gaps)})", flush=True)
    print("  rejected candidates (first 15):", flush=True)
    for r in b_rejected[:15]:
        print(f"    p{r[0]}: {r[1]!r} -> {r[2]}", flush=True)
    print(f"  body ANCHOR: highest plain = {b_max}; expected by user = 511 -> "
          f"{'OK' if b_max == 511 else 'WARNING'}", flush=True)
    a4_report(act_id, scan)
    a5_report(scan["stats"])
    if b_gaps:
        print("\n  body gap contexts (judge each yourself):", flush=True)
        print_gap_context(scan, b_entries, b_gaps)
    V.write_json(V.RESULTS / f"{act_id}_markers.json", scan["markers"])

    V.write_json(V.RESULTS / f"{act_id}_expected.json",
                 [{"number": n_, "title": t} for n_, t in entries])
    V.write_json(V.RESULTS / f"{act_id}_expected_meta.json", {
        "expected_source": "toc",
        "mode": "toc",
        "header_page_1based": header + 1,
        "toc_pages_1based": pages_used,
        "expected_count": len(entries),
        "gaps": gaps,
        "duplicates": dup,
        "deduped_dropped": dropped,
        "anchor_value": 511,
        "anchor_max_plain_seen": max_plain_toc,
        "anchor_ok": bool(max_plain_toc == 511),
        "lettered": [n for n in nums if not n.isdigit()],
        "rejected_count": len(b_rejected),
        "body_markers": len(b_entries),
        "body_max_plain": b_max,
        "body_gaps": b_gaps,
    })
    V.write_json(V.RESULTS / f"{act_id}_toc_meta.json", {
        "mode": "toc",
        "header_page_1based": header + 1,
        "toc_pages_1based": pages_used,
        "expected_count": len(entries),
        "gaps": gaps,
        "duplicates": dup,
        "deduped_dropped": dropped,
        "body_markers": len(b_entries),
        "raw_vs_block_order_diff_pages": diff_pages,
        "hyphen_line_breaks": hyp,
    })
    doc.close()
    print("\nSTEP 2 CHECKPOINT 1 complete (ToC mode).", flush=True)
    return 0


def count_modes(doc):
    modes = {}
    for pg in doc:
        m, _ = V.reading_order(pg)
        modes[m] = modes.get(m, 0) + 1
    return modes


def block_order_evidence(doc, n, diff_pages, hyp):
    """LAYOUT + READING ORDER paragraph - the evidence-based decision."""
    two = []
    for i, pg in enumerate(doc):
        m, _ = V.reading_order(pg)
        if m == "two-column":
            two.append(i + 1)
    print(f"\nLAYOUT: {n} pages; two-column pages: {len(two)} "
          f"{two[:20]}{'...' if len(two) > 20 else ''}; "
          f"{len(diff_pages)} pages diverge from raw text order; "
          f"{hyp} hyphen line-breaks.", flush=True)


if __name__ == "__main__":
    try:
        rc = main()
    except SystemExit:
        raise
    except Exception:
        import traceback
        print("FATAL unhandled error in step2_inspect.py", flush=True)
        traceback.print_exc(file=sys.stdout)
        rc = 2
    print(f"[exit] {rc}", flush=True)
    sys.exit(rc)
