"""Data-derived relevance-threshold calibration (Round 2, task 4).

Collects the top-1 fused score of every retrieval-eval query under the
production search path (threshold temporarily disabled), then chooses the
floor that maximises balanced accuracy between answerable (exact+similar)
and unanswerable (irrelevant) queries. The result is written to
hector/api/data/relevance_threshold.json, which
HectorHybridRetriever._min_relevance reads as its default (env
HECTOR_MIN_RELEVANCE still overrides).

Design notes:
- No query expansion here: calibration measures search() itself, so the
  script has no LLM dependency and is deterministic.
- Candidate thresholds are the observed scores (+reject-all), i.e. every
  distinct classification partition; ties break toward the higher floor
  (more conservative: prefer abstaining over serving low-relevance text).
- The score scale depends on the active scorer (reranker fallback by
  default), which is recorded in the artifact for provenance.
"""

import json
import os
import sys
import time
from pathlib import Path

os.environ["HF_HUB_OFFLINE"] = "1"
# Collect raw scores: the gate must not pre-filter candidates while calibrating.
os.environ["HECTOR_MIN_RELEVANCE"] = "0"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # hector/backend
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api"))  # hector/api

from data.hybrid_retriever import HectorHybridRetriever as HybridRetriever  # noqa: E402
from run_retrieval_eval import TEST_QUERIES  # noqa: E402

OUTPUT_PATH = (
    Path(__file__).resolve().parents[1] / "api" / "data" / "relevance_threshold.json"
)
ANSWERABLE = ("exact", "similar")
EPS = 1e-9


def choose_threshold(answerable_scores, unanswerable_scores):
    """Pick the score floor with best balanced accuracy (Youden optimum).

    answerable_scores: top-1 scores for answerable queries (None = no result,
    treated as always rejected). Raises ValueError when either group is empty.
    """
    if not answerable_scores or not unanswerable_scores:
        raise ValueError(
            "both answerable and unanswerable score groups are required"
        )
    n_a = len(answerable_scores)
    n_u = len(unanswerable_scores)

    observed = sorted(
        {s for s in list(answerable_scores) + list(unanswerable_scores) if s is not None}
    )
    if not observed:
        raise ValueError("no numeric scores collected")
    candidates = observed + [observed[-1] + EPS]

    best = None
    for threshold in candidates:
        tp = sum(1 for s in answerable_scores if s is not None and s >= threshold)
        fn = n_a - tp
        fp = sum(1 for s in unanswerable_scores if s is not None and s >= threshold)
        tn = n_u - fp
        tpr = tp / n_a
        tnr = tn / n_u
        bal = (tpr + tnr) / 2.0
        record = {
            "threshold": threshold,
            "balanced_accuracy": bal,
            "tpr": tpr,
            "tnr": tnr,
            "tp": tp,
            "fn": fn,
            "fp": fp,
            "tn": tn,
        }
        # Tie-break: higher threshold (fewer false accepts).
        if best is None or (bal, threshold) > (best["balanced_accuracy"], best["threshold"]):
            best = record
    best["n_answerable"] = n_a
    best["n_unanswerable"] = n_u
    for key in ("balanced_accuracy", "tpr", "tnr"):
        best[key] = round(best[key], 6)
    return best


def legacy_metrics(answerable_scores, unanswerable_scores, legacy=0.05):
    """Metrics of the previous hardcoded 0.05 floor, for comparison."""
    n_a = len(answerable_scores)
    n_u = len(unanswerable_scores)
    tp = sum(1 for s in answerable_scores if s is not None and s >= legacy)
    fp = sum(1 for s in unanswerable_scores if s is not None and s >= legacy)
    tpr = tp / n_a
    tnr = (n_u - fp) / n_u
    return {
        "threshold": legacy,
        "balanced_accuracy": round((tpr + tnr) / 2.0, 6),
        "tpr": round(tpr, 6),
        "tnr": round(tnr, 6),
    }


def collect_scores():
    """Run every eval query through search() and return raw top-1 scores."""
    retriever = HybridRetriever()
    answerable = []
    unanswerable = []
    rows = []
    for q in TEST_QUERIES:
        started = time.time()
        try:
            results = retriever.search(q["query"], top_k=10)
            score = float(results[0].get("score")) if results else None
            error = None
        except Exception as exc:  # keep the run going; record the failure
            results = []
            score = None
            error = f"{type(exc).__name__}: {exc}"
        elapsed_ms = round((time.time() - started) * 1000, 1)
        mode = getattr(retriever, "last_search_mode", None) or "unknown"
        group = (
            answerable if q["category"] in ANSWERABLE else unanswerable
        )
        group.append(score)
        rows.append(
            {
                "id": q["id"],
                "category": q["category"],
                "query": q["query"],
                "top1_score": score,
                "n_results": len(results),
                "mode": mode,
                "retrieve_ms": elapsed_ms,
                "error": error,
            }
        )
        shown = "none" if score is None else f"{score:.4f}"
        print(
            f"Q{q['id']:2d} [{q['category']:9s}] top1={shown:>6} "
            f"n={len(results)} [{mode}] {elapsed_ms:6.0f}ms | {q['query'][:50]}"
        )
    return answerable, unanswerable, rows


def main():
    print("=" * 70)
    print("HECTOR RELEVANCE THRESHOLD CALIBRATION")
    print("=" * 70)
    answerable, unanswerable, rows = collect_scores()

    a_sorted = sorted(s for s in answerable if s is not None)
    u_sorted = sorted(s for s in unanswerable if s is not None)

    def fmt(group):
        if not group:
            return "n=0"
        mean = sum(group) / len(group)
        mid = group[len(group) // 2]
        return (
            f"n={len(group)} mean={mean:.3f} p50={mid:.3f} "
            f"min={group[0]:.3f} max={group[-1]:.3f}"
        )

    print(f"\nanswerable    top1: {fmt(a_sorted)}")
    print(f"unanswerable  top1: {fmt(u_sorted)}")

    best = choose_threshold(answerable, unanswerable)
    legacy = legacy_metrics(answerable, unanswerable)
    print(f"\nchosen threshold: {best['threshold']:.4f} "
          f"(bal_acc={best['balanced_accuracy']:.4f} "
          f"tpr={best['tpr']:.4f} tnr={best['tnr']:.4f})")
    print(f"legacy 0.05     : bal_acc={legacy['balanced_accuracy']:.4f} "
          f"tpr={legacy['tpr']:.4f} tnr={legacy['tnr']:.4f}")

    artifact = {
        "threshold": best["threshold"],
        "method": "balanced_accuracy_max_on_top1_scores",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "n_answerable": best["n_answerable"],
        "n_unanswerable": best["n_unanswerable"],
        "balanced_accuracy": best["balanced_accuracy"],
        "tpr": best["tpr"],
        "tnr": best["tnr"],
        "tp": best["tp"],
        "fn": best["fn"],
        "fp": best["fp"],
        "tn": best["tn"],
        "legacy_0_05": legacy,
        "scorer": "search_pipeline_top1",
        "source": "run_retrieval_eval.TEST_QUERIES (raw, unexpanded)",
        "answerable_top1": a_sorted,
        "unanswerable_top1": u_sorted,
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as fh:
        json.dump(artifact, fh, indent=2)
    print(f"\nwrote {OUTPUT_PATH}")

    with open(OUTPUT_PATH.with_name("relevance_calibration_rows.json"), "w", encoding="utf-8") as fh:
        json.dump(rows, fh, indent=2)
    print(f"wrote {OUTPUT_PATH.with_name('relevance_calibration_rows.json')}")


if __name__ == "__main__":
    main()
