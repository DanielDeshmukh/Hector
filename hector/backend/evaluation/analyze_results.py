#!/usr/bin/env python3
"""
HECTOR Evaluation Results Analyzer

Parses RAGAS evaluation results and generates human-readable reports.

Usage:
    python evaluation/analyze_results.py results/rag_evaluation_summary.json
    python evaluation/analyze_results.py results/rag_evaluation_summary.json --compare results_v2/rag_evaluation_summary.json
"""

import argparse
import json
from pathlib import Path
from typing import Any


def load_summary(path: str) -> dict[str, Any]:
    """Load a RAGAS evaluation summary JSON."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def print_summary(summary: dict[str, Any], label: str = "") -> None:
    """Print a formatted summary table."""
    prefix = f" [{label}]" if label else ""
    print(f"\n{'=' * 65}")
    print(f"  EVALUATION SUMMARY{prefix}")
    print(f"{'=' * 65}")
    print(f"  Dataset:            {summary.get('dataset', 'unknown')}")
    print(f"  Queries evaluated:  {summary.get('total_queries', 0)}")
    print("")
    print("  RAGAS Quality Metrics:")
    print(
        f"    Faithfulness:     {summary.get('faithfulness', 0):.3f}  "
        f"{'*' if summary.get('faithfulness', 0) < 0.5 else ''}"
    )
    print(
        f"    Answer Relevance: {summary.get('answer_relevance', 0):.3f}  "
        f"{'*' if summary.get('answer_relevance', 0) < 0.4 else ''}"
    )
    print(
        f"    Context Precision:{summary.get('context_precision', 0):.3f}  "
        f"{'*' if summary.get('context_precision', 0) < 0.3 else ''}"
    )
    print(
        f"    Context Recall:   {summary.get('context_recall', 0):.3f}  "
        f"{'*' if summary.get('context_recall', 0) < 0.4 else ''}"
    )
    print("")
    print("  Citation Metrics:")
    print(f"    Section Recall:   {summary.get('section_recall', 0):.3f}")
    print(f"    Act Recall:       {summary.get('act_recall', 0):.3f}")
    print(f"    Avg Citations:    {summary.get('avg_citation_count', 0):.1f}")
    print("")
    print("  Performance:")
    print(f"    Avg Latency:      {summary.get('avg_latency_ms', 0):.0f}ms")
    print(f"    P95 Latency:      {summary.get('p95_latency_ms', 0):.0f}ms")
    print(f"    Min Latency:      {summary.get('min_latency_ms', 0):.0f}ms")
    print(f"    Max Latency:      {summary.get('max_latency_ms', 0):.0f}ms")

    errors = summary.get("errors", [])
    if errors:
        print("")
        print(f"  Errors: {len(errors)}")
        for e in errors[:5]:
            print(f"    - {e['query'][:60]}...: {e['error'][:80]}")

    # Category breakdown
    by_cat = summary.get("by_category", {})
    if by_cat:
        print("")
        print("  By Category:")
        for cat, cat_data in by_cat.items():
            print(
                f"    {cat:25s}  n={cat_data['count']:2d}  "
                f"faith={cat_data['faithfulness']:.2f}  "
                f"rel={cat_data['answer_relevance']:.2f}  "
                f"recall={cat_data['context_recall']:.2f}"
            )

    print(f"{'=' * 65}")


def compare_summaries(
    baseline: dict[str, Any],
    treatment: dict[str, Any],
) -> None:
    """Print a side-by-side comparison of two evaluation runs."""
    print(f"\n{'=' * 75}")
    print("  COMPARISON: Baseline vs Treatment")
    print(f"{'=' * 75}")

    metrics = [
        ("faithfulness", "Faithfulness"),
        ("answer_relevance", "Answer Relevance"),
        ("context_precision", "Context Precision"),
        ("context_recall", "Context Recall"),
        ("section_recall", "Section Recall"),
        ("act_recall", "Act Recall"),
        ("avg_citation_count", "Avg Citations"),
        ("avg_latency_ms", "Avg Latency (ms)"),
        ("p95_latency_ms", "P95 Latency (ms)"),
    ]

    print(
        f"  {'Metric':25s}  {'Baseline':>10s}  {'Treatment':>10s}  {'Delta':>10s}  {'Change':>8s}"
    )
    print(f"  {'-' * 25}  {'-' * 10}  {'-' * 10}  {'-' * 10}  {'-' * 8}")

    for key, label in metrics:
        b_val = baseline.get(key, 0)
        t_val = treatment.get(key, 0)
        delta = t_val - b_val
        if b_val != 0:
            pct = (delta / b_val) * 100
            change_str = f"{pct:+.1f}%"
        else:
            change_str = "N/A"

        # Color indicator
        if key in ("avg_latency_ms", "p95_latency_ms"):
            indicator = (
                "improved" if delta < 0 else "regressed" if delta > 0 else "same"
            )
        else:
            indicator = (
                "improved" if delta > 0 else "regressed" if delta < 0 else "same"
            )

        marker = (
            "+" if indicator == "improved" else "-" if indicator == "regressed" else "="
        )
        print(
            f"  {label:25s}  {b_val:10.3f}  {t_val:10.3f}  {delta:+10.3f}  {change_str:>8s} {marker}"
        )

    print(f"  {'-' * 25}  {'-' * 10}  {'-' * 10}  {'-' * 10}  {'-' * 8}")

    b_queries = baseline.get("total_queries", 0)
    t_queries = treatment.get("total_queries", 0)
    print(f"  {'Total Queries':25s}  {b_queries:10d}  {t_queries:10d}")
    print(f"{'=' * 75}")


def print_trend(results_dir: str) -> None:
    """Print trend across multiple evaluation runs in a directory."""
    results_path = Path(results_dir)
    json_files = sorted(results_path.glob("rag_*_evaluation_summary.json"))

    if len(json_files) < 2:
        print("Need at least 2 evaluation runs for trend analysis.")
        return

    print(f"\n{'=' * 80}")
    print(f"  TREND ANALYSIS — {results_dir}")
    print(f"{'=' * 80}")
    print(
        f"  {'Run':30s}  {'Faith':>6s}  {'Relev':>6s}  {'CtxPrec':>7s}  {'CtxRec':>6s}  {'LatP95':>7s}"
    )
    print(f"  {'-' * 30}  {'-' * 6}  {'-' * 6}  {'-' * 7}  {'-' * 6}  {'-' * 7}")

    for f in json_files:
        data = load_summary(str(f))
        name = f.stem.replace("rag_", "").replace("_evaluation_summary", "")
        print(
            f"  {name:30s}  "
            f"{data.get('faithfulness', 0):6.3f}  "
            f"{data.get('answer_relevance', 0):6.3f}  "
            f"{data.get('context_precision', 0):7.3f}  "
            f"{data.get('context_recall', 0):6.3f}  "
            f"{data.get('p95_latency_ms', 0):7.0f}"
        )

    print(f"{'=' * 80}")


def main():
    parser = argparse.ArgumentParser(
        description="Analyze HECTOR RAGAS evaluation results",
    )
    parser.add_argument(
        "summary_json",
        help="Path to evaluation summary JSON",
    )
    parser.add_argument(
        "--compare",
        help="Path to second summary JSON for comparison",
    )
    parser.add_argument(
        "--trend-dir",
        help="Directory with multiple evaluation runs for trend analysis",
    )

    args = parser.parse_args()

    summary = load_summary(args.summary_json)
    print_summary(summary, label="Current")

    if args.compare:
        baseline = load_summary(args.compare)
        compare_summaries(baseline, summary)

    if args.trend_dir:
        print_trend(args.trend_dir)


if __name__ == "__main__":
    main()
