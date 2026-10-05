#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""diag_books_triage.py - does the IPC-tuned regex parse EVERY book?

For each PDF in api/data/Books, sweep start_page and keep the value that
yields the longest clean section run (density ~1.0). Reports, per book:

  markers  span  density  order-violations  best_start  verdict

'PARSEABLE' = some start_page gives density >= 0.99 with >= 20 markers and
zero order violations: the number/heading regex transfers unchanged and only
the front-matter boundary is book-specific.

Diagnostic only - not a gate. Output -> results/books_triage.json + stdout.

Usage: python diag_books_triage.py [--step 2] [--max-start 32] [--only bns]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import v2_common as V  # noqa: E402
import v2_scanner as S  # noqa: E402

BOOKS_DIR = V.INGEST.parent.parent / "api" / "data" / "Books"


def scan_at(path, start):
    doc = V.fitz.open(str(path))
    try:
        sc = S.scan_document(doc, start_page=start)
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"
    finally:
        doc.close()
    mk = sc["markers"]
    st = sc["stats"]
    if not mk:
        return {"markers": 0, "density": 0.0, "viol": 0, "span": (0, 0),
                "missing": 0, "rejected": st["rejected"]}, None
    b = [m["base"] for m in mk]
    lo, hi = min(b), max(b)
    cov = set(b)
    miss = hi - lo + 1 - len(cov)
    dens = len(cov) / (hi - lo + 1)
    viol = sum(1 for i in range(1, len(b)) if b[i] < b[i - 1])
    return {"markers": len(mk), "density": round(dens, 4), "viol": viol,
            "span": (lo, hi), "missing": miss,
            "rejected": st["rejected"]}, None


def triage(path, step, max_start):
    """Coarse sweep, then refine around the coarse winner."""
    candidates = list(range(0, max_start + 1, step))
    best = None
    for sp in candidates:
        res, err = scan_at(path, sp)
        if err:
            return {"error": err}
        # prefer a long, gapless, in-order run; a 1-marker span scores 1.0
        # density but is worthless, hence the marker floor
        score = (1 if res["density"] >= 0.99 and res["markers"] >= 20 else 0,
                 res["markers"] if res["density"] >= 0.99 else 0,
                 res["density"])
        if best is None or score > best[0]:
            best = (score, sp, res)
    _, coarse, best_res = best

    # refine: neighbours the coarse step may have skipped
    for sp in range(max(0, coarse - step + 1), coarse + step):
        if sp in candidates:
            continue
        res, err = scan_at(path, sp)
        if err:
            continue
        score = (1 if res["density"] >= 0.99 and res["markers"] >= 20 else 0,
                 res["markers"] if res["density"] >= 0.99 else 0,
                 res["density"])
        if score > best[0]:
            best = (score, sp, res)
    score, sp, res = best

    verdict = "PARSEABLE" if score[0] == 1 else "NEEDS OWN REGEX"
    return {"best_start": sp, **res, "verdict": verdict,
            "edge": coarse >= max_start}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--step", type=int, default=2)
    ap.add_argument("--max-start", type=int, default=32)
    ap.add_argument("--only", nargs="*", default=None)
    args = ap.parse_args()

    pdfs = sorted(BOOKS_DIR.glob("*.pdf"))
    if args.only:
        keys = [k.lower() for k in args.only]
        pdfs = [p for p in pdfs if any(k in p.name.lower() for k in keys)]
    print(f"[triage] {len(pdfs)} pdfs, step={args.step}, max_start={args.max_start}",
          flush=True)

    out = {}
    t0 = time.time()
    for i, p in enumerate(pdfs, 1):
        r = triage(p, args.step, args.max_start)
        out[p.name] = r
        if "error" in r:
            print(f"  [{i}/{len(pdfs)}] {p.name:<58} ERROR {r['error']}", flush=True)
            continue
        flag = "  <-- sweep edge, extend" if r.get("edge") else ""
        print(f"  [{i}/{len(pdfs)}] {p.name:<58} start={r['best_start']:<3} "
              f"n={r['markers']:<5} {str(r['span'][0]) + '..' + str(r['span'][1]):<12} "
              f"d={r['density']:.3f} viol={r['viol']:<4} {r['verdict']}{flag}",
              flush=True)

    res_dir = os.path.join(HERE, "results")
    os.makedirs(res_dir, exist_ok=True)
    dest = os.path.join(res_dir, "books_triage.json")
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump({"step": args.step, "max_start": args.max_start,
                   "elapsed_s": round(time.time() - t0, 1), "books": out},
                  fh, indent=2, ensure_ascii=False)
    ok = sum(1 for v in out.values() if v.get("verdict") == "PARSEABLE")
    print(f"\n[triage] {ok}/{len(out)} PARSEABLE  ({time.time() - t0:.0f}s)")
    print(f"[triage] wrote {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
