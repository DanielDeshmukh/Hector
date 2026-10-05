"""bench_retrieval.py - where does per-query retrieval latency come from?

Splits dense_ms (embed vs pinecone vs retry) and rerank_ms (candidate pool),
measures warm/cold, and shows what concurrency buys. Diagnostic only.

Usage: python bench_retrieval.py [--n 5] [--pool 30]
"""
from __future__ import annotations

import argparse
import json
import os
import statistics as st
import sys
import time
from concurrent.futures import ThreadPoolExecutor

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

QUERIES = [
    "What does Section 302 of the Indian Penal Code provide?",
    "How does the Indian Penal Code deal with theft?",
    "According to Section 498A of the Indian Penal Code, what is the law on cruelty?",
    "Explain Section 420 of the Indian Penal Code (cheating)",
    "What treatment does the Indian Penal Code provide for criminal conspiracy?",
    "State the provisions of Section 144 of the Indian Penal Code",
]


def log(m):
    print(f"[bench] {m}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=5, help="warm repeats per query")
    ap.add_argument("--pool", type=int, default=30, help="candidate_pool")
    args = ap.parse_args()

    # ---- build the same stack the eval harness uses -------------------
    os.environ.setdefault(
        "HECTOR_EVAL_CORPUS",
        os.path.join(SCRIPT_DIR, "..", "ingest_v2", "output", "eval_corpus.jsonl"),
    )
    os.environ.setdefault("HECTOR_EVAL_INDEX", "hector")
    sys.path.insert(0, SCRIPT_DIR)
    from run_gold_eval import build_stack

    stack = build_stack()
    r = stack["retriever"]

    # ---- 1. embed -----------------------------------------------------
    t = time.time()
    v = r._embed_text(QUERIES[0])
    embed_cold = (time.time() - t) * 1000
    ts = []
    for q in QUERIES:
        t = time.time()
        r._embed_text(q)
        ts.append((time.time() - t) * 1000)
    log(f"embed: cold={embed_cold:.0f}ms  warm mean={st.mean(ts):.0f}ms "
        f"min={min(ts):.0f} max={max(ts):.0f}  dim={len(v) if v else 0}")

    # ---- 2. pinecone query alone -------------------------------------
    pc_times = []
    for q in QUERIES:
        vec = r._embed_text(q)
        t = time.time()
        r._pinecone.query(vector=vec, top_k=10, include_metadata=True)
        pc_times.append((time.time() - t) * 1000)
    log(f"pinecone.query alone: mean={st.mean(pc_times):.0f}ms "
        f"min={min(pc_times):.0f} max={max(pc_times):.0f}")

    # ---- 3. concurrency on the network leg ---------------------------
    vecs = [r._embed_text(q) for q in QUERIES]

    def pq(vec):
        t = time.time()
        r._pinecone.query(vector=vec, top_k=10, include_metadata=True)
        return (time.time() - t) * 1000

    for workers in (1, 4, 8):
        t = time.time()
        with ThreadPoolExecutor(max_workers=workers) as ex:
            list(ex.map(pq, vecs * 4))
        n = len(vecs) * 4
        wall = (time.time() - t) * 1000
        log(f"  pinecone x{n} workers={workers}: wall={wall:.0f}ms "
            f"({wall / n:.0f}ms/query effective)")

    # ---- 4. full search + stage timings ------------------------------
    per_stage = {}
    for _ in range(args.n):
        for q in QUERIES:
            t = time.time()
            r.search(q, top_k=10, candidate_pool=args.pool)
            total = (time.time() - t) * 1000
            si = getattr(r, "last_stage_info", None) or {}
            for k, val in (si.get("timings_ms") or {}).items():
                per_stage.setdefault(k, []).append(val)
            per_stage.setdefault("wall_search", []).append(total)

    log(f"full search (pool={args.pool}), warm x{args.n * len(QUERIES)}:")
    for k in ("bm25_ms", "dense_ms", "rerank_ms", "score_ms", "fuse_ms",
              "total_ms", "wall_search"):
        if per_stage.get(k):
            v2 = per_stage[k]
            log(f"  {k:12} mean={st.mean(v2):8.0f}ms  median={st.median(v2):8.0f}")

    # ---- 5. rerank scaling -------------------------------------------
    for pool in (10, 30, 60):
        tt = []
        for q in QUERIES:
            t = time.time()
            r.search(q, top_k=10, candidate_pool=pool)
            si = getattr(r, "last_stage_info", None) or {}
            tt.append((si.get("timings_ms") or {}).get("rerank_ms", 0))
        log(f"  rerank pool={pool:3}: mean={st.mean(tt):8.0f}ms")

    log("done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
