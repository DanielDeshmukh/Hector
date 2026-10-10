"""sweep_retrieval_gate.py - retrieval-only gate for all 4 indexed acts.

The full run_gold_eval harness generates + LLM-judges every answer x 3 seeds -
correct for the small human gold, but the 4-act per-section gate has 3,280
questions (IPC 1,162 + BNS 716 + BNSS 1,062 + BSA 340). This sweep measures
only the retrieval leg: expand -> hybrid search (top_k=10, candidate_pool=30)
-> section_hit against expected_sections.

Speed design (measured 2026-10-10: live NIM embed ~1-6s + NIM rerank ~5s per
question made the naive sweep a ~10h serial job):
  * Query embeddings come from query_embeds.npz (precompute_query_embeds.py),
    byte-identical vectors to live NIM embeds, served through a patched
    _embed_text. Cache misses fall back to the live API (correctness first).
  * Default --rerank off: the reranker is disabled and the deterministic
    fallback scorer orders the fused pool, so a query costs ~50-100ms of
    local CPU (npz matrix + BM25 + fusion). Fully offline, resumable.
  * --rerank on: production NIM rerank (nim provider). Used by --verify to
    measure how many verdicts the cross-encoder actually flips - targeted at
    fast-pass misses + a random hit sample instead of all 3,280 questions.

Recorded per question (stage_info is read on the same thread right after
search returns, so no copy is needed):
  fused_hit  - expected section reached the dense+BM25 fusion pool
               (stages.scored, <=60 rows) ... rerank-independent coverage
  pool_hit   - survived threshold/floor pre-truncation (stages.final) ...
               "would retrieve with top_k=inf"
  hit        - in the returned top-10 ... the gate number

Pinecone data-plane egress is exhausted until 2026-11-01 (HTTP 429); the
dense leg uses the precomputed npz (same NIM embeddings the index holds).

Resumable: appends results/sweep_{act}[_rerank].jsonl, skips ids present.
Chunked: --offset/--limit keep each invocation under ~15 min.

Usage:
  python precompute_query_embeds.py --all          # one-time (~5-10 min)
  python sweep_retrieval_gate.py --all             # fast pass
  python sweep_retrieval_gate.py --verify          # NIM rerank on misses+sample
  python sweep_retrieval_gate.py --summary         # report + flip analysis
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
sys.path.insert(0, os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "api")))

CORPUS_PATH = os.path.abspath(
    os.path.join(SCRIPT_DIR, "..", "ingest_v2", "output", "eval_corpus.jsonl")
)
QUERY_EMBEDS = os.path.join(SCRIPT_DIR, "query_embeds.npz")
os.environ.setdefault("HECTOR_EVAL_CORPUS", CORPUS_PATH)
os.environ.setdefault("HECTOR_EVAL_INDEX", "hector")
os.environ.setdefault("HF_HUB_OFFLINE", "1")

for _line in open(os.path.join(SCRIPT_DIR, "..", "..", "..", ".env"), encoding="utf-8"):
    _line = _line.strip()
    if _line and not _line.startswith("#") and "=" in _line:
        _k, _v = _line.split("=", 1)
        os.environ.setdefault(_k, _v)

from run_gold_eval import TOP_K, CANDIDATE_POOL, read_jsonl, section_hit  # noqa: E402

RESULTS_DIR = os.getenv("HECTOR_EVAL_RESULTS") or os.path.join(SCRIPT_DIR, "results")

GOLD = {
    "ipc": os.path.join(SCRIPT_DIR, "gold_set_ipc.jsonl"),
    "bns": os.path.join(SCRIPT_DIR, "gold_bns.jsonl"),
    "bnss": os.path.join(SCRIPT_DIR, "gold_bnss.jsonl"),
    "bsa": os.path.join(SCRIPT_DIR, "gold_bsa.jsonl"),
}

_write_lock = threading.Lock()
_records_cache: list[dict] | None = None
_records_by_id: dict[str, dict] = {}
_records_lock = threading.Lock()
_embed_cache: dict[str, object] | None = None
_embed_misses = [0]
_tls = threading.local()


def log(msg: str) -> None:
    print(f"[sweep] {msg}", flush=True)


def sha1(text: str) -> str:
    return hashlib.sha1((text or "").encode("utf-8")).hexdigest()


def out_path(act: str, rerank: bool) -> str:
    suffix = "_rerank" if rerank else ""
    return os.path.join(RESULTS_DIR, f"sweep_{act}{suffix}.jsonl")


def load_records() -> list[dict]:
    global _records_cache, _records_by_id
    with _records_lock:
        if _records_cache is None:
            rows = []
            with open(CORPUS_PATH, encoding="utf-8") as fh:
                for line in fh:
                    if line.strip():
                        rows.append(json.loads(line))
            _records_cache = [
                {"id": r["id"], "document": r["document"], "metadata": r["metadata"]}
                for r in rows
            ]
            _records_by_id = {r["id"]: r for r in _records_cache}
            log(f"corpus loaded: {len(_records_cache)} records")
    return _records_cache


def load_embed_cache() -> dict[str, object]:
    global _embed_cache
    if _embed_cache is None:
        _embed_cache = {}
        if os.path.exists(QUERY_EMBEDS):
            import numpy as np

            data = np.load(QUERY_EMBEDS, allow_pickle=False)
            keys = [str(k) for k in data["keys"]]
            vecs = data["vecs"].astype(np.float32, copy=False)
            _embed_cache = dict(zip(keys, vecs))
            log(f"query embeds: {len(_embed_cache)} vectors from query_embeds.npz")
        else:
            log("query embeds: NONE - every query hits the live NIM API "
                "(run precompute_query_embeds.py --all first)")
    return _embed_cache


def get_retriever():
    retriever = getattr(_tls, "retriever", None)
    if retriever is None:
        from data.hybrid_retriever import HectorHybridRetriever

        retriever = HectorHybridRetriever.from_records(load_records())
        # Pinecone egress exhausted until 2026-11-01; npz dense matrix is the
        # same vectors the index holds, so the dense leg stays faithful.
        retriever._pinecone_dead = True
        retriever._local_records_loaded = True
        retriever.reranker_disabled = not RERANK_ON
        original = retriever._embed_text
        cache = load_embed_cache()

        def _cached_embed(text, _orig=original, _cache=cache):
            vec = _cache.get(sha1(text))
            if vec is not None:
                return vec
            _embed_misses[0] += 1
            return _orig(text)

        retriever._embed_text = _cached_embed
        _tls.retriever = retriever
    return retriever


def get_expander():
    expander = getattr(_tls, "expander", None)
    if expander is None:
        from core.query_expander import QueryExpander

        expander = QueryExpander()
        _tls.expander = expander
    return expander


def stage_ids(stage_info, stage: str) -> list[str]:
    return list((((stage_info or {}).get("stages")) or {}).get(stage) or [])


def specs_hit(ids: list[str], specs: list[str]) -> bool:
    if not specs:
        return False
    for rid in ids:
        rec = _records_by_id.get(rid)
        if rec is None:
            continue
        for spec in specs:
            if section_hit(rec["document"], rec["metadata"], spec):
                return True
    return False


def run_one(g: dict, act: str) -> dict:
    retriever = get_retriever()
    raw = g["question"]
    t0 = time.time()
    error = None
    results = []
    stage_info = None
    try:
        expanded = get_expander().expand(raw) or raw
    except Exception:
        expanded = raw
    try:
        results = retriever.search(
            expanded,
            top_k=TOP_K,
            candidate_pool=CANDIDATE_POOL,
            raw_query=raw,
        )
        stage_info = retriever.last_stage_info
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    specs = g.get("expected_sections") or []
    top_meta = [r.get("metadata") or {} for r in results[:3]]
    return {
        "qid": g["id"],
        "act": act,
        "variant": g.get("variant"),
        "hit": any(
            section_hit(r.get("document"), r.get("metadata"), spec)
            for spec in specs
            for r in results
        ),
        "pool_hit": specs_hit(stage_ids(stage_info, "final"), specs),
        "fused_hit": specs_hit(stage_ids(stage_info, "scored"), specs),
        "error": error,
        "n_results": len(results),
        "retrieval_mode": getattr(retriever, "last_search_mode", None),
        "rerank": "nim" if RERANK_ON else "off",
        "top_act_ids": [m.get("act_id") or "" for m in top_meta],
        "ms": round((time.time() - t0) * 1000),
    }


def select_todo(act: str, rerank: bool, offset: int, limit: int,
                verify: bool, verify_sample: int) -> list[dict]:
    gold = read_jsonl(GOLD[act])
    done = {r["qid"] for r in read_jsonl(out_path(act, rerank))}
    if verify:
        # Deterministic selection: full gold verdicts + fixed seed, so
        # re-invocations with --limit chunk the SAME selection; done qids
        # are dropped after selection for clean resume.
        fast = {}
        for r in read_jsonl(out_path(act, False)):
            fast[r["qid"]] = r  # last write wins
        misses = [g for g in gold if fast.get(g["id"], {}).get("hit") is False]
        hits = [g for g in gold if fast.get(g["id"], {}).get("hit") is True]
        rng = random.Random(13)
        sample = rng.sample(hits, min(verify_sample, len(hits)))
        selected = {x["id"] for x in misses + sample}
        todo = [g for g in gold if g["id"] in selected]
        log(f"{act}: verify selection = {len(misses)} misses + "
            f"{len(sample)} sampled hits = {len(todo)}")
    else:
        todo = [g for g in gold if g["id"] not in done]
    todo = [g for g in todo if g["id"] not in done]
    if offset:
        todo = todo[offset:]
    if limit:
        todo = todo[:limit]
    return todo


def sweep_act(act: str, offset: int, limit: int, workers: int,
              verify: bool, verify_sample: int) -> int:
    rerank = RERANK_ON
    gold_total = len(read_jsonl(GOLD[act]))
    done = {r["qid"] for r in read_jsonl(out_path(act, rerank))}
    todo = select_todo(act, rerank, offset, limit, verify, verify_sample)
    log(f"{act}: gold={gold_total} done={len(done)} this_chunk={len(todo)} "
        f"workers={workers} rerank={'nim' if rerank else 'off'}")
    if not todo:
        return 0

    n_hit = n_err = 0
    t0 = time.time()
    os.makedirs(RESULTS_DIR, exist_ok=True)
    fh = open(out_path(act, rerank), "a", encoding="utf-8")
    try:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(run_one, g, act) for g in todo]
            for i, fut in enumerate(as_completed(futures), 1):
                row = fut.result()
                n_hit += int(row["hit"])
                n_err += int(row["error"] is not None)
                with _write_lock:
                    fh.write(json.dumps(row, ensure_ascii=False) + "\n")
                    fh.flush()
                if i % 50 == 0 or i == len(todo):
                    el = time.time() - t0
                    rate = i / el if el else 0
                    eta = (len(todo) - i) / rate if rate else 0
                    log(f"  {act} {i}/{len(todo)} hits={n_hit} err={n_err} "
                        f"{el:.0f}s eta={eta:.0f}s")
    finally:
        fh.close()
    log(f"{act} chunk done: {n_hit}/{len(todo)} hit, {n_err} errors, "
        f"embed_cache_misses={_embed_misses[0]}")
    return 0


def _dedup(rows: list[dict]) -> list[dict]:
    seen = {}
    for r in rows:  # last write wins (resumable reruns)
        seen[r["qid"]] = r
    return list(seen.values())


def _line(tag: str, rows: list[dict]) -> None:
    free = [r for r in rows if r.get("variant") == "number_free"]
    anch = [r for r in rows if r.get("variant") == "number_anchored"]
    errs = [r for r in rows if r.get("error")]
    misses = [r for r in rows if not r["hit"]]

    def kn(xs):
        return sum(1 for r in xs if r["hit"]), len(xs)

    k, n = kn(rows)
    kf, nf = kn(free)
    ka, na = kn(anch)
    fused = sum(1 for r in rows if r.get("fused_hit"))
    pool = sum(1 for r in rows if r.get("pool_hit"))
    log(f"{tag}: recall@{TOP_K}={k}/{n} = {k / n:.3f} "
        f"number_free={kf}/{nf} = {kf / nf if nf else 0:.3f} "
        f"number_anchored={ka}/{na} = {ka / na if na else 0:.3f} "
        f"fused_pool={fused}/{n} pool={pool}/{n} "
        f"errors={len(errs)} misses={len(misses)}")
    for r in misses[:8]:
        log(f"  miss {r['qid']} fused={r.get('fused_hit')} "
            f"pool={r.get('pool_hit')} mode={r.get('retrieval_mode')} "
            f"top={r.get('top_act_ids')}")
    for r in errs[:3]:
        log(f"  err sample {r['qid']}: {str(r['error'])[:120]}")


def summarize(acts: list[str]) -> int:
    grand_k = grand_n = 0
    rr_k = rr_n = 0
    for act in acts:
        fast = _dedup(read_jsonl(out_path(act, False)))
        rr = _dedup(read_jsonl(out_path(act, True)))
        if not fast and not rr:
            log(f"{act}: no results yet")
            continue
        if fast:
            _line(act, fast)
            grand_k += sum(1 for r in fast if r["hit"])
            grand_n += len(fast)
        if rr:
            _line(f"{act} [rerank=nim]", rr)
            rr_k += sum(1 for r in rr if r["hit"])
            rr_n += len(rr)
            # flip analysis: fast verdict vs rerank verdict on the same qids
            fmap = {r["qid"]: r for r in fast}
            pairs = [(fmap[r["qid"]], r) for r in rr if r["qid"] in fmap]
            if pairs:
                up = sum(1 for f, r in pairs if not f["hit"] and r["hit"])
                down = sum(1 for f, r in pairs if f["hit"] and not r["hit"])
                both = sum(1 for f, r in pairs if f["hit"] and r["hit"])
                log(f"{act} flips vs fast pass: n={len(pairs)} "
                    f"miss->hit={up} hit->miss={down} stable_hit={both} "
                    f"stable_miss={len(pairs) - up - down - both}")
    if grand_n:
        log(f"GRAND (fast pass): recall@{TOP_K} {grand_k}/{grand_n} = "
            f"{grand_k / grand_n:.4f}")
    if rr_n:
        log(f"GRAND (rerank=nim): recall@{TOP_K} {rr_k}/{rr_n} = "
            f"{rr_k / rr_n:.4f}")
    return 0


RERANK_ON = False


def main() -> int:
    global RERANK_ON
    ap = argparse.ArgumentParser()
    ap.add_argument("--act", choices=sorted(GOLD), default=None)
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--summary", action="store_true",
                    help="print recall so far, do not search")
    ap.add_argument("--all", action="store_true",
                    help="fast sweep of every act sequentially (no chunking)")
    ap.add_argument("--rerank", action="store_true",
                    help="production NIM rerank (slow, ~5s/query)")
    ap.add_argument("--verify", action="store_true",
                    help="rerank on: fast-pass misses + random hit sample")
    ap.add_argument("--verify-sample", type=int, default=150,
                    help="hit sample size for --verify")
    args = ap.parse_args()

    if args.summary:
        return summarize(sorted(GOLD))

    RERANK_ON = args.rerank or args.verify
    if RERANK_ON:
        os.environ["HECTOR_RERANK_PROVIDER"] = "nim"
        log("rerank ON: provider=nim (production)")
    else:
        log("rerank OFF: fallback scorer (fast local pass)")

    acts = sorted(GOLD) if args.all else [args.act]
    if acts == [None]:
        raise SystemExit("need --act, --all, --verify, or --summary")

    t0 = time.time()
    load_records()
    load_embed_cache()
    get_retriever()  # warm BM25 + embed-cache patch on the main thread
    log(f"warmup in {time.time() - t0:.1f}s")

    for act in acts:
        sweep_act(act, args.offset, args.limit, args.workers,
                  args.verify, args.verify_sample)

    return summarize(acts)


if __name__ == "__main__":
    sys.exit(main())
