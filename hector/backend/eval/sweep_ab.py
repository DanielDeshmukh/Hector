"""A/B recall+latency sweep for retrieval configuration changes.

Baseline config (pool=30, local cross-encoder rerank) measured in iter4:
  retrieve p50 = 5459ms  (dense 2935 + rerank 2541 + ~60ms local)
Budget is 2-5s retrieval-only, so this tests what each lever actually buys
and what it costs in section_recall@10 (gate >= 0.98, currently 198/198).

    python sweep_ab.py base
    python sweep_ab.py norerank
    python sweep_ab.py pool15   (any pool<N> works, default pool=30)
    python sweep_ab.py pool15_norerank
"""

import json
import os
import re
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

os.environ["HECTOR_GOLD_PATH"] = str(EVAL / "gold_iteration1.jsonl")
os.environ["HECTOR_EVAL_CORPUS"] = str(
    EVAL.parent / "ingest_v2" / "output" / "eval_corpus.jsonl")
os.environ["HECTOR_EVAL_INDEX"] = "hector"

import run_gold_eval as rge  # noqa: E402

SAMPLE = int(os.getenv("SWEEP_SAMPLE", "200"))
SEED = int(os.getenv("SWEEP_SEED", "20261013"))
MODE = (sys.argv[1] if len(sys.argv) > 1 else "base").lower()
GATE = 0.98


def pct(v, p):
    v = sorted(v)
    return v[min(int(len(v) * p), len(v) - 1)] if v else 0.0


def main():
    rge.GOLD_SAMPLE = SAMPLE
    rge.GOLD_SAMPLE_SEED = SEED
    gold = rge.load_gold()
    stack = rge.build_stack()
    ret = stack["retriever"]
    expander = stack["expander"]

    pool = rge.CANDIDATE_POOL
    m = re.search(r"pool(\d+)", MODE)
    if m:
        pool = int(m.group(1))
    if "norerank" in MODE:
        ret.reranker_disabled = True

    print(f"[sweep-ab] mode={MODE} pool={pool} "
          f"reranker_disabled={ret.reranker_disabled} "
          f"n={len(gold)} top_k={rge.TOP_K}", flush=True)

    total = hits = 0
    misses = []
    dense_ms, rerank_ms, total_ms = [], [], []
    # Which reranker path actually produced each result set (silent
    # fallbacks made earlier sweeps indistinguishable from norerank).
    flags = {"api": 0, "ce": 0, "disabled": 0, "other": 0}
    t0 = time.time()
    for i, g in enumerate(gold, 1):
        specs = g.get("expected_sections") or []
        if not specs:
            continue
        try:
            expanded = expander.expand(g["question"])
        except Exception as exc:
            print(f"  expand failed {g['id']}: {exc}")
            expanded = ""
        query = expanded or g["question"]
        try:
            chunks = ret.search(
                query, top_k=rge.TOP_K, candidate_pool=pool,
                raw_query=g["question"],
            )
        except Exception as exc:
            print(f"  search failed {g['id']}: {type(exc).__name__}: {exc}")
            chunks = []
        reasons_list = [c.get("reasons") or [] for c in chunks]
        if any(
            ("nim-reranked" in r) or ("groq-reranked" in r)
            for r in reasons_list
        ):
            flags["api"] += 1
        elif any("cross-encoder-unavailable" in r for r in reasons_list):
            flags["ce"] += 1
        elif any("reranker-disabled" in r for r in reasons_list):
            flags["disabled"] += 1
        else:
            flags["other"] += 1
        t = ((ret.last_stage_info or {}).get("timings_ms") or {})
        if t.get("dense_ms"):
            dense_ms.append(t["dense_ms"])
        if t.get("rerank_ms"):
            rerank_ms.append(t["rerank_ms"])
        if t.get("total_ms"):
            total_ms.append(t["total_ms"])
        for spec in specs:
            total += 1
            hit = any(rge.section_hit(c.get("document"), c.get("metadata"), spec)
                      for c in chunks)
            hits += hit
            if not hit:
                misses.append((g["id"], spec, g["question"][:70]))
        # Groq rate limits throttle back-to-back rerank calls (20-50s
        # queueing observed at ~120 RPM); pace the sweep to stay polite.
        if os.getenv("SWEEP_RERANK_PAUSE_S"):
            time.sleep(float(os.environ["SWEEP_RERANK_PAUSE_S"]))
        if i % 25 == 0:
            print(f"  [{i}/{len(gold)}] recall-so-far {hits}/{total} "
                  f"rerank-path api/ce/disabled/other="
                  f"{flags['api']}/{flags['ce']}/{flags['disabled']}/{flags['other']}",
                  flush=True)

    recall = hits / total if total else 0.0
    print(f"\n=== mode={MODE} ===")
    print(f"section_recall@10 = {hits}/{total} = {recall:.4f}")
    print(f"rerank-path counts: api={flags['api']} ce-fallback={flags['ce']} "
          f"disabled={flags['disabled']} other={flags['other']} of {len(gold)}")
    print(f"gate >= {GATE:.4f} -> {'PASS' if recall >= GATE else 'FAIL'}")
    print(f"latency ms: dense p50={pct(dense_ms,.5):.0f} "
          f"rerank p50={pct(rerank_ms,.5):.0f} "
          f"total p50={pct(total_ms,.5):.0f} "
          f"total p95={pct(total_ms,.95):.0f}")
    if misses:
        print(f"\nmisses ({len(misses)}):")
        for qid, spec, q in misses:
            print(f"   {qid:<16} {spec:<10} {q}")
    print(f"\nelapsed {time.time()-t0:.0f}s")

    out = {"mode": MODE, "pool": pool, "reranker_disabled":
           ret.reranker_disabled, "hits": hits, "total": total,
           "recall": recall, "pass": recall >= GATE,
           "rerank_path_flags": flags,
           "dense_p50": pct(dense_ms, .5), "rerank_p50": pct(rerank_ms, .5),
           "total_p50": pct(total_ms, .5), "total_p95": pct(total_ms, .95),
           "misses": misses, "elapsed_s": round(time.time() - t0)}
    path = EVAL / "results" / f"ab_{MODE}.json"
    path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"wrote {path}")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("[FATAL] sweep aborted:", file=sys.stderr)
        traceback.print_exc()
        raise
    finally:
        sys.stdout.flush()
        sys.stderr.flush()
