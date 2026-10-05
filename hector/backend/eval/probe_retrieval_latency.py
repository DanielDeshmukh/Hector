"""Split retrieval latency into embed / Pinecone / rerank to find the real lever.

stage_latencies.py showed dense_ms p50=2935 and rerank_ms p50=2541 dominate
the 5459ms p50, with bm25+scoring ~60ms. This probe separates the two remote
calls inside dense (NIM embed vs Pinecone query) and sizes the rerank payload.

    python probe_retrieval_latency.py [n_questions]
"""

import os
import sys
import time
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


def med(v):
    v = sorted(v)
    return v[len(v) // 2] if v else 0.0


def main(n_questions):
    rge.GOLD_SAMPLE = 200
    rge.GOLD_SAMPLE_SEED = 20261013
    gold = rge.load_gold()[:n_questions]
    stack = rge.build_stack()
    ret = stack["retriever"]
    print(f"[probe] {len(gold)} questions, top_k={rge.TOP_K}, "
          f"pool={rge.CANDIDATE_POOL}", flush=True)

    embed_ms, sem_ms, rerank_ms, full_ms = [], [], [], []
    rerank_sizes = []
    rows = []
    for i, g in enumerate(gold, 1):
        q = g["question"]

        t0 = time.perf_counter()
        ret._embed_text(q)
        e = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        sem = ret._semantic_search(q, rge.CANDIDATE_POOL)
        s = (time.perf_counter() - t0) * 1000

        dedup = ret._deduplicate_results(sem)
        t0 = time.perf_counter()
        ret._rerank_with_cross_encoder(q, dedup)
        r = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        ret.search(q, top_k=rge.TOP_K, candidate_pool=rge.CANDIDATE_POOL)
        f = (time.perf_counter() - t0) * 1000

        pine = max(0.0, s - e)
        embed_ms.append(e)
        sem_ms.append(s)
        rerank_ms.append(r)
        full_ms.append(f)
        rerank_sizes.append(len(dedup))
        rows.append((g["id"], e, s - e, r, f, len(dedup), len(sem)))
        print(f"  {g['id']:<15} embed={e:7.0f} pinecone={pine:7.0f} "
              f"rerank={r:7.0f} (n={len(dedup):3d}) full={f:7.0f}", flush=True)

    print("\n=== summary (ms) ===")
    print(f"{'component':<22}{'p50':>9}{'max':>9}")
    for name, vals in (("embed (NIM /embeddings)", embed_ms),
                       ("pinecone (dense-embed)", [max(0, b - a) for a, b in
                                                   zip(embed_ms, sem_ms)]),
                       ("dense total", sem_ms),
                       ("rerank (Nemotron API)", rerank_ms),
                       ("full search()", full_ms)):
        print(f"{name:<22}{med(vals):>9.0f}{max(vals):>9.0f}")
    print(f"\nrerank payload: p50={med(rerank_sizes):.0f} "
          f"max={max(rerank_sizes)} docs")
    print(f"remote total p50 ~ {med(embed_ms) + med(rerank_ms):.0f}ms "
          f"(embed + rerank, sequential)")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 12)
