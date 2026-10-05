#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""step6_validate.py - STEP 6 of the ingest_v2 pilot: run gates G1-G9 and
write results/<act_id>_gates.json.

Usage: python step6_validate.py --act <act_id>

Log: results/<act_id>_step6_validate.log (tee'd by this script).
Writes: results/<act_id>_gates.json
Exit code: 3 if any gate FAILs, else 0.

Seeds: G1 random middle pages 20261010; A2 removed-line sample 20261012.
"""

import argparse
import json
import random
import re
import sys

import v2_common as V
import v2_scanner as S

G1_SEED = 20261010
A2_SEED = 20261012
A7B_SEED = 20261014
WINDOW = 60
PRIMARY_RATE = 0.99
MAX_CHARS = 3000

WHITELIST_RE = re.compile(
    r"^(Illustrations?|Explanation|Exceptions?|Provided|Chapter|Part|"
    r"Schedule)\b")
HYPHEN_BREAK_RE = re.compile(r"[a-z]-\n[a-z]")
PAGENUM_LINE_RE = re.compile(r"^\s*\d{1,3}\s*$")
SEP_LINE_RE = re.compile(r"^\s*[-\u2013\u2014*]{5,}\s*$")
BOILER_RE = re.compile(r"This Bare Act", re.I)
FREF_PREFIX_RE = re.compile(r"^\s*(?:\d{1,3}\s*)?\*+\[?|^\s*\d{1,3}\s*\[+")


def norm_raw(t):
    t = S.SOFT_RE.sub("", t)
    t = re.sub(r"[ \t]+\n", "\n", t)
    t = re.sub(r"\n{2,}", "\n", t)
    t = re.sub(r"\n[ \t]+", "\n", t)
    t = re.sub(r"(?<=[A-Za-z0-9])-\n(?=[a-z])", "-", t)
    return V.norm_ws(t)


def is_plain_number(num):
    return not S.suffix_of(num) or " to " in num


def chunks60(s):
    if len(s) < WINDOW:
        return [s] if s else []
    return [s[i:i + WINDOW] for i in range(0, len(s) - WINDOW + 1, WINDOW)]


def gate_g1(doc, act, markers):
    raw1 = doc[0].get_text("text")
    n1_name = V.norm_ws(act["act_name"]).lower() in norm_raw(raw1).lower()
    n1_year = str(act["year"]) in raw1
    n = len(doc)
    rng = random.Random(G1_SEED)
    mid = list(range(n // 4, n - n // 4))
    pages = sorted(rng.sample(mid, 5))
    marker_pages = {}
    for m in markers:
        marker_pages.setdefault(m["page_1based"], []).append(m["number"])
    page_hits = []
    ok = True
    for p0 in pages:
        nums = marker_pages.get(p0 + 1, [])
        page_hits.append({"page_1based": p0 + 1, "markers_found": nums[:3]})
        if not nums:
            ok = False
    status = "PASS" if (n1_name and n1_year and ok) else "FAIL"
    ev = {"page1_has_act_name": n1_name, "page1_has_year": n1_year,
          "seed": G1_SEED, "middle_pages_0based": pages, "page_hits": page_hits}
    print(f"  page1 contains act_name: {n1_name}; year {act['year']}: "
          f"{n1_year}", flush=True)
    for h in page_hits:
        print(f"    middle page {h['page_1based']}: markers "
              f"{h['markers_found'] or 'NONE'}", flush=True)
    return status, ev


def gate_g2(markers, records, expected, emeta):
    if emeta.get("mode") == "toc":
        # ToC mode: every expected section must have at least one record;
        # range markers cover their printed span (bases only); lettered
        # numbers need their own record unless a range covers their base.
        exp_nums = [e["number"] for e in expected]
        exp_set = set(exp_nums)
        exp_bases = {int(re.sub(r"[A-Za-z]+", "", n)) for n in exp_nums}
        rec_nums = {r["number"] for r in records}
        range_bases = set()
        for m in markers:
            if m.get("covers"):
                range_bases.update(m["covers"])
        missing = []
        for e_ in exp_nums:
            if e_ in rec_nums:
                continue
            base = int(re.sub(r"[A-Za-z]+", "", e_))
            if base in range_bases:
                continue
            missing.append(e_)
        extra = []
        for m in markers:
            num = m["number"]
            if num in exp_set:
                continue
            if m.get("covers") and m["base"] in exp_bases:
                continue
            extra.append(num)
        status = "PASS" if not missing and not extra else "FAIL"
        ev = {"mode": "toc", "expected_count": len(exp_nums),
              "records": len(records), "missing": missing, "extra": extra,
              "anchor_max_plain_seen": emeta.get("anchor_max_plain_seen"),
              "anchor_ok": emeta.get("anchor_ok")}
        print(f"  ToC expected sections: {len(exp_nums)}; records: "
              f"{len(records)}", flush=True)
        print(f"  missing (expected, no record): "
              f"{missing if len(missing) <= 40 else str(missing[:40]) + '...'} "
              f"(total {len(missing)})", flush=True)
        print(f"  extra (markers, not in ToC): "
              f"{extra if len(extra) <= 40 else str(extra[:40]) + '...'} "
              f"(total {len(extra)})", flush=True)
        print(f"  external anchor max plain = "
              f"{ev['anchor_max_plain_seen']} vs 511 -> "
              f"{'OK' if ev['anchor_ok'] else 'WARNING'}", flush=True)
        return status, ev
    covered = set()
    bases_seq = []
    for m in markers:
        if m.get("covers"):
            covered.update(m["covers"])
            bases_seq.append(m["base"])
        elif is_plain_number(m["number"]):
            covered.add(m["base"])
            bases_seq.append(m["base"])
    gaps = []
    if covered:
        gaps = [x for x in range(min(covered), max(covered) + 1)
                if x not in covered]
    increasing = all(b > a for a, b in zip(bases_seq, bases_seq[1:]))
    max_plain = max(covered) if covered else None
    anchor_ok = (max_plain == 511)
    status = "FAIL" if gaps else "SEQUENCE_ONLY"
    ev = {"mode": "sequence_only", "markers": len(markers),
          "plain_strictly_increasing": increasing,
          "covered_range": [min(covered), max(covered)] if covered else None,
          "gaps": gaps, "max_plain": max_plain,
          "external_anchor_511": "OK" if anchor_ok else "WARNING"}
    print(f"  strictly increasing: {increasing}; covered "
          f"{min(covered) if covered else '-'}..{max(covered) if covered else '-'};"
          f" gaps: {gaps if len(gaps) <= 40 else str(gaps[:40]) + '...'} "
          f"(total {len(gaps)})", flush=True)
    print(f"  external anchor max plain = {max_plain}; expected 511 -> "
          f"{'OK' if anchor_ok else 'WARNING'}", flush=True)
    return status, ev


def strip_prefix(t):
    needed = False
    while True:
        m = FREF_PREFIX_RE.match(t)
        if m and m.end() > m.start():
            t = t[m.end():]
            needed = True
            continue
        if t.startswith("["):
            t = t[1:]
            needed = True
            continue
        break
    return t.lstrip(), needed


def gate_g3(records):
    fails = []
    stripped_count = 0
    checked = 0
    for r in records:
        if r["part_index"] != 0:
            continue
        checked += 1
        t, needed = strip_prefix(r["text"].lstrip())
        if needed:
            stripped_count += 1
        num = r["number"]
        if not (t.lower().startswith(num.lower())
                or t.lower().startswith(num.lower() + ".")):
            fails.append({"id": r["id"], "head": t[:70]})
    status = "PASS" if not fails else "FAIL"
    ev = {"part0_records": checked, "needed_prefix_stripping": stripped_count,
          "failures": fails[:10]}
    print(f"  part-0 records checked: {checked}; needed prefix stripping: "
          f"{stripped_count}", flush=True)
    print(f"  not starting with own number: {len(fails)} "
          f"{[f['id'] for f in fails[:6]]}", flush=True)
    return status, ev


def gate_g4(doc, records, total_pages):
    pagelines = []
    hyphens = []
    boiler = []
    repeats = {}
    raw_line_pages = {}
    for pi in range(total_pages):
        _, ls = V.page_lines(doc[pi])
        seen = set()
        for l in ls:
            s = l["text"].strip()
            if s:
                seen.add(s)
        for s in seen:
            raw_line_pages[s] = raw_line_pages.get(s, 0) + 1
    for r in records:
        for ln in r["text"].split("\n"):
            s = ln.strip()
            if not s:
                continue
            if PAGENUM_LINE_RE.match(s):
                pagelines.append((r["id"], s))
            if HYPHEN_BREAK_RE.search(ln):
                hyphens.append((r["id"], ln[:60]))
            if BOILER_RE.search(s) or SEP_LINE_RE.match(s):
                boiler.append((r["id"], s[:70]))
            if (len(s) >= 4 and not WHITELIST_RE.match(s)
                    and not PAGENUM_LINE_RE.match(s)):
                cnt = raw_line_pages.get(s, 0)
                if cnt / total_pages >= 0.30:
                    repeats.setdefault(s, set()).add(r["id"])
    repeat_hits = [{"line": s[:80], "pages": raw_line_pages.get(s, 0),
                    "records": sorted(ids)[:4]}
                   for s, ids in sorted(repeats.items())]
    status = "PASS" if not (pagelines or hyphens or boiler or repeat_hits) \
        else "FAIL"
    ev = {"page_number_lines": len(pagelines),
          "hyphen_breaks": len(hyphens), "boilerplate": len(boiler),
          "repeated_30pct_lines": len(repeat_hits),
          "examples_page_number": pagelines[:5],
          "examples_hyphen": hyphens[:5],
          "examples_boiler": boiler[:5],
          "examples_repeats": repeat_hits[:5]}
    print(f"  standalone page-number lines: {len(pagelines)}", flush=True)
    print(f"  [a-z]-\\n[a-z] hyphen breaks: {len(hyphens)}", flush=True)
    print(f"  boilerplate/separator lines: {len(boiler)}", flush=True)
    print(f"  non-whitelisted lines on >=30% of pages: {len(repeat_hits)} "
          f"{[h['line'][:40] for h in repeat_hits[:3]]}", flush=True)
    return status, ev


def gate_g5(records, keys):
    bad_ids = []
    empty = []
    missing = []
    for r in records:
        if len(r["id"].split(":")) != 4 or not r["id"].startswith(r["act_id"]):
            bad_ids.append(r["id"])
        if not r["text"].strip():
            empty.append(r["id"])
        for k in keys:
            if k not in r:
                missing.append((r.get("id"), k))
            elif k not in ("title", "chapter", "repealed_on", "replaced_by") \
                    and r[k] is None:
                missing.append((r.get("id"), k))
        if not isinstance(r.get("amendment_notes"), list):
            missing.append((r.get("id"), "amendment_notes"))
    ids = [r["id"] for r in records]
    dups = sorted({i for i in ids if ids.count(i) > 1})
    status = "PASS" if not (bad_ids or empty or missing or dups) else "FAIL"
    ev = {"records": len(records), "duplicate_ids": dups,
          "malformed_ids": bad_ids[:5], "empty_texts": empty[:5],
          "missing_or_null_nonnullable": missing[:5]}
    print(f"  records: {len(records)}; duplicate ids: {dups or 'none'}; "
          f"empty texts: {len(empty)}; non-nullable problems: {len(missing)}",
          flush=True)
    return status, ev


def gate_g6(doc, scan, segs, records, raw_pages):
    lines = scan["lines"]
    # symmetric normalization: lines the scanner drops as running
    # headers/footers (gate_g4's >=30%-of-pages rule) are also dropped from
    # the raw reference, so both sides compare verbatim content only.
    repeat_lines = scan.get("repeat_lines") or []
    seg_by_num = {s["number"]: s for s in segs["sections"]}
    raw_cache = {}
    total_w = found_w = 0
    whole_total = whole_found = 0
    line_total = line_found = 0
    failures = []
    for rec in records:
        seg = seg_by_num.get(rec["number"])
        if seg is None or rec["part_index"] >= len(seg["parts"]):
            failures.append({"id": rec["id"], "why": "segment missing"})
            continue
        kept_rec = seg["parts"][rec["part_index"]]["lines"]
        p0, p1 = rec["page_start"], rec["page_end"]
        if (p0, p1) not in raw_cache:
            txt = "\n".join(raw_pages[p0 - 1:p1])
            for rep in repeat_lines:
                txt = txt.replace(rep, " ")
            raw_cache[(p0, p1)] = norm_raw(txt)
        rawn = raw_cache[(p0, p1)]
        frags = []
        cur = []
        for k in kept_rec:
            if cur and k != cur[-1] + 1:
                frags.append(cur)
                cur = []
            cur.append(k)
        if cur:
            frags.append(cur)
        rec_fail = 0
        for g in frags:
            ft, _, _, _ = S.assemble_text(lines, g)
            fn = V.norm_ws(ft)
            for w in chunks60(fn):
                total_w += 1
                if w in rawn:
                    found_w += 1
                else:
                    rec_fail += 1
        wfn = V.norm_ws(rec["text"])
        for w in chunks60(wfn):
            whole_total += 1
            if w in rawn:
                whole_found += 1
        for ln in rec["text"].split("\n"):
            s = V.norm_ws(ln)
            if not s:
                continue
            line_total += 1
            if s in rawn:
                line_found += 1
        if rec_fail:
            failures.append({"id": rec["id"], "missing_windows": rec_fail,
                             "page_range": [p0, p1]})
    primary = found_w / total_w if total_w else 1.0
    whole = whole_found / whole_total if whole_total else 1.0
    liner = line_found / line_total if line_total else 1.0
    failures.sort(key=lambda f: -f.get("missing_windows", 0))
    status = "PASS" if primary >= PRIMARY_RATE else "FAIL"
    ev = {"primary_fragment_rate": round(primary, 6),
          "diagnostic_whole_record_rate": round(whole, 6),
          "diagnostic_line_rate": round(liner, 6),
          "raw_reference": "get_text('text', sort=True)",
          "reference_repeated_lines_stripped": list(repeat_lines),
          "windows": total_w, "primary_failures": len(failures),
          "worst_5": failures[:5], "threshold": PRIMARY_RATE}
    print(f"  A2 PRIMARY fragment windows: {found_w}/{total_w} = "
          f"{primary:.4%} (threshold {PRIMARY_RATE:.0%})", flush=True)
    print(f"  DIAGNOSTIC whole-record windows: {whole_found}/{whole_total} = "
          f"{whole:.4%}", flush=True)
    print(f"  DIAGNOSTIC cleaned-lines-in-raw: {line_found}/{line_total} = "
          f"{liner:.4%}", flush=True)
    print(f"  records with missing windows: {len(failures)}; worst 5:",
          flush=True)
    for f in failures[:5]:
        print(f"    {f}", flush=True)
    return status, ev


def gate_g7(records, markers):
    order = [m["number"] for m in markers]
    parents = []
    parts_ok = True
    problems = []
    by_parent = {}
    for r in records:
        by_parent.setdefault(r["parent_id"], []).append(r)
        if r["part_index"] == 0:
            parents.append(r["number"])
    if parents != order:
        problems.append({"parent_order_mismatch": True,
                         "first_divergence": next(
                             (i for i, (a, b) in enumerate(
                                 zip(parents, order)) if a != b), None)})
        parts_ok = False
    for pid, recs in by_parent.items():
        idxs = [r["part_index"] for r in recs]
        if idxs != list(range(len(recs))) or any(
                r["part_count"] != len(recs) for r in recs):
            problems.append({"parent_id": pid, "part_index": idxs,
                             "part_counts": [r["part_count"] for r in recs]})
            parts_ok = False
    status = "PASS" if parts_ok else "FAIL"
    ev = {"parents": len(parents), "markers": len(order), "problems": problems[:5]}
    print(f"  record parent order matches marker order: {parents == order}; "
          f"part_index/part_count consistent: {parts_ok}", flush=True)
    return status, ev


def gate_g8(records, flags):
    flagged = {(f["number"], f["part_index"]) for f in flags.get(
        "long_unsplit", [])}
    over = [(r["id"], len(r["text"])) for r in records
            if len(r["text"]) > MAX_CHARS
            and (r["number"], r["part_index"]) not in flagged]
    status = "PASS" if not over else "FAIL"
    ev = {"limit": MAX_CHARS, "flagged_long_unsplit": sorted(flagged),
          "unflagged_over_limit": over[:10],
          "longest_text": max((len(r["text"]) for r in records), default=0)}
    print(f"  longest record: {ev['longest_text']} chars; over limit "
          f"without LONG_UNSPLIT flag: {len(over)}; flagged: {len(flagged)}",
          flush=True)
    return status, ev


def gate_g9(scan, records, segs, clean):
    st = scan["stats"]
    lines = scan["lines"]
    fns = scan["footnotes"]
    att_f = [f for f in fns if f["status"] == "attached"]
    una_f = [f for f in fns if f["status"] == "unattached"]
    amb_f = [f for f in fns if f["status"] == "ambiguous"]
    detected = sum(len(f["members"]) for f in fns)
    attached_lines = sum(len(f["members"]) for f in att_f)
    unattached_lines = sum(len(f["members"]) for f in una_f + amb_f)
    label_footnote = sum(1 for ln in lines if ln["label"] == "footnote")
    accounting_ok = (detected == attached_lines + unattached_lines
                     and detected == label_footnote)
    leaked = []
    for seg in segs["sections"]:
        for p in seg["parts"]:
            for k in p["lines"]:
                if lines[k]["label"] == "footnote":
                    leaked.append((seg["number"], p["part_index"], k))
                    break
    status = "PASS" if (accounting_ok and not leaked) else "FAIL"
    ev = {"footnotes_total": len(fns),
          "footnotes_attached": len(att_f),
          "footnotes_unattached": len(una_f),
          "footnotes_ambiguous": len(amb_f),
          "footnote_lines_detected": detected,
          "labelled_footnote_lines": label_footnote,
          "attached_lines": attached_lines,
          "unattached_lines": unattached_lines,
          "scope_boundaries": st.get("scope_boundaries"),
          "chapter_notes": st.get("chapter_notes"),
          "groups": len(scan["groups"]),
          "accounting_ok": accounting_ok,
          "records_containing_footnote_lines": leaked[:5]}
    print(f"  footnote-level (A7): total {len(fns)} = attached {len(att_f)} + "
          f"unattached {len(una_f)} + ambiguous {len(amb_f)}", flush=True)
    print(f"  line-level accounting: {detected} detected = "
          f"{attached_lines} attached + {unattached_lines} unattached; "
          f"labelled {label_footnote} -> {accounting_ok}", flush=True)
    print(f"  scope boundaries: {st.get('scope_boundaries')}; chapter notes: "
          f"{st.get('chapter_notes')}; groups: {len(scan['groups'])}", flush=True)
    print(f"  records still containing a footnote line: {len(leaked)}",
          flush=True)
    return status, ev


def a7b_report(scan, records):
    lines = scan["lines"]
    fns = scan["footnotes"]
    groups = scan["groups"]
    bounds = scan["scope_boundaries"]
    print("\n" + "=" * 76, flush=True)
    print("A7b REPORT - printed-page scope footnote attachment", flush=True)
    print("=" * 76, flush=True)
    print(f"scope boundaries (kind == page_number): {len(bounds)}", flush=True)
    for b in bounds[:8]:
        print(f"  line {b}: {lines[b]['text']!r} "
              f"(pdf page {lines[b]['page'] + 1})", flush=True)
    att = [f for f in fns if f["status"] == "attached"]
    una = [f for f in fns if f["status"] == "unattached"]
    amb = [f for f in fns if f["status"] == "ambiguous"]
    print(f"footnotes: total {len(fns)}; attached by reference {len(att)}; "
          f"unattached {len(una)}; ambiguous {len(amb)}", flush=True)
    print("  (ambiguous = footnote number not parseable, or its reference "
          "precedes the first section marker of the span)", flush=True)
    for f in una:
        print(f"  UNATTACHED group {f['group']} num={f['num']} "
              f"pdf_page={f['pdf_page']} span={tuple(f['span'])} "
              f"text={f['text'][:90]!r}", flush=True)
    for f in amb:
        print(f"  AMBIGUOUS group {f['group']} num={f['num']} "
              f"reason={f['reason']!r} text={f['text'][:90]!r}", flush=True)
    fn_by_group = {}
    for f in fns:
        fn_by_group.setdefault(f["group"], []).append(f)
    all_att = sum(1 for g in groups
                  if fn_by_group.get(g["id"])
                  and all(x["status"] == "attached"
                          for x in fn_by_group[g["id"]]))
    any_att = sum(1 for g in groups
                  if any(x["status"] == "attached"
                         for x in fn_by_group.get(g["id"], [])))
    print(f"group-level now: {len(groups)} groups; all-footnotes-attached="
          f"{all_att}; any-attached={any_att}; none-attached="
          f"{len(groups) - any_att}", flush=True)
    print("round-1 audit (positional rule): 80 groups = 19 by reference, "
          "1 fallback, 60 ambiguous", flush=True)

    parent = {}
    for r in records:
        if r["part_index"] == 0:
            parent[r["number"]] = r["id"]
    rng = random.Random(A7B_SEED)
    samp = rng.sample(att, min(25, len(att)))
    print(f"\n25 random attachments (seed {A7B_SEED}):", flush=True)
    for f in samp:
        r0 = f["refs"][0] if f["refs"] else None
        pid = parent.get(f["owner_numbers"][0], "?")
        print(f"  group {f['group']} num={f['num']} owners="
              f"{f['owner_numbers']} pdf_page={f['pdf_page']}", flush=True)
        print(f"    footnote text: {f['text'][:150]!r}", flush=True)
        if r0:
            print(f"    matched marker: {r0['text']!r} at line {r0['line']}"
                  f"{' (chapter_note)' if r0['chapter_note'] else ''}",
                  flush=True)
            print(f"    ctx80: {r0['ctx']!r}", flush=True)
        print(f"    record id: {pid}", flush=True)

    print("\nfootnote groups for PDF pages 5 and 7:", flush=True)
    for pdfp in (5, 7):
        pgs = [g for g in groups
               if any(lines[mi]["page"] + 1 == pdfp for mi in g["members"])]
        print(f"  PDF page {pdfp}: {len(pgs)} group(s)", flush=True)
        for g in pgs:
            for f in fn_by_group.get(g["id"], []):
                lo, hi = f["span"]
                folio_lo = lines[lo]["text"] if 0 <= lo < len(lines) else "<start>"
                folio_hi = lines[hi]["text"] if 0 <= hi < len(lines) else "<end>"
                print(f"    group {g['id']} span=({lo},{hi}) "
                      f"folios=({folio_lo!r},{folio_hi!r})", flush=True)
                print(f"      num={f['num']} status={f['status']} "
                      f"owners={f['owner_numbers']} "
                      f"text={f['text'][:110]!r}", flush=True)
                for r in f["refs"][:3]:
                    rnums = [scan["markers"][i]["number"]
                             for i in r["owners"]]
                    print(f"      ref line {r['line']}: {r['text']!r} "
                          f"-> in sections {rnums}", flush=True)

    print("\nchapter notes (A7c item 2):", flush=True)
    for f in scan["chapter_notes"]:
        crefs = [r for r in f["refs"] if r["chapter_note"]]
        print(f"  group {f['group']} num={f['num']} owners="
              f"{f['owner_numbers']} text={f['text'][:110]!r}", flush=True)
        for r in crefs:
            print(f"    heading marker {r['text']!r} at line {r['line']}",
                  flush=True)


def a7c_verify(records, scan):
    print("\n" + "=" * 76, flush=True)
    print("A7c VERIFICATION - cases a-g (full record text + amendment_notes)",
          flush=True)
    print("=" * 76, flush=True)
    by_num = {}
    for r in records:
        by_num.setdefault(r["number"], []).append(r)

    # Cases a-g assert IPC-specific content: section 498A and its CHAPTER XXA
    # insertion, the "46 of 1983" amendment note, and IPC footnote ownership
    # of 302/303/304. An act that contains no section 498A has nothing for
    # these cases to assert, so report n/a instead of fabricating FAILs.
    # a7c is diagnostic only - it never contributes to G1-G9 or the exit code
    # (see the gate summary in main()).
    if "498A" not in by_num:
        print("\n[a7c] n/a for this act: cases a-g assert IPC-specific "
              "content (section 498A / CHAPTER XXA / 46-of-1983 note) and "
              "this act contains no section 498A. Diagnostic only; does not "
              "affect G1-G9.", flush=True)
        return

    fn_owner = {}
    for f in scan["footnotes"]:
        for on in f["owner_numbers"]:
            fn_owner.setdefault(on, []).append(f)
    mk_by_num = {m["number"]: m for m in scan["markers"]}
    oks = []

    def show(num):
        recs = by_num.get(num, [])
        if not recs:
            print(f"  !! no record for {num}", flush=True)
        for r in recs:
            print(f"--- record {r['id']} part {r['part_index']}/"
                  f"{r['part_count']} status={r['status']} "
                  f"pages {r['page_start']}-{r['page_end']} "
                  f"chapter={r['chapter']!r}", flush=True)
            print(f"text ({len(r['text'])} chars):", flush=True)
            print(r["text"], flush=True)
            print(f"amendment_notes ({len(r['amendment_notes'])}):",
                  flush=True)
            for note in r["amendment_notes"]:
                print(f"  - {note!r}", flush=True)
        return recs

    for num in ("498A", "498", "302", "303", "304", "304A", "304B", "300",
                "19", "20", "21", "13"):
        show(num)

    # a. 498A
    r498a = by_num.get("498A", [None])[0]
    exp_chapter = ("CHAPTER XXA - OF CRUELTY BY HUSBAND OR RELATIVES OF "
                   "HUSBAND")
    chap_note = any("498A" in f["owner_numbers"]
                    for f in scan["chapter_notes"])
    # chapter compared fuzzily: some editions' PDF text layer glues spaces
    # inside the heading (OFCRUELTY); title_score is the same matcher used
    # for ToC titles.
    chap_ok = bool(r498a) and V.title_score(
        exp_chapter, r498a["chapter"]) >= 0.90
    a_ok = bool(r498a) and re.search(r"Explanation.[-\u2010-\u2015]",
                                     r498a["text"]) \
        and "(a)" in r498a["text"] and "wilful conduct" in r498a["text"] \
        and "(b)" in r498a["text"] and "harassment" in r498a["text"] \
        and chap_ok \
        and any("46 of 1983" in n
                for n in r498a["amendment_notes"]) and chap_note
    oks.append(("a 498A Explanation(a)/(b) + chapter XXA + chapter note",
                a_ok))
    print(f"\nCHECK a: 498A chapter={r498a['chapter']!r} expected="
          f"{exp_chapter!r} fuzzy={V.title_score(exp_chapter, r498a['chapter']):.3f}; "
          f"46-of-1983 note: "
          f"{any('46 of 1983' in n for n in r498a['amendment_notes'])}; "
          f"chapter_note attached to 498A: {chap_note} -> "
          f"{'PASS' if a_ok else 'FAIL'}", flush=True)

    # b. 498
    r498 = by_num.get("498", [None])[0]
    b_ok = bool(r498) and "CHAPTER XXA" not in r498["text"] \
        and r498["text"].rstrip().endswith("or with both.")
    oks.append(("b 498 has no CHAPTER XXA, ends 'or with both.'", b_ok))
    print(f"CHECK b: 498 contains 'CHAPTER XXA': "
          f"{'CHAPTER XXA' in r498['text'] if r498 else 'n/a'}; tail="
          f"{(r498['text'][-70:] if r498 else None)!r} -> "
          f"{'PASS' if b_ok else 'FAIL'}", flush=True)

    # c. 302/303/304 -> fn1; 304A/304B -> the insertion footnote the book's
    # own marker attaches (this edition numbers them 1/2; SPEC's 2/3 was the
    # old edition's page-170 layout) - intent: each carries its note
    c_ok = True
    for num, want in (("302", "1"), ("303", "1"), ("304", "1"),
                      ("304A", None), ("304B", None)):
        recs = by_num.get(num, [])
        if want is None:
            owned = [f for f in fn_owner.get(num, [])
                     if "Ins." in f["text"]]
            label = "insertion note"
        else:
            owned = [f for f in fn_owner.get(num, []) if f["num"] == want]
            label = f"footnote {want}"
        texts = [f["text"] for f in owned]
        notes_all = [note for r in recs for note in r["amendment_notes"]]
        has = any(t in note for t in texts for note in notes_all)
        this_ok = bool(texts) and has
        c_ok = c_ok and this_ok
        print(f"CHECK c: {num} owns {label}: texts="
              f"{[t[:70] for t in texts]!r} in amendment_notes: {this_ok}",
              flush=True)
    oks.append(("c 302/303/304 fn1, 304A/304B carry insertion note",
                c_ok))

    # d. 300 across page number 167
    r300 = by_num.get("300", [None])[0]
    d_ok = False
    if r300:
        standalone = any(ln.strip() == "167"
                         for ln in r300["text"].split("\n"))
        idx = r300["text"].find("2ndly")
        ctx = r300["text"][max(0, idx - 90): idx + 40] if idx >= 0 else ""
        d_ok = (not standalone) and "167" not in r300["text"] \
            and bool(idx >= 0) and re.search(r"or[-\u2010-\u2015]", ctx)
        print(f"CHECK d: 300 standalone '167' line: {standalone}; "
              f"'167' substring: {'167' in r300['text']}; context around "
              f"'2ndly': {ctx!r} -> {'PASS' if d_ok else 'FAIL'}", flush=True)
    oks.append(("d 300 continuous across removed '167'", d_ok))

    # e. 304 across PDF page break
    r304 = by_num.get("304", [None])[0]
    e_ok = False
    if r304:
        flat = re.sub(r"\s+", " ", r304["text"])
        e_ok = bool(re.search(
            r"such bodily injury as is likely to cause death;", flat)) \
            and r304["page_start"] != r304["page_end"]
        print(f"CHECK e: 304 join 'such bodily injury as is likely to cause "
              f"death;': {'such bodily injury as is likely to cause death;' in flat}; "
              f"page span {r304['page_start']}-{r304['page_end']} -> "
              f"{'PASS' if e_ok else 'FAIL'}", flush=True)
    oks.append(("e 304 continuous across PDF page break", e_ok))

    # f. 19/20 carry the Madras footnote; 21's 5*[Third. does not
    madras = [f for f in scan["footnotes"]
              if "Madras Civil Courts Act" in f["text"]]
    m_owners = sorted({o for f in madras for o in f["owner_numbers"]})
    n19 = [r["amendment_notes"] for r in by_num.get("19", [])]
    n20 = [r["amendment_notes"] for r in by_num.get("20", [])]
    n21 = [r["amendment_notes"] for r in by_num.get("21", [])]
    mtext = madras[0]["text"] if madras else ""
    in19 = any(mtext in n for nn in n19 for n in nn)
    in20 = any(mtext in n for nn in n20 for n in nn)
    in21 = any("Madras Civil Courts Act" in n for nn in n21 for n in nn)
    fn21_5 = [f for f in fn_owner.get("21", []) if f["num"] == "5"]
    line_third = next((ln["i"] for ln in scan["lines"]
                       if "5*[Third" in ln["text"]), None)
    f_ok = ("19" in m_owners and "20" in m_owners and in19 and in20
            and not in21)
    print(f"CHECK f: Madras footnote owners={m_owners}; in 19 notes: {in19}; "
          f"in 20 notes: {in20}; in 21 notes: {in21} -> "
          f"{'PASS' if f_ok else 'FAIL'}", flush=True)
    print(f"  21's own footnote 5: "
          f"{[f['text'][:80] for f in fn21_5]!r}", flush=True)
    print(f"  '5*[Third.' marker line: {line_third} "
          f"{(scan['lines'][line_third]['text'][:70] if line_third is not None else None)!r}",
          flush=True)
    oks.append(("f 19+20 carry Madras fn, 21 does not", f_ok))

    # g. 13 omitted, verbatim
    r13 = by_num.get("13", [None])[0]
    mk13 = mk_by_num.get("13")
    g_ok = bool(r13) and r13["status"] == "omitted" \
        and mk13["status_hint"] == "omitted" \
        and ("Rep." in r13["text"] or "Omitted" in r13["text"]) \
        and r13["text"].startswith("13.")
    oks.append(("g 13 omitted, text verbatim", g_ok))
    print(f"CHECK g: 13 status={r13['status'] if r13 else None} "
          f"status_hint={mk13['status_hint'] if mk13 else None} text="
          f"{(r13['text'] if r13 else None)!r} -> "
          f"{'PASS' if g_ok else 'FAIL'}", flush=True)

    print("\nA7c verification summary:", flush=True)
    for name, ok in oks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}", flush=True)


def typo_report(doc, records):
    print("\n" + "=" * 76, flush=True)
    print("A7c SOURCE TYPO REPORT (verbatim, NOT corrected)", flush=True)
    print("=" * 76, flush=True)
    for typo in ("Jutsice", "he likely", ". or"):
        print(f"\ntypo {typo!r}:", flush=True)
        rec_hits = 0
        for r in records:
            idx = 0
            while True:
                i = r["text"].find(typo, idx)
                if i < 0:
                    break
                rec_hits += 1
                ctx = r["text"][max(0, i - 70):i + len(typo) + 70]
                print(f"  record {r['id']}: ...{ctx!r}...", flush=True)
                idx = i + len(typo)
        raw_hits = 0
        for pi in range(len(doc)):
            txt = doc[pi].get_text("text")
            i = txt.find(typo)
            if i >= 0:
                raw_hits += 1
                ctx = re.sub(r"\s+", " ",
                             txt[max(0, i - 70):i + len(typo) + 70])
                page1 = pi + 1
                owners = [r["id"] for r in records
                          if typo in r["text"]
                          and r["page_start"] <= page1 <= r["page_end"]]
                tag = (f"in records: {owners}" if owners else
                       "NOT in any record (removed footnote/header line)")
                print(f"  raw PDF page {page1}: ...{ctx!r}... [{tag}]",
                      flush=True)
        print(f"  totals: raw_pages={raw_hits}, record_hits={rec_hits}",
              flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--act", required=True, help="act_id from act_registry.yaml")
    args = ap.parse_args()

    V.ensure_dirs()
    act_id = args.act
    V.tee(f"{act_id}_step6_validate")
    print(f"seeds used: G1 middle pages {G1_SEED}; A2 removed-line sample "
          f"{A2_SEED}; A7b attachment sample {A7B_SEED}", flush=True)
    registry = V.load_registry()
    act = next((a for a in registry if a["act_id"] == act_id), None)
    if act is None:
        print(f"FATAL: act_id {act_id!r} not in {V.REGISTRY_PATH}", flush=True)
        return 2

    need = {
        "markers": V.RESULTS / f"{act_id}_markers.json",
        "clean": V.RESULTS / f"{act_id}_clean.json",
        "segments": V.RESULTS / f"{act_id}_segments.json",
        "flags": V.RESULTS / f"{act_id}_flags.json",
        "jsonl": V.OUTPUT / f"{act_id}.jsonl",
        "expected": V.RESULTS / f"{act_id}_expected.json",
        "emeta": V.RESULTS / f"{act_id}_expected_meta.json",
    }
    for label, p in need.items():
        if not p.exists():
            print(f"FATAL: {label} missing: {p}", flush=True)
            return 2
    markers = json.loads(need["markers"].read_text(encoding="utf-8"))
    clean = json.loads(need["clean"].read_text(encoding="utf-8"))
    segs = json.loads(need["segments"].read_text(encoding="utf-8"))
    flags = json.loads(need["flags"].read_text(encoding="utf-8"))
    records = [json.loads(ln) for ln in
               need["jsonl"].read_text(encoding="utf-8").splitlines() if ln]
    expected = json.loads(need["expected"].read_text(encoding="utf-8"))
    emeta = json.loads(need["emeta"].read_text(encoding="utf-8"))
    from step5_records import KEYS

    src = V.SOURCES / act["source_file"].split("/")[-1]
    doc = V.fitz.open(str(src))
    n = len(doc)
    # G6 raw reference: raw page text in the page's own line reading order
    # (sort=True); default block-index order has a ghost-whitespace-block
    # artifact documented in SPEC ASSUMPTIONS (see also diag_g6b.log).
    raw_pages = [doc[i].get_text("text", sort=True) for i in range(n)]

    print("\n" + "=" * 76, flush=True)
    print(f"STEP 6 VALIDATE {act_id}  ({act['act_name']}); pages={n}; "
          f"records={len(records)}", flush=True)
    print("=" * 76, flush=True)

    print("\nG1 identity:", flush=True)
    g1s, g1e = gate_g1(doc, act, markers)
    g2_mode = "TOC" if emeta.get("mode") == "toc" else "SEQUENCE_ONLY"
    print(f"\nG2 coverage ({g2_mode}):", flush=True)
    g2s, g2e = gate_g2(markers, records, expected, emeta)
    print("\nG3 starts with own number:", flush=True)
    g3s, g3e = gate_g3(records)
    print("\nG4 clean text:", flush=True)
    g4s, g4e = gate_g4(doc, records, n)
    print("\nG5 integrity:", flush=True)
    g5s, g5e = gate_g5(records, KEYS)

    print("\nre-scanning document for A2/G9 evidence ...", flush=True)
    scan = S.scan_document(doc, start_page=V.body_scan_start(act_id))
    print("\nG6 verbatim (A2 PRIMARY):", flush=True)
    g6s, g6e = gate_g6(doc, scan, segs, records, raw_pages)
    print("\nG7 order:", flush=True)
    g7s, g7e = gate_g7(records, markers)
    print("\nG8 size:", flush=True)
    g8s, g8e = gate_g8(records, flags)
    print("\nG9 footnote accounting:", flush=True)
    g9s, g9e = gate_g9(scan, records, segs, clean)

    # ---- A2 removed-line sample (seed 20261012) ------------------------
    pool = []
    for c in clean["sections"]:
        for r in c["removals"]:
            pool.append((c["number"], r))
    rng = random.Random(A2_SEED)
    sample = rng.sample(pool, min(20, len(pool)))
    print(f"\nA2 REMOVED-LINE SAMPLE (20 of {len(pool)}, seed {A2_SEED}):",
          flush=True)
    for num, r in sample:
        print(f"  {num}: [{r['label']}] {r['text'][:90]!r}", flush=True)
    print(f"A2 label counts: {clean['label_counts']}; unlabeled: "
          f"{clean['unlabeled_removals']}", flush=True)

    a7b_report(scan, records)
    a7c_verify(records, scan)
    typo_report(doc, records)

    gates = {
        "G1": {"status": g1s, "evidence": g1e},
        "G2": {"status": g2s, "evidence": g2e},
        "G3": {"status": g3s, "evidence": g3e},
        "G4": {"status": g4s, "evidence": g4e},
        "G5": {"status": g5s, "evidence": g5e},
        "G6": {"status": g6s, "evidence": g6e},
        "G7": {"status": g7s, "evidence": g7e},
        "G8": {"status": g8s, "evidence": g8e},
        "G9": {"status": g9s, "evidence": g9e},
    }
    print("\n" + "=" * 76, flush=True)
    print("GATE SUMMARY", flush=True)
    print("=" * 76, flush=True)
    for k, v in gates.items():
        print(f"  {k}: {v['status']}", flush=True)
    any_fail = any(v["status"] == "FAIL" for v in gates.values())
    V.write_json(V.RESULTS / f"{act_id}_gates.json",
                 {"act_id": act_id, "gates": gates,
                  "summary": "FAIL" if any_fail else "OK"})
    doc.close()
    print(f"\n[write] results/{act_id}_gates.json", flush=True)
    print(f"[exit] {'3' if any_fail else '0'}", flush=True)
    return 3 if any_fail else 0


if __name__ == "__main__":
    sys.exit(main())
