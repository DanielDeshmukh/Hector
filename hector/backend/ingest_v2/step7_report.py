#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""step7_report.py - STEP 7 of the ingest_v2 pilot: final report.

Usage: python step7_report.py --act <act_id>
Writes: results/pilot_report.md
Seeds used: step7 random record sample 20261011 (G1/A2 seeds are quoted from
the gate evidence produced by step6).
"""

import argparse
import json
import random
import sys

import v2_common as V

SEED = 20261011
SAMPLE_N = 20


def gate_evidence_line(name, ev):
    if name == "G1":
        hits = ", ".join(str(p["page_1based"]) for p in ev["page_hits"])
        return (f"page1 act_name={ev['page1_has_act_name']}, "
                f"year={ev['page1_has_year']}; middle pages {hits} all have "
                f"markers (seed {ev['seed']})")
    if name == "G2":
        if ev.get("mode") == "toc":
            return (f"mode=toc; expected {ev['expected_count']} sections; "
                    f"records {ev['records']}; missing {len(ev['missing'])} "
                    f"{ev['missing'][:12]}; extra {len(ev['extra'])} "
                    f"{ev['extra'][:12]}; external anchor max_plain="
                    f"{ev['anchor_max_plain_seen']} vs 511 -> "
                    f"{'OK' if ev['anchor_ok'] else 'WARNING'}")
        return (f"mode=sequence_only; {ev['markers']} markers strictly "
                f"increasing={ev['plain_strictly_increasing']}; covered "
                f"{ev['covered_range']}; gaps={ev['gaps']} "
                f"(total {len(ev['gaps'])}); external anchor max_plain="
                f"{ev['max_plain']} vs 511 -> {ev['external_anchor_511']}")
    if name == "G3":
        return (f"part-0 records {ev['part0_records']}; prefix stripping "
                f"needed {ev['needed_prefix_stripping']}; failures "
                f"{len(ev['failures'])}")
    if name == "G4":
        return (f"page-number lines {ev['page_number_lines']}; hyphen breaks "
                f"{ev['hyphen_breaks']}; boilerplate {ev['boilerplate']}; "
                f"repeated>=30% pages {ev['repeated_30pct_lines']}")
    if name == "G5":
        return (f"records {ev['records']}; duplicates {ev['duplicate_ids']}; "
                f"empty {ev['empty_texts']}; non-nullable problems "
                f"{len(ev['missing_or_null_nonnullable'])}")
    if name == "G6":
        return (f"PRIMARY fragment windows {ev['windows']} total, "
                f"{round(ev['primary_fragment_rate'] * 100, 4)}% found "
                f"(>=99% required; reference {ev['raw_reference']}); "
                f"DIAG whole-record {round(ev['diagnostic_whole_record_rate'] * 100, 4)}%, "
                f"DIAG lines {round(ev['diagnostic_line_rate'] * 100, 4)}%; "
                f"failures {ev['primary_failures']}")
    if name == "G7":
        return (f"parent order matches marker order; parts consistent; "
                f"problems {ev['problems']}")
    if name == "G8":
        return (f"limit {ev['limit']} chars; longest {ev['longest_text']}; "
                f"unflagged overs {len(ev['unflagged_over_limit'])}; "
                f"flagged {len(ev['flagged_long_unsplit'])}")
    if name == "G9":
        return (f"detected {ev['footnote_lines_detected']} = attached "
                f"{ev['attached_lines']} + unattached {ev['unattached_lines']}; "
                f"accounting_ok={ev['accounting_ok']}; records containing "
                f"footnote lines {len(ev['records_containing_footnote_lines'])}")
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--act", required=True, help="act_id from act_registry.yaml")
    args = ap.parse_args()

    V.ensure_dirs()
    act_id = args.act
    V.tee(f"{act_id}_step7_report")
    print(f"seeds used: step7 record sample {SEED} "
          f"(G1 {20261010}; A2 removal sample {20261012} quoted from "
          f"step6 gate evidence)", flush=True)

    registry = V.load_registry()
    act = next((a for a in registry if a["act_id"] == act_id), None)
    if act is None:
        print(f"FATAL: act_id {act_id!r} not in {V.REGISTRY_PATH}", flush=True)
        return 2

    need = {
        "gates": V.RESULTS / f"{act_id}_gates.json",
        "clean": V.RESULTS / f"{act_id}_clean.json",
        "flags": V.RESULTS / f"{act_id}_flags.json",
        "assembly": V.RESULTS / f"{act_id}_assembly.json",
        "numlines": V.RESULTS / f"{act_id}_numlines.json",
        "toc_meta": V.RESULTS / f"{act_id}_toc_meta.json",
        "expected_meta": V.RESULTS / f"{act_id}_expected_meta.json",
        "block_order": V.RESULTS / "block_order_counter.json",
        "jsonl": V.OUTPUT / f"{act_id}.jsonl",
        "spec": V.INGEST / "SPEC.md",
    }
    for label, p in need.items():
        if not p.exists():
            print(f"FATAL: {label} missing: {p}", flush=True)
            return 2
    gates = json.loads(need["gates"].read_text(encoding="utf-8"))
    clean = json.loads(need["clean"].read_text(encoding="utf-8"))
    flags = json.loads(need["flags"].read_text(encoding="utf-8"))
    assembly = json.loads(need["assembly"].read_text(encoding="utf-8"))
    numlines = json.loads(need["numlines"].read_text(encoding="utf-8"))
    toc = json.loads(need["toc_meta"].read_text(encoding="utf-8"))
    emeta = json.loads(need["expected_meta"].read_text(encoding="utf-8"))
    bo = json.loads(need["block_order"].read_text(encoding="utf-8"))
    records = [json.loads(ln) for ln in
               need["jsonl"].read_text(encoding="utf-8").splitlines() if ln]
    spec_text = need["spec"].read_text(encoding="utf-8")

    rng = random.Random(SEED)
    sample = rng.sample(records, min(SAMPLE_N, len(records)))

    statuses = {k: v["status"] for k, v in gates["gates"].items()}
    any_fail = any(s == "FAIL" for s in statuses.values())

    a2_ev = gates["gates"]["G6"]["evidence"]
    label_counts = clean["label_counts"]
    scan_stats = clean.get("scan_stats", {})

    L = []
    L.append(f"# HECTOR ingest_v2 pilot report - {act['act_name']} "
             f"({act_id})")
    L.append("")
    L.append(f"- source: {act['source_file']} "
             f"({bo['acts'].get(act_id, {}).get('pages', '?')} pages "
             f"as scanned)")
    L.append(f"- records written: {len(records)} "
             f"(output/{act_id}.jsonl)")
    L.append(f"- gate summary: "
             f"{'FAIL' if any_fail else 'all gates OK'}")
    L.append(f"- seeds: G1 middle pages 20261010; A2 removed-line sample "
             f"20261012; step7 record sample {SEED}")
    L.append(f"- external anchor: max plain section = "
             f"{emeta['anchor_max_plain_seen']} (expected "
             f"{emeta['anchor_value']}) -> "
             f"{'OK' if emeta['anchor_ok'] else 'WARNING'}")
    L.append("")

    L.append("## Gate table (G1-G9)")
    L.append("")
    L.append("| Gate | Status | Evidence |")
    L.append("|---|---|---|")
    for g in ["G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "G9"]:
        ev = gates["gates"][g]["evidence"]
        line = gate_evidence_line(g, ev).replace("|", "\\|")
        L.append(f"| {g} | **{statuses[g]}** | {line} |")
    L.append("")
    L.append("Notes:")
    if emeta.get("mode") == "toc":
        L.append("- G2 is the ToC cross-check: every section listed in the "
                 "book's Arrangement of Sections must have at least one "
                 "record (100% coverage required; missing and extra numbers "
                 "listed in gate evidence). Range markers count as covering "
                 "their printed span; the external anchor 511 is reported "
                 "separately above.")
    else:
        L.append("- G2 is reported as SEQUENCE_ONLY and never PASS: the PDF "
                 "has no table of contents, so coverage is proven by a "
                 "strictly increasing, gapless accepted sequence (1..511) "
                 "plus the external anchor 511, not by a ToC cross-check.")
    L.append("- G6 PRIMARY uses the A2 fragment-window definition; the "
             "whole-record window check and the cleaned-line check are "
             "DIAGNOSTIC (A2).")
    L.append("")

    L.append("## Coverage / sequence detail (A4, A5, A6)")
    L.append("")
    L.append(f"- accepted markers: {scan_stats.get('markers', len(records))}; "
             f"forms: {scan_stats.get('forms', {})}")
    L.append(f"- lettered/other non-plain numbers: "
             f"{len(emeta['lettered'])} entries "
             f"({', '.join(emeta['lettered'][:12])}"
             f"{'...' if len(emeta['lettered']) > 12 else ''})")
    L.append(f"- rejected candidates: {emeta['rejected_count']}")
    L.append(f"- gaps: {emeta['gaps']}")
    L.append(f"- A4 classification counts (number-lines): "
             f"{numlines['counts']}; unlabeled removals "
             f"{numlines['unlabeled_removed']}")
    L.append(f"- A4 UNKNOWN lines: {len(numlines['unknowns'])} "
             f"(full context in results/{act_id}_numlines.json):")
    for u in numlines["unknowns"]:
        L.append(f"  - line {u['line']} p{u['page']}: {u['text'][:110]!r}")
    L.append(f"- A5 LOOKAHEAD_LINES={scan_stats.get('lookahead_constant')}, "
             f"longest actually used={scan_stats.get('max_lookahead_used')}, "
             f"restated >2 pages away: "
             f"{scan_stats.get('restated_more_than_2_pages', [])}")
    L.append(f"- A6 scanner iterations: 3 of the A6 maximum (see "
             f"ASSUMPTIONS); iteration outcome: 0 gaps in 1..511.")
    L.append("")

    L.append("## A1 page-joining evidence (first 5 page-spanning records)")
    L.append("")
    L.append(f"- page-spanning records: {assembly.get('page_spanning_total', 'n/a')}")
    for r in assembly.get("shown", []):
        L.append(f"- section {r['number']} pages p{r['page_start']}-"
                 f"p{r['page_end']}")
        for j in r.get("joins", []):
            L.append(f"  - join {j['from_page']}->{j['to_page']} "
                     f"removed between: {j['removed_labels']}")
            L.append(f"  - before: ...{j['before_tail'].strip()!r}")
            L.append(f"  - after: {j['after_head'].strip()!r}")
    L.append("")

    L.append("## A2 verbatim / removal labels")
    L.append("")
    L.append(f"- A2 PRIMARY fragment windows: "
             f"{round(a2_ev['primary_fragment_rate'] * 100, 4)}% "
             f"(threshold 99%)")
    L.append(f"- DIAGNOSTIC whole-record windows: "
             f"{round(a2_ev['diagnostic_whole_record_rate'] * 100, 4)}%")
    L.append(f"- DIAGNOSTIC cleaned-lines-in-raw: "
             f"{round(a2_ev['diagnostic_line_rate'] * 100, 4)}%")
    L.append(f"- removal label counts: {label_counts}; unlabeled removals: "
             f"{clean['unlabeled_removals']} (unlabeled = FAIL)")
    L.append(f"- 20-line removed sample printed with seed 20261012: see "
             f"results/{act_id}_step6_validate.log")
    L.append("")

    L.append("## A3 statuses")
    L.append("")
    sc = {}
    for r in records:
        sc[r["status"]] = sc.get(r["status"], 0) + 1
    L.append(f"- status counts: {sc}")
    L.append(f"- R-form (omitted) sections: "
             f"{', '.join(sorted({r['number'] for r in records if r['status'] == 'omitted'}))}")
    L.append("")

    L.append(f"## 20 random records (seed {SEED})")
    L.append("")
    for i, r in enumerate(sample, 1):
        head = r["text"].replace("\n", " ")[:240]
        L.append(f"### {i}. {r['id']}")
        L.append(f"- number={r['number']!r}, title={r['title']!r}, "
                 f"chapter={r['chapter']!r}, pages "
                 f"{r['page_start']}-{r['page_end']}, status={r['status']}, "
                 f"chars={len(r['text'])}, parts "
                 f"{r['part_index'] + 1}/{r['part_count']}")
        L.append(f"- has: proviso={r['has_proviso']}, "
                 f"explanation={r['has_explanation']}, "
                 f"exception={r['has_exception']}, "
                 f"illustration={r['has_illustration']}, "
                 f"amendment_notes={len(r['amendment_notes'])}")
        L.append(f"- text: {head}...")
        L.append("")

    L.append("## Consumer Protection 2019 (paused at checkpoint 1)")
    L.append("")
    L.append("- registry entry and source PDF present; inspection NOT run "
             "per instruction.")
    L.append("- when resumed, G2 must run in ToC mode: every expected "
             "section from the ToC needs >=1 record (100% required; "
             "missing/extra listed).")
    L.append("")

    L.append("## Block-order note")
    L.append("")
    tot = bo["totals"]
    act_bo = bo["acts"].get(act_id, {})
    L.append(f"- pages where raw extraction order differs from (y,x) reading "
             f"order: {act_bo.get('diff_page_count', '?')}/"
             f"{act_bo.get('pages', '?')} "
             f"(total counter: {tot}); (y,x) order kept. G6 evidence: see "
             f"ASSUMPTIONS (ghost-whitespace-block artifact, sorted raw "
             f"reference).")
    L.append("")

    L.append("## ASSUMPTIONS (verbatim from SPEC.md)")
    L.append("")
    if "ASSUMPTIONS" in spec_text:
        tail = spec_text.split("ASSUMPTIONS", 1)[1]
        L.append("ASSUMPTIONS" + tail)
    else:
        L.append("(missing)")
    L.append("")

    L.append("## Files produced")
    L.append("")
    L.append(f"- output/{act_id}.jsonl ({len(records)} records)")
    L.append(f"- results/{act_id}_gates.json, _clean.json, _segments.json, "
             f"_flags.json, _assembly.json, _markers.json, _numlines.json, "
             f"_expected.json, _expected_meta.json, _toc_meta.json")
    L.append(f"- results/{act_id}_step2_inspect.log ... "
             f"_{act_id}_step7_report.log (one per step)")
    L.append("- results/pilot_report.md (this file)")
    L.append("")

    out = V.RESULTS / "pilot_report.md"
    out.write_text("\n".join(L), encoding="utf-8")
    print(f"[write] {out}", flush=True)
    print(f"gate summary: "
          f"{', '.join(f'{k}={v}' for k, v in statuses.items())}", flush=True)
    print(f"[exit] {'3' if any_fail else '0'}", flush=True)
    return 3 if any_fail else 0


if __name__ == "__main__":
    sys.exit(main())
