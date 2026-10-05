"""Retrieval-only section_recall@10 sweep over the real eval sample.

Runs the exact gold subset the eval selects (GOLD_SAMPLE=200,
GOLD_SAMPLE_SEED=20261013) through expand -> search -> section_hit, with no
generation, so gate 1 can be measured before spending tokens.

Reports hits/total, projected recall, and every miss."""

import json
import os
import sys
import time
import traceback
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
EVAL = Path(__file__).resolve().parent
ROOT = EVAL.parents[2]
for p in (ROOT / "hector" / "api", ROOT / "hector" / "backend", ROOT / "hector"):
    sys.path.insert(0, str(p))
for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
    s = line.strip()
    if s and not s.startswith("#") and "=" in s:
        k, _, v = s.partition("=")
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

# run_gold_eval reads GOLD_PATH at import time, so this must be set BEFORE the
# import or the sweep silently scores the 60-row default file instead. A
# pre-set HECTOR_GOLD_PATH wins, so one-off golds (bns, compare) can be swept
# with: HECTOR_GOLD_PATH=... SWEEP_SAMPLE=... python sweep_recall.py
os.environ.setdefault("HECTOR_GOLD_PATH", str(EVAL / "gold_iteration1.jsonl"))
os.environ["HECTOR_EVAL_CORPUS"] = str(
    EVAL.parent / "ingest_v2" / "output" / "eval_corpus.jsonl")
os.environ["HECTOR_EVAL_INDEX"] = "hector"

import run_gold_eval as rge  # noqa: E402

SAMPLE = int(os.getenv("SWEEP_SAMPLE", "200"))
SEED = int(os.getenv("SWEEP_SEED", "20261013"))


def main():
    rge.GOLD_SAMPLE = SAMPLE
    rge.GOLD_SAMPLE_SEED = SEED
    gold = rge.load_gold()
    print(f"[sweep] {len(gold)} questions (sample={SAMPLE}, seed={SEED})")

    stack = rge.build_stack()
    ret, expander = stack["retriever"], stack["expander"]
    print("[stack] ready", flush=True)

    total = hits = 0
    misses = []
    t0 = time.time()
    for i, g in enumerate(gold, 1):
        specs = g.get("expected_sections") or []
        if not specs:
            continue
        expanded = ""
        try:
            expanded = expander.expand(g["question"])
        except Exception as exc:
            print(f"  expand failed {g['id']}: {exc}")
        query = expanded or g["question"]
        try:
            chunks = ret.search(query, top_k=rge.TOP_K,
                                candidate_pool=rge.CANDIDATE_POOL,
                                raw_query=g["question"])
        except Exception as exc:
            print(f"  search failed {g['id']}: {type(exc).__name__}: {exc}")
            chunks = []
        for spec in specs:
            total += 1
            hit = any(rge.section_hit(c.get("document"), c.get("metadata"), spec)
                      for c in chunks)
            hits += hit
            if not hit:
                misses.append((g["id"], spec, g["question"][:70]))
        if i % 20 == 0:
            rate = i / max(1e-9, time.time() - t0)
            print(f"  [{i}/{len(gold)}] {total - hits}/{total} missed so far"
                  f"  ({rate:.2f} q/s, eta {(len(gold) - i) / max(rate, 1e-9) / 60:.1f} min)")

    recall = hits / total if total else 0.0
    print(f"\n=== section_recall@10 = {hits}/{total} = {recall:.4f} ===")
    print(f"gate >= 0.9800 -> {'PASS' if recall >= 0.98 else 'FAIL'}"
          f"  (need >= {-(-int(0.98 * total) // 1)} hits)")
    if misses:
        print(f"\nmisses ({len(misses)}):")
        for qid, spec, q in misses:
            print(f"   {qid:<16} {spec:<10} {q}")
    print(f"\nelapsed {time.time() - t0:.0f}s")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("[FATAL] sweep aborted:", file=sys.stderr)
        traceback.print_exc()
        sys.stderr.flush()
        raise
    finally:
        sys.stdout.flush()
        sys.stderr.flush()
