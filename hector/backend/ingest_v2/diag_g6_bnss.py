"""Why does BNSS G6 fail on record bnss-2023:s:531:0 (and s:359:0)?

G6 primary = fraction of 60-char windows of each record's fragment text that
occur verbatim in raw_pages[page_start-1 : page_end]. raw is a SUPERSET of
the record's pages, so a miss can only be ordering/normalisation, not
missing content. G6's own diagnostics say line_rate=0.999058 (individual
lines all present) but fragment_rate=0.884545 (cross-line windows missing)
=> line ORDER differs.

This prints, for the failing records only:
  - line coverage of the segment part vs the record's page_start/page_end
  - fragment/window/failure counts
  - the first failing windows with the source line pair they span
  - for one such pair: whether the two lines are adjacent in raw sort order
  - which raw page each failing window actually lives on (whole-doc search)

Also compares the LAST record's page span vs document length for every act,
to see whether trailing schedule/form pages attached to the last section is
BNSS-specific or the normal end-of-book behaviour.
"""

import json

import v2_common as V
import v2_scanner as S
import step6_validate as G

ACTS = ["ipc-1860", "bns-2023", "bnss-2023", "bsa-2023"]


def load(act_id):
    registry = V.load_registry()
    act = next(a for a in registry if a["act_id"] == act_id)
    src = V.SOURCES / act["source_file"].split("/")[-1]
    doc = V.fitz.open(str(src))
    records = [json.loads(ln) for ln in
               (V.OUTPUT / f"{act_id}.jsonl").read_text(encoding="utf-8").splitlines()
               if ln]
    segs = json.loads((V.RESULTS / f"{act_id}_segments.json")
                      .read_text(encoding="utf-8"))
    return act, doc, records, segs


def last_record_span(act_id, doc, records):
    last = records[-1]
    print(f"  {act_id:<11} doc_pages={doc.page_count:<4} records={len(records):<4}"
          f" last_record={last['id']} pages {last['page_start']}"
          f"..{last['page_end']} "
          f"({last['page_end'] - last['page_start'] + 1} pages)", flush=True)


def detail(doc, records, segs, target_id):
    n = len(doc)
    raw_pages = [doc[i].get_text("text", sort=True) for i in range(n)]
    scan = S.scan_document(doc, start_page=V.body_scan_start("bnss-2023"))
    lines = scan["lines"]
    seg_by_num = {s["number"]: s for s in segs["sections"]}

    rec = next(r for r in records if r["id"] == target_id)
    seg = seg_by_num[rec["number"]]
    part = seg["parts"][rec["part_index"]]
    kept = part["lines"]
    pages = sorted({lines[g]["page"] + 1 for g in kept})
    print(f"\n=== {target_id} ===", flush=True)
    print(f"  record pages {rec['page_start']}..{rec['page_end']}; "
          f"segment part lines cover pages {pages[0]}..{pages[-1]} "
          f"({len(pages)} pages, {len(kept)} lines)", flush=True)
    print(f"  seg parts for this number: {len(seg['parts'])}; "
          f"record part_index={rec['part_index']}", flush=True)

    p0, p1 = rec["page_start"], rec["page_end"]
    txt = "\n".join(raw_pages[p0 - 1:p1])
    for rep in scan.get("repeat_lines") or []:
        txt = txt.replace(rep, " ")
    rawn = G.norm_raw(txt)

    frags, cur = [], []
    for k in kept:
        if cur and k != cur[-1] + 1:
            frags.append(cur)
            cur = []
        cur.append(k)
    if cur:
        frags.append(cur)
    print(f"  fragments: {len(frags)} "
          f"(sizes {sorted((len(f) for f in frags), reverse=True)[:6]})",
          flush=True)

    total = miss = 0
    examples = []
    for fi, g in enumerate(frags):
        ft, _, _, _ = S.assemble_text(lines, g)
        fn = V.norm_ws(ft)
        for w in G.chunks60(fn):
            total += 1
            if w in rawn:
                continue
            miss += 1
            if len(examples) < 6:
                examples.append((fi, g[0], g[-1], w))
    print(f"  windows={total} missing={miss} "
          f"rate={(total - miss) / total if total else 1:.4%}", flush=True)

    for fi, g0, g1, w in examples:
        print(f"\n  MISSING window (fragment {fi}, lines {g0}..{g1}):", flush=True)
        print(f"    win: {w!r}", flush=True)
        for g in range(g0, min(g1 + 1, g0 + 3)):
            print(f"    line {g} p{lines[g]['page'] + 1}: "
                  f"{lines[g]['text'][:100]!r}", flush=True)
        # where does this window live, in the whole document?
        hits = [i + 1 for i in range(n) if w in
                G.norm_raw(raw_pages[i].replace("IndiaCode", " "))]
        print(f"    found on raw pages: {hits[:12] or 'NOWHERE'}", flush=True)

    if examples:
        fi, g0, g1, _ = examples[0]
        print("\n  adjacency check for first failing pair:", flush=True)
        if g1 >= g0 + 1:
            a = V.norm_ws(lines[g0]["text"])
            b = V.norm_ws(lines[g0 + 1]["text"])
            pn = lines[g0]["page"] + 1
            raw_page = G.norm_raw(raw_pages[pn - 1].replace("IndiaCode", " "))
            print(f"    line {g0} ends {a[-60:]!r}", flush=True)
            print(f"    line {g0 + 1} starts {b[:60]!r}", flush=True)
            print(f"    both lines present individually on p{pn}: "
                  f"{a in raw_page} / {b in raw_page}", flush=True)
            ab = (a[-40:] + " " + b[:40])
            print(f"    crossing string present on p{pn}: "
                  f"{ab in raw_page}", flush=True)


print("=== last-record span per act ===", flush=True)
for aid in ACTS:
    _, doc, recs, _ = load(aid)
    last_record_span(aid, doc, recs)
    doc.close()

print("\n=== BNSS failing records ===", flush=True)
_, doc, recs, segs = load("bnss-2023")
for tid in ("bnss-2023:s:531:0", "bnss-2023:s:359:0"):
    detail(doc, recs, segs, tid)
doc.close()
