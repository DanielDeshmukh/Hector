#!/usr/bin/env python3
"""
HECTOR Benchmark Adapter

Translates HECTOR-specific API responses into the format expected
by the benchmark CLI. Used for profiling stage timing breakdowns.

Usage:
    python benchmark/adapters/hector_adapter.py --host localhost --port 8000 --query "What is Section 302 IPC?"
"""

import argparse
import json
import os
import sys
import time

import requests


def profile_query(host: str, port: int, query: str, api_key: str | None = None) -> dict:
    """Send a single query and return detailed timing breakdown."""
    url = f"http://{host}:{port}/v1/search"
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "query": query,
        "top_k": 10,
        "response_format": "detailed",
    }

    t0 = time.perf_counter()
    resp = requests.post(url, json=payload, headers=headers, timeout=60)
    total_ms = (time.perf_counter() - t0) * 1000
    resp.raise_for_status()
    data = resp.json()

    # Extract stage timings from response
    stage_timings = data.get("stage_timings", {})

    return {
        "query": query,
        "total_http_ms": round(total_ms, 1),
        "stage_timings": stage_timings,
        "num_results": data.get("total_results", 0),
        "num_items": len(data.get("items", [])),
        "num_citations": len(data.get("citations", [])),
        "route": data.get("route", ""),
        "confidence_level": data.get("confidence_level", ""),
        "cached": data.get("cached", False),
    }


def main():
    parser = argparse.ArgumentParser(description="HECTOR Benchmark Adapter")
    parser.add_argument("--host", default=os.getenv("HECTOR_API_HOST", "localhost"))
    parser.add_argument("--port", type=int, default=int(os.getenv("HECTOR_API_PORT", 8000)))
    parser.add_argument("--query", required=True, help="Query to profile")
    parser.add_argument("--api-key", default=os.getenv("HECTOR_API_KEY"))

    args = parser.parse_args()

    result = profile_query(args.host, args.port, args.query, args.api_key)
    print(json.dumps(result, indent=2))

    # Print timing breakdown
    timings = result.get("stage_timings", {})
    if timings:
        print(f"\nStage Timing Breakdown:")
        print(f"  Routing:       {timings.get('route_ms', 0):.1f}ms")
        print(f"  Normalization: {timings.get('normalize_ms', 0):.1f}ms")
        print(f"  Generation:    {timings.get('generate_ms', 0):.1f}ms")
        print(f"  Verification:  {timings.get('verify_ms', 0):.1f}ms")
        print(f"  Total:         {timings.get('total_ms', 0):.1f}ms")

        # Identify bottleneck
        stages = {
            "routing": timings.get("route_ms", 0),
            "normalization": timings.get("normalize_ms", 0),
            "generation": timings.get("generate_ms", 0),
            "verification": timings.get("verify_ms", 0),
        }
        bottleneck = max(stages, key=stages.get)
        print(f"\n  Bottleneck: {bottleneck} ({stages[bottleneck]:.1f}ms)")


if __name__ == "__main__":
    main()
