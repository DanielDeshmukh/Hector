"""Stage-by-stage retrieval diagnosis for compare/BNS recall misses.

Read-only, no LLM calls. For each requested qid: run the exact harness path
(expand -> search with harness TOP_K/CANDIDATE_POOL) and print, per expected
section spec, its 1-based rank at every retrieval sub-stage (dense, bm25,
rrf, scored, dedup, rerank, final), plus the scored top-5 components and the
final top-10 hit flags.

Usage:
  HECTOR_GOLD_PATH=... python diag_compare_ranks.py <qid> [<qid> ...]
"""

import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import os as _os

# Match sweep_recall/harness exactly: same corpus, same index.
if _os.getenv("HECTOR_EVAL_CORPUS") in (None, ""):
    from pathlib import Path as _Path
    _os.environ["HECTOR_EVAL_CORPUS"] = str(
        _Path(SCRIPT_DIR).parent
        / "ingest_v2" / "output" / "eval_corpus.jsonl"
    )
_os.environ.setdefault("HECTOR_EVAL_INDEX", "hector")

import run_gold_eval as hg  # noqa: E402  (sets env vars + sys.path)

STAGE_ORDER = ["dense", "bm25", "rrf", "scored", "dedup", "rerank", "final"]
TOP_PRINT = 10


def rank_of_stage(stage_ids, spec, rec_by_id):
    for i, doc_id in enumerate(stage_ids, start=1):
        rec = rec_by_id.get(doc_id)
        if rec is None:
            continue
        if hg.section_hit(rec["document"], rec["metadata"], spec):
            return i
    return None


def main(qids):
    gold = {g["id"]: g for g in hg.load_gold()}
    stack = hg.build_stack()
    retriever = stack["retriever"]
    expander = stack["expander"]
    rec_by_id = {rec["id"]: rec for rec in retriever.records}
    print(f"[diag] gold={hg.GOLD_PATH} records={len(rec_by_id)}", flush=True)

    for qid in qids:
        if qid not in gold:
            print(f"\n!! {qid} not in {hg.GOLD_PATH}")
            continue
        g = gold[qid]
        query = expander.expand(g["question"])
        results = retriever.search(
            query, top_k=hg.TOP_K, candidate_pool=hg.CANDIDATE_POOL,
            raw_query=g["question"],
        )
        info = retriever.last_stage_info or {}
        stages = info.get("stages", {})
        timings = info.get("timings_ms", {})
        detail = info.get("detail") or {}
        scored_top = detail.get("scored_top", [])

        print("\n" + "=" * 100)
        print(f"{qid} [{g.get('category')}] {g['question']}")
        print(f"  expanded==raw: {query == g['question']}  "
              f"len={len(query)}")
        print(f"  expected: {g['expected_sections']}")
        print("  mode=%s chunks=%d total_ms=%s"
              % (retriever.last_search_mode, len(results),
                 timings.get("total_ms")))
        if info.get("filter"):
            print(f"  filter={info.get('filter')}")

        for spec in g["expected_sections"]:
            cells = []
            for stage in STAGE_ORDER:
                r = rank_of_stage(stages.get(stage, []), spec, rec_by_id)
                cells.append(f"{stage}={r if r is not None else '-'}")
            print(f"  {spec:<22} " + "  ".join(cells))

        print("  scored top-5:")
        for item in scored_top[:5]:
            print("    score=%-8s rrf=%-8s sem=%-7s bm25=%-7s boost=%-7s act=%s"
                  % (item.get("score"), item.get("rrf_score"),
                     item.get("semantic_score"), item.get("bm25_score"),
                     item.get("boost_score"), str(item.get("act"))[:55]))

        print(f"  final top-{TOP_PRINT}:")
        for i, res in enumerate(results[:TOP_PRINT], start=1):
            meta = res.get("metadata") or {}
            hits = [s for s in g["expected_sections"]
                    if hg.section_hit(res.get("document") or "", meta, s)]
            print("    %2d score=%-8s hit=%-18s act=%s"
                  % (i, res.get("score"), ",".join(hits) or "-",
                     str(res.get("act") or meta.get("real_act_name"))[:60]))

        print("  timings_ms: "
              + " ".join(f"{k}={timings.get(k)}" for k in sorted(timings)))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    main(sys.argv[1:])
