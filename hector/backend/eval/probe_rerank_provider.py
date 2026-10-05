"""Which reranker is actually in use, and how fast is each option?

The probe printed "Loading weights: 105/105" + "[warmup] reranker=True in
11.6s", yet hybrid_retriever requests provider="nemotron" while
rerank_provider documents "local" as the default. Resolve which one the
retriever ends up with, and time local vs remote on a 30-doc payload.

    python probe_rerank_provider.py
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
from core.rerank_provider import (  # noqa: E402
    LocalReranker, NemotronReranker, get_rerank_provider, warmup_reranker,
)


def main():
    print(f"env HECTOR_RERANK_PROVIDER = {os.getenv('HECTOR_RERANK_PROVIDER')!r}")
    print(f"env HECTOR_NEMOTRON_RERANK_MODEL = "
          f"{os.getenv('HECTOR_NEMOTRON_RERANK_MODEL')!r}")

    t0 = time.time()
    ok = warmup_reranker()
    print(f"[warmup] provider default -> ok={ok} in {time.time()-t0:.1f}s")

    r = get_rerank_provider("nemotron")
    print(f"get_rerank_provider('nemotron') -> {type(r).__name__}")
    r2 = get_rerank_provider("local")
    print(f"get_rerank_provider('local')    -> {type(r2).__name__}")

    stack = rge.build_stack()
    ret = stack["retriever"]
    cached = getattr(ret, "_reranker_cached", None)
    print(f"retriever cached provider       -> "
          f"{type(cached).__name__ if cached else None}")
    print(f"env used by retriever default  -> "
          f"{os.getenv('HECTOR_RERANK_PROVIDER', 'nemotron')!r} (no env set)")

    # Build a realistic 30-doc payload from one real query.
    g = rge.load_gold()[0]
    query = g["question"]
    sem = ret._semantic_search(query, rge.CANDIDATE_POOL)
    dedup = ret._deduplicate_results(sem)
    print(f"\npayload: {len(dedup)} docs, query={query[:70]!r}")

    for name, reranker in (("as-configured", ret._reranker_cached),
                           ("nemotron-or-fallback", get_rerank_provider("nemotron")),
                           ("local", LocalReranker())):
        if reranker is None:
            continue
        try:
            docs = [dict(d) for d in dedup]
            t0 = time.perf_counter()
            out = reranker.rerank(query, docs)
            ms = (time.perf_counter() - t0) * 1000
            top = [d.get("id") or d.get("metadata", {}).get("section_number")
                   for d in out[:5]]
            print(f"  {name:<24} {type(reranker).__name__:<18} "
                  f"{ms:8.0f}ms  top5={top}")
        except Exception as exc:
            print(f"  {name:<24} {type(reranker).__name__:<18} "
                  f"FAILED: {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    main()
