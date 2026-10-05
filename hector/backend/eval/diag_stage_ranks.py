"""Round 4 retrieval diagnosis (read-only, no LLM calls).

For the questions that were refused in ALL 3 round-3 runs, print the rank
of every expected section at each retrieval sub-stage (dense, bm25, rrf,
scored, dedup, rerank, final), the wrong-act composition of the top
candidates, and the per-stage latency profile.

Expanded queries are reused from results/raw_runs.jsonl (run 1) so the
diagnosis matches the exact queries used in the round-3 gold runs.

Usage: python diag_stage_ranks.py
"""

import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import run_gold_eval as hg  # noqa: E402  (sets env vars + sys.path)

# Refused in all 3 round-3 runs (never answered).
ALWAYS_REFUSED = ["g013", "g016", "g021", "g027", "g028", "g029", "g044"]
STAGE_ORDER = ["dense", "bm25", "rrf", "scored", "dedup", "rerank", "final"]
TOP_PRINT = 8


def load_round1_expansions():
    rows = hg.read_jsonl(hg.RAW_PATH)
    expanded = {}
    for row in rows:
        if row.get("run") == 1 and row.get("qid") in ALWAYS_REFUSED:
            expanded.setdefault(
                row["qid"], row.get("expanded") or row.get("question") or ""
            )
    return expanded


def rank_of_stage(stage_ids, spec, rec_by_id):
    """1-based rank of the first id whose record matches the section spec."""
    for i, doc_id in enumerate(stage_ids, start=1):
        rec = rec_by_id.get(doc_id)
        if rec is None:
            continue
        if hg.section_hit(rec["document"], rec["metadata"], spec):
            return i
    return None


def main():
    gold = {g["id"]: g for g in hg.load_gold()}
    expanded = load_round1_expansions()
    print(
        f"[diag] expanded queries loaded for "
        f"{sorted(expanded)}/{ALWAYS_REFUSED}",
        flush=True,
    )

    stack = hg.build_stack()
    retriever = stack["retriever"]
    rec_by_id = {rec["id"]: rec for rec in retriever.records}
    print(f"[diag] records={len(rec_by_id)}", flush=True)

    for qid in ALWAYS_REFUSED:
        g = gold[qid]
        query = expanded.get(qid) or g["question"]
        results = retriever.search(
            query, top_k=hg.TOP_K, candidate_pool=hg.CANDIDATE_POOL
        )
        info = retriever.last_stage_info or {}
        stages = info.get("stages", {})
        timings = info.get("timings_ms", {})
        scored_top = (info.get("detail") or {}).get("scored_top", [])

        print("\n" + "=" * 100)
        print(f"{qid} [{g['category']}] {g['question']}")
        print(f"  expanded: {query[:180]}")
        print(f"  expected: {g['expected_sections']}")
        print(
            "  mode=%s chunks=%d total_ms=%s"
            % (
                retriever.last_search_mode,
                len(results),
                timings.get("total_ms"),
            )
        )
        if not g["expected_sections"]:
            print("  (no expected sections)")
        for spec in g["expected_sections"]:
            cells = []
            for stage in STAGE_ORDER:
                r = rank_of_stage(stages.get(stage, []), spec, rec_by_id)
                cells.append(f"{stage}={r if r is not None else '-'}")
            print(f"  {spec:<22} " + "  ".join(cells))

        print("  scored top-5 (score components / act):")
        for item in scored_top[:5]:
            act = item.get("act") or ""
            print(
                "    score=%-8s rrf=%-8s sem=%-7s bm25=%-7s boost=%-7s act=%s"
                % (
                    item.get("score"),
                    item.get("rrf_score"),
                    item.get("semantic_score"),
                    item.get("bm25_score"),
                    item.get("boost_score"),
                    str(act)[:55],
                )
            )

        print("  final top-%d:" % TOP_PRINT)
        for i, res in enumerate(results[:TOP_PRINT], start=1):
            meta = res.get("metadata") or {}
            hit = any(
                hg.section_hit(res.get("document") or "", meta, spec)
                for spec in g["expected_sections"]
            )
            print(
                "    %d score=%-8s hit=%-5s act=%s"
                % (
                    i,
                    res.get("score"),
                    hit,
                    str(res.get("act") or meta.get("real_act_name"))[:60],
                )
            )

        print(
            "  timings_ms: "
            + " ".join(f"{k}={timings.get(k)}" for k in sorted(timings))
        )


if __name__ == "__main__":
    main()
