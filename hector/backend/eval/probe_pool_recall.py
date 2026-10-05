"""Recall + latency vs candidate_pool, retrieval only (no generation).

Answers the one question blocking the latency fix: if CANDIDATE_POOL drops
from 30 to 10 (rerank 3.0s -> 1.15s), does section_recall@10 stay >= 0.98?

Uses the harness's own expander + section_hit so the number is directly
comparable to the 0.980 recorded in results/iter1.
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import run_gold_eval as R  # noqa: E402

R.GOLD_SAMPLE = 200
R.GOLD_SAMPLE_SEED = 20261013

POOLS = [int(p) for p in (sys.argv[1:] or ["10"])]
LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pool_recall.log")


def log(msg=""):
    """Print to the console and append to pool_recall.log (self-tee)."""
    print(msg, flush=True)
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(msg + "\n")


def pct(values, q):
    if not values:
        return 0
    v = sorted(values)
    idx = min(len(v) - 1, int(round(q * (len(v) - 1))))
    return v[idx]


def main():
    gold = R.load_gold()
    stack = R.build_stack()
    retriever = stack["retriever"]
    expander = stack["expander"]

    for pool in POOLS:
        hits = specs = 0
        lat = []
        wrong = []
        t_pool = time.time()
        for i, g in enumerate(gold, 1):
            t0 = time.time()
            try:
                expanded = expander.expand(g["question"])
                results = retriever.search(
                    g["question"] if not expanded else expanded,
                    top_k=R.TOP_K,
                    candidate_pool=pool,
                )
            except Exception as exc:
                log(f"  ERROR {g['id']}: {exc}")
                continue
            lat.append((time.time() - t0) * 1000)
            expected = g.get("expected_sections") or []
            if not expected:
                continue
            any_hit = any(
                R.section_hit(c["document"], c["metadata"], spec)
                for spec in expected
                for c in results
            )
            specs += 1
            hits += int(any_hit)
            if not any_hit and len(wrong) < 8:
                wrong.append((g["id"], expected))
            if i % 25 == 0:
                log(
                    f"  pool={pool} {i}/{len(gold)} recall="
                    f"{hits / max(1, specs):.4f} p50={pct(lat, .5):.0f}ms"
                )

        recall = hits / max(1, specs)
        verdict = "PASS" if recall >= 0.98 else "FAIL"
        log(
            f"POOL={pool}  recall@10={recall:.4f} ({hits}/{specs}) {verdict}  "
            f"latency p50={pct(lat, .5):.0f}ms p95={pct(lat, .95):.0f}ms "
            f"max={max(lat):.0f}ms  [{time.time() - t_pool:.0f}s]"
        )
        for qid, exp in wrong:
            log(f"    miss {qid} expected={exp}")


if __name__ == "__main__":
    main()
