#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""pdf_profile.py - read-only structural profile of every source PDF used by HECTOR.

Rules honoured by this script:
  * reads PDFs only; writes NOTHING (all output -> stdout; the caller redirects
    to eval/results/pdf_profile.log).
  * does not touch Pinecone, Chroma, git, or any existing file.
  * on any failure: prints the exact error and stops (exit 2).
"""

import re
import sys
import math
import traceback
from pathlib import Path
from collections import Counter, defaultdict

try:
    sys.stdout.reconfigure(line_buffering=True, encoding="utf-8",
                           errors="backslashreplace")
    sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
except Exception:
    pass

try:
    import signal
    signal.signal(signal.SIGINT, signal.SIG_IGN)
except Exception:
    pass

from pypdf import PdfReader  # noqa: E402

ROOT = Path(r"D:\Vs Code\VS code\Hector")
BOOKS_DIR = ROOT / "hector" / "api" / "data" / "Books"
SKIP_PDFS = {  # copied from hector/api/scripts/reingest_full.py:22-30 (read-only)
    "fixed_Whartons_law_Lexicon.pdf",
    "fixed_The_Code_of_Criminal.pdf",
    "Textbook on The Law of Evidence (Chief Justice M Monir) (z-library.sk, 1lib.sk, z-lib.sk).pdf",
    "The Bharatiya Sakshya Adhiniyam 2023 (N Vijayaraghavan  Sharath Chandran) (z-library.sk, 1lib.sk, z-lib.sk).pdf",
    "Commentary on The Narcotic Drugs and Psychotropic Substances Act (Dr J N Barowalia  Abhishek Barowalia) (z-library.sk, 1lib.sk, z-lib.sk).pdf",
    "Fighting corruption  strategies for prevention  report of the proceedings of the Public Sector Anti-corruption Conference. ( etc.) (z-library.sk, 1lib.sk, z-lib.sk).pdf",
}

TOC_HEADER_RE = re.compile(
    r"arrangement of sections|table of contents|^\s*contents\s*$", re.I | re.M)
DOT_LEADER_RE = re.compile(r"\.{4,}")
SEC_RE = re.compile(r"^\s*(\d{1,4})[A-Za-z]?\.\s+([A-Za-z\"'(].{5,})$")
TOC_ENTRY_RE = re.compile(r"^\s*(\d{1,4})[A-Za-z]?\.\s+(\S.{6,})$")
PROVISO_RES = [
    ("proviso", re.compile(r"^\s*Provided\s+(?:that|also|further|nevertheless)", re.I)),
    ("explanation", re.compile(r"^\s*Explanation\s*(?:\d\s*)?[:.\u2014-]", re.I)),
    ("illustration", re.compile(r"^\s*Illustration\s*(?:\([a-z0-9]+\))?\s*[:.(]", re.I)),
    ("exception", re.compile(r"^\s*Exception\s*:", re.I)),
]
FOOTNOTE_RE = re.compile(
    r"^\s*(?:\d+\.\s*)?(?:Inserted by|Ins\.\s*by|Substituted for|Subs\.|Omitted by|"
    r"Amended by|Substituted|Omitted|Replaced by|w\.e\.f\.|with effect from)", re.I)
CONT_PUNCT = ",;:)]\u2014-"


def die(msg):
    print("FATAL", msg, flush=True)
    traceback.print_exc(file=sys.stdout)
    sys.exit(2)


def short(name, width=46):
    return (name[:width - 1] + "~") if len(name) > width else name


def lines_of(text):
    return [l.rstrip() for l in text.splitlines()]


def nonempty(text):
    return [l for l in lines_of(text) if l.strip()]


def sniff_category(name, first_text):
    lname = name.lower()
    if "lexicon" in lname or "wharton" in lname:
        return "dictionary", "filename: Wharton's Law Lexicon"
    if "textbook" in lname:
        return "textbook", "filename: 'Textbook ...'"
    if "commentary" in lname:
        return "commentary", "filename: 'Commentary ...'"
    if "fighting corruption" in lname:
        return "other", "filename: conference report (z-library)"
    if "z-library" in lname or "z-lib.sk" in lname:
        return "commentary", "filename: z-library book scan"
    if re.search(r"\b(act|code|constitution|sanhita|adhiniyam|ordinance|schedule)\b",
                 lname.replace("_", " ")):
        has_arr = "arrangement of sections" in first_text.lower()
        return "bare act", ("filename act-like; "
                            + ("'Arrangement of Sections' present" if has_arr
                               else "'Arrangement of Sections' NOT found in first pages"))
    if "arrangement of sections" in first_text.lower():
        return "bare act", "content: 'Arrangement of Sections'"
    return "other", "no act/filename signal"


def read_pages(path):
    reader = PdfReader(str(path))
    pages, errs = [], []
    for i, pg in enumerate(reader.pages):
        try:
            pages.append(pg.extract_text() or "")
        except Exception as exc:  # page-level corruption: report, do not hide
            pages.append("")
            if len(errs) < 3:
                errs.append(f"page {i + 1}: {type(exc).__name__}: {exc}")
    return pages, errs


def coverage(pages):
    if not pages:
        return 0.0, 0
    empty = sum(1 for t in pages if len(t.strip()) < 50)
    return 1.0 - empty / len(pages), empty


def scan_label(pages):
    frac, empty = coverage(pages)
    if frac < 0.4:
        return "SCANNED/no text", empty
    if frac < 0.85:
        return "partial text", empty
    return "text extractable", empty


def find_toc(pages):
    """Return (start, end) 0-based inclusive page range of the ToC, or None."""
    n = len(pages)
    header = [i for i, t in enumerate(pages) if TOC_HEADER_RE.search(t)]
    dots = [i for i, t in enumerate(pages) if len(DOT_LEADER_RE.findall(t)) >= 5]
    cand = set(dots)
    for h in header:
        if h < max(10, n // 3):
            cand.add(h)
            for k in range(1, 4):
                if h + k < n:
                    cand.add(h + k)
    if not cand:
        for h in header:
            if h < n // 3:
                start = h
                end = h
                while end + 1 < n:
                    body = nonempty(pages[end + 1])
                    num = sum(1 for l in body if TOC_ENTRY_RE.match(l))
                    if len(body) and num / len(body) >= 0.4:
                        end += 1
                    else:
                        break
                if end > start:
                    return (start, end)
        return None
    ordered, runs, cur = sorted(cand), [], [sorted(cand)[0]]
    for x in ordered[1:]:
        if x - cur[-1] <= 2:
            cur.append(x)
        else:
            runs.append(cur)
            cur = [x]
    runs.append(cur)
    best = max(runs, key=len)
    return (best[0], best[-1])


def toc_entries(pages, toc):
    nums = []
    if not toc:
        return nums
    for i in range(toc[0], toc[1] + 1):
        for line in nonempty(pages[i]):
            m = TOC_ENTRY_RE.match(line)
            if m and not DOT_LEADER_RE.search(line):
                nums.append(int(m.group(1)))
            elif m and DOT_LEADER_RE.search(line):
                nums.append(int(m.group(1)))
    return nums


def body_markers(pages, toc, n):
    nums, samples = set(), []
    for i, text in enumerate(pages):
        if toc and toc[0] <= i <= toc[1]:
            continue
        for line in lines_of(text):
            m = SEC_RE.match(line)
            if not m:
                continue
            v = int(m.group(1))
            if v > 999:
                continue
            nums.add(v)
            if len(samples) < 6 and (".\u2014" in line or ")." in line
                                     or len(samples) < 3):
                if line.strip() not in samples:
                    samples.append(line.strip())
    return nums, samples


def columns_label(path, pages, toc, sample_n=12):
    idx = [i for i in range(len(pages))
           if pages[i].strip() and not (toc and toc[0] <= i <= toc[1])]
    if not idx:
        return "unknown (no body pages)", None
    step = max(1, len(idx) // sample_n)
    picks = idx[::step][:sample_n]
    reader = PdfReader(str(path))
    fracs = []
    for i in picks:
        try:
            lt = reader.pages[i].extract_text(extraction_mode="layout") or ""
        except Exception:
            continue
        ls = [l.strip() for l in lt.splitlines() if l.strip()]
        if not ls:
            continue
        gap = sum(1 for l in ls if re.search(r"\S {4,}\S", l))
        fracs.append(gap / len(ls))
    if not fracs:
        return "unknown (layout extraction failed)", None
    med = sorted(fracs)[len(fracs) // 2]
    verdict = "two-column" if med >= 0.35 else "single-column"
    return f"{verdict} (median {med:.0%} of lines have an internal gap)", med


def repeated_lines(pages, toc):
    per_page = Counter()
    page_no_line_pages = set()
    for i, text in enumerate(pages):
        if toc and toc[0] <= i <= toc[1]:
            continue
        seen = set()
        for line in nonempty(text):
            norm = " ".join(line.split())
            if re.fullmatch(r"[-\u2022 ]*\d{1,4}[-\u2022 ]*", norm):
                page_no_line_pages.add(i)
                continue
            if len(norm) < 5:
                continue
            if norm in seen:
                continue
            seen.add(norm)
            per_page[norm] += 1
    body_pages = max(1, sum(1 for i in range(len(pages))
                            if not (toc and toc[0] <= i <= toc[1])))
    thresh = max(3, math.ceil(0.10 * body_pages))
    top = [(k, v) for k, v in per_page.most_common() if v >= thresh][:10]
    pnum = f"page-number-only lines on {len(page_no_line_pages)} pages" \
        if page_no_line_pages else "no page-number-only lines"
    return top, thresh, pnum


def continuation(pages, toc):
    cont, total, examples = 0, 0, []
    prev_last, prev_i = None, None
    for i, text in enumerate(pages):
        if toc and toc[0] <= i <= toc[1]:
            prev_last = None
            continue
        ne = nonempty(text)
        if not ne:
            prev_last = None
            continue
        first = ne[0].strip()
        if prev_last is not None:
            total += 1
            last = prev_last
            is_sec = bool(SEC_RE.match(first))
            mid = (not last.endswith((".", "?", "!"))
                   or first[:1].islower()
                   or (first[:1] in CONT_PUNCT and not is_sec))
            if mid and not is_sec:
                cont += 1
                if len(examples) < 3:
                    examples.append((prev_i + 1, last, i + 1, first))
        prev_last = ne[-1].strip()
        prev_i = i
    return cont, total, examples


def find_example(pages, toc, pattern, limit=2):
    out = []
    for i, text in enumerate(pages):
        if toc and toc[0] <= i <= toc[1]:
            continue
        for line in nonempty(text):
            if pattern.search(line):
                out.append(f"p{i + 1}: {line.strip()[:150]}")
                if len(out) >= limit:
                    return out
    return out


def marker_shape(samples):
    shapes = []
    for s in samples:
        if "\u2014" in s or "\u2013" in s:
            shapes.append("N. Title.<em-dash> (e.g. %r)" % s[:60])
        elif re.match(r"^\d+[A-Za-z]?\.\s+\(", s):
            shapes.append("N. (sub-clause...)")
        else:
            shapes.append("N. Title (no dash) (e.g. %r)" % s[:60])
    return shapes[:3]


def main():
    if not BOOKS_DIR.is_dir():
        raise RuntimeError(f"Books dir not found: {BOOKS_DIR}")
    pdfs = sorted(BOOKS_DIR.glob("*.pdf"))
    txts = sorted(BOOKS_DIR.glob("*.txt"))
    print("=" * 78)
    print("[0] INVENTORY")
    print("=" * 78)
    print(f"books dir : {BOOKS_DIR}")
    print(f"pdf files : {len(pdfs)}")
    print(f"txt sidecars: {len(txts)} -> {[t.name for t in txts]}")
    print("local ingest (enhanced_ingestor.py:911) ingests every *.pdf;")
    print("reingest_full.py:276 also scans *.pdf but skips SKIP_PDFS (6 files).")

    rows = []           # step 1
    detail = []         # step 2/3 per bare act
    profiles = {}       # name -> dict

    print("\n" + "=" * 78)
    print("[1] STEP 1 - every source PDF + classification (first pass: sniff)")
    print("=" * 78)

    # ---- pass 1: classify every pdf (cheap: page count + first pages sniff)
    for path in pdfs:
        reader = PdfReader(str(path))
        n = len(reader.pages)
        first = ""
        for i in range(min(3, n)):
            try:
                first += (reader.pages[i].extract_text() or "") + "\n"
            except Exception:
                pass
        cat, why = sniff_category(path.name, first)
        rows.append({
            "name": path.name, "pages": n, "category": cat, "why": why,
            "reingest": "SKIP" if path.name in SKIP_PDFS else "ingest",
            "arr": "arrangement of sections" in first.lower(),
        })
        profiles[path.name] = {"pages_n": n, "category": cat}
        print(f"  classified {short(path.name, 60)} -> {cat} ({n} pages)",
              flush=True)

    hdr = f"{'pdf':46} {'category':11} {'pages':>5} {'arr?':>4} {'reingest':>8}  why"
    print("\n" + hdr)
    print("-" * len(hdr))
    for r in rows:
        print(f"{short(r['name']):46} {r['category']:11} {r['pages']:5d} "
              f"{'Y' if r['arr'] else 'n':>4} {r['reingest']:>8}  {r['why']}")
    by_cat = Counter(r["category"] for r in rows)
    print("\ncategory counts:", dict(by_cat))

    bare = [r for r in rows if r["category"] == "bare act"]
    print(f"\nbare-act PDFs to profile in depth: {len(bare)}")

    # ---- pass 2: deep profile of every bare act
    print("\n" + "=" * 78)
    print("[2] STEP 2 - per bare act: layout, ToC, markers, footnotes, headers")
    print("=" * 78)

    for r in bare:
        path = BOOKS_DIR / r["name"]
        print(f"\n{'-' * 78}\n### {r['name']}  ({r['pages']} pages, "
              f"reingest={r['reingest']})\n{'-' * 78}", flush=True)
        pages, errs = read_pages(path)
        label, empty = scan_label(pages)
        col_label, col_med = columns_label(path, pages, None)
        toc = find_toc(pages)
        toc_range = f"p{toc[0] + 1}-p{toc[1] + 1} ({toc[1] - toc[0] + 1} pages)" \
            if toc else "NOT FOUND"
        # re-run column detection excluding ToC for a cleaner read
        col_label, col_med = columns_label(path, pages, toc)
        ent = toc_entries(pages, toc)
        nums, msamples = body_markers(pages, toc, r["pages"])
        cont_k, cont_n, cont_ex = continuation(pages, toc)
        hdr_top, thresh, pnum = repeated_lines(pages, toc)

        print(f"  text extraction     : {label} "
              f"({r['pages'] - empty}/{r['pages']} pages have >=50 chars)")
        if errs:
            for e in errs:
                print(f"  page extract error  : {e}")
        print(f"  layout              : {col_label}")
        print(f"  ToC / Arrangement   : {toc_range}")
        print(f"  section markers     : {len(nums)} distinct numbers found in body"
              f"; highest = {max(nums) if nums else 'NONE'}")
        print(f"  marker format samples:")
        for s in msamples[:6]:
            print(f"      {s}")
        for shape in marker_shape(msamples):
            print(f"      shape: {shape}")
        for name, pat in PROVISO_RES:
            ex = find_example(pages, toc, pat, 2)
            print(f"  {name} starts      : "
                  + (f"{len(ex)} sample(s)" if ex else "none found"))
            for e in ex:
                print(f"      {e}")
        fn = find_example(pages, toc, FOOTNOTE_RE, 3)
        print(f"  amendment footnotes : "
              + (f"{len(fn)} sample(s)" if fn else "none found"))
        for e in fn:
            print(f"      {e}")
        print(f"  repeated header/footer lines "
              f"(>= {thresh} body pages; {pnum}):")
        for k, v in hdr_top:
            print(f"      [{v:4d} pages] {k[:120]}")
        if not hdr_top:
            print("      (none cross the threshold)")
        print(f"  sections continue across page breaks: "
              f"{'YES' if cont_k else 'NO'} ({cont_k}/{cont_n} sampled breaks "
              f"start mid-section)")
        for pi, last, pj, first in cont_ex:
            print(f"      p{pi} last: {last[:90]}")
            print(f"      p{pj} first: {first[:90]}")

        # raw samples: one typical middle body page + one ToC page
        body_idx = [i for i in range(len(pages))
                    if not (toc and toc[0] <= i <= toc[1]) and pages[i].strip()]
        mid = body_idx[len(body_idx) // 2] if body_idx else None
        if mid is not None:
            print(f"\n  --- RAW first 40 lines of middle body page p{mid + 1} ---")
            for l in nonempty(pages[mid])[:40]:
                print(f"  |{l}")
        if toc:
            print(f"\n  --- RAW first 40 lines of ToC page p{toc[0] + 1} ---")
            for l in nonempty(pages[toc[0]])[:40]:
                print(f"  |{l}")
        else:
            print("\n  --- RAW ToC page: NOT FOUND ---")

        toc_nums = set(ent)
        detail.append({
            "name": r["name"], "pages": r["pages"], "label": label,
            "columns": col_label, "toc": toc, "toc_range": toc_range,
            "toc_entries": len(toc_nums),
            "toc_max": max(toc_nums) if toc_nums else None,
            "body_nums": nums,
            "body_max": max(nums) if nums else None,
            "cont": (cont_k, cont_n),
            "markers": msamples,
        })

    # ---- step 3
    print("\n" + "=" * 78)
    print("[3] STEP 3 - ToC expected section count vs highest section in body")
    print("=" * 78)
    hdr = (f"{'pdf':46} {'pages':>5} {'toc_rng':>14} {'toc_ent':>7} "
           f"{'toc_max':>7} {'body_max':>8} {'body_#':>7}  flag")
    print(hdr)
    print("-" * (len(hdr) + 12))
    flags = 0
    for d in detail:
        tm, bm = d["toc_max"], d["body_max"]
        if tm is None:
            flag = "FLAG: no ToC parsed"
        elif bm is None:
            flag = "FLAG: no body sections detected"
        elif tm != bm:
            flag = f"FLAG: toc_max {tm} != body_max {bm} (delta {bm - tm:+d})"
            flags += 1
        else:
            flag = "ok"
        if d["toc_entries"] and len(d["body_nums"]):
            cov = len(d["body_nums"]) / max(1, d["toc_entries"])
            if cov < 0.7:
                flag += f" | FLAG: body finds only {cov:.0%} of ToC entries"
                flags += 1
        rng = f"p{d['toc'][0] + 1}-{d['toc'][1] + 1}" if d["toc"] else "-"
        print(f"{short(d['name']):46} {d['pages']:5d} {rng:>14} "
              f"{d['toc_entries']:7d} "
              f"{str(tm):>7} {str(bm):>8} {len(d['body_nums']):7d}  {flag}")
    print(f"\nmismatch flags raised: {flags}")

    print("\n" + "=" * 78)
    print("DONE")
    print("=" * 78, flush=True)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        die("unhandled error in pdf_profile.py")
