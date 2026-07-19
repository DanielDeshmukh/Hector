#!/usr/bin/env python3
"""
Sweep Comparison Table

Reads sweep_results.json and prints a formatted comparison table
showing how concurrency and top_k affect throughput and latency.

Usage:
    python benchmark/sweep_comparison.py benchmark/results/sweep_run_XXX/sweep_results.json
"""

import argparse
import json
import sys


def main():
    parser = argparse.ArgumentParser(description="Sweep Comparison Table")
    parser.add_argument("sweep_json", help="Path to sweep_results.json")
    args = parser.parse_args()

    with open(args.sweep_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not data:
        print("No sweep results found.")
        sys.exit(1)

    # Filter points with valid stats
    points = [p for p in data if p.get("stats") and p["stats"].get("throughput_qps")]

    if not points:
        print("No valid data points in sweep results.")
        sys.exit(1)

    # Sort by concurrency then top_k
    points.sort(key=lambda p: (p.get("concurrency", 0), p.get("top_k", 0)))

    print(f"\n{'=' * 85}")
    print("  SWEEP RESULTS COMPARISON")
    print(f"{'=' * 85}")
    print(
        f"  {'Concurrency':>12s}  {'Top-K':>6s}  {'QPS':>8s}  {'Avg(ms)':>8s}  {'P95(ms)':>8s}  {'Err%':>6s}  {'Success':>8s}"
    )
    print(
        f"  {'-' * 12}  {'-' * 6}  {'-' * 8}  {'-' * 8}  {'-' * 8}  {'-' * 6}  {'-' * 8}"
    )

    for p in points:
        s = p["stats"]
        cr = p.get("concurrency", s.get("concurrency", "-"))
        tk = p.get("top_k", "-")
        qps = s.get("throughput_qps", 0)
        avg = s.get("avg_latency_ms", 0)
        p95 = s.get("p95_latency_ms", 0)
        err = s.get("error_rate", 0)
        ok = s.get("successful", 0)

        print(
            f"  {cr:>12d}  {tk:>6d}  {qps:>8.1f}  {avg:>8.0f}  {p95:>8.0f}  {err:>5.1f}%  {ok:>8d}"
        )

    print(f"{'=' * 85}")

    # Find optimal point
    optimal = max(points, key=lambda p: p["stats"].get("throughput_qps", 0))
    s = optimal["stats"]
    print(
        f"\n  Optimal: concurrency={optimal.get('concurrency')}, top_k={optimal.get('top_k')}"
    )
    print(f"    Throughput: {s.get('throughput_qps', 0):.1f} QPS")
    print(f"    P95 Latency: {s.get('p95_latency_ms', 0):.0f}ms")
    print(f"    Error Rate: {s.get('error_rate', 0):.1f}%")
    print()


if __name__ == "__main__":
    main()
