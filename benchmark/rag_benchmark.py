#!/usr/bin/env python3
"""
HECTOR Performance Benchmark CLI

Config-driven performance benchmarking for HECTOR's RAG pipeline.
Profiles per-stage timing, measures throughput under load, and
identifies bottlenecks.

Usage:
    python benchmark/rag_benchmark.py -c benchmark/configs/quick_profile.yaml
    python benchmark/rag_benchmark.py -c benchmark/configs/single_run.yaml
    python benchmark/rag_benchmark.py -c benchmark/configs/sweep.yaml
"""

import argparse
import csv
import json
import os
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import requests
import yaml


# ---------------------------------------------------------------------------
# Config models
# ---------------------------------------------------------------------------

@dataclass
class TargetConfig:
    url: str = "http://localhost:8000"
    timeout_s: int = 60


@dataclass
class RagConfig:
    endpoint: str = "/v1/search"
    method: str = "POST"
    collection_names: list[str] = field(default_factory=lambda: ["indian_law_bns"])
    top_k: int | list[int] = 10
    response_format: str = "detailed"


@dataclass
class ProfilingConfig:
    enabled: bool = True
    warmup_requests: int = 3
    profile_requests: int = 20
    capture_stage_timings: bool = True


@dataclass
class AiperfConfig:
    enabled: bool = False
    concurrency: int | list[int] = 5
    iterations: int = 3
    duration_s: int = 60
    sleep_between_points_s: int = 0


@dataclass
class InputConfig:
    file: str = "benchmark/queries.jsonl"


@dataclass
class OutputConfig:
    dir: str = "benchmark/results"
    experiment_name: str = "benchmark"


@dataclass
class BenchConfig:
    target: TargetConfig = field(default_factory=TargetConfig)
    rag: RagConfig = field(default_factory=RagConfig)
    profiling: ProfilingConfig = field(default_factory=ProfilingConfig)
    aiperf: AiperfConfig = field(default_factory=AiperfConfig)
    input: InputConfig = field(default_factory=InputConfig)
    output: OutputConfig = field(default_factory=OutputConfig)


def load_config(path: str) -> BenchConfig:
    """Load YAML config into BenchConfig."""
    with open(path, "r") as f:
        raw = yaml.safe_load(f)

    cfg = BenchConfig()
    if "target" in raw:
        cfg.target = TargetConfig(**raw["target"])
    if "rag" in raw:
        cfg.rag = RagConfig(**raw["rag"])
    if "profiling" in raw:
        cfg.profiling = ProfilingConfig(**raw["profiling"])
    if "aiperf" in raw:
        cfg.aiperf = AiperfConfig(**raw["aiperf"])
    if "input" in raw:
        cfg.input = InputConfig(**raw["input"])
    if "output" in raw:
        cfg.output = OutputConfig(**raw["output"])
    return cfg


# ---------------------------------------------------------------------------
# Query loader
# ---------------------------------------------------------------------------

def load_queries(path: str) -> list[str]:
    """Load queries from a JSONL file."""
    queries = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if "query" in obj:
                queries.append(obj["query"])
    return queries


# ---------------------------------------------------------------------------
# HECTOR API client
# ---------------------------------------------------------------------------

def query_hector(
    url: str,
    query: str,
    top_k: int = 10,
    timeout: int = 60,
    api_key: str | None = None,
) -> dict[str, Any]:
    """Send a single query to HECTOR and return timing + response data."""
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "query": query,
        "top_k": top_k,
        "response_format": "detailed",
    }

    t0 = time.perf_counter()
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        resp.raise_for_status()
        data = resp.json()
        return {
            "status": "success",
            "latency_ms": round(elapsed_ms, 1),
            "num_results": data.get("total_results", 0),
            "num_items": len(data.get("items", [])),
            "num_citations": len(data.get("citations", [])),
            "answer_length": len(data.get("generated_response", "")),
            "route": data.get("route", ""),
            "cached": data.get("cached", False),
            "confidence_level": data.get("confidence_level", ""),
        }
    except Exception as e:
        elapsed_ms = (time.perf_counter() - t0) * 1000
        return {
            "status": "error",
            "latency_ms": round(elapsed_ms, 1),
            "error": str(e),
        }


# ---------------------------------------------------------------------------
# Profiling phase
# ---------------------------------------------------------------------------

def run_profiling(
    cfg: BenchConfig,
    queries: list[str],
    api_key: str | None = None,
) -> dict[str, Any]:
    """Run profiling phase — sequential queries with per-stage timing."""
    if not cfg.profiling.enabled:
        return {"skipped": True}

    url = cfg.target.url + cfg.rag.endpoint
    top_k = cfg.rag.top_k if isinstance(cfg.rag.top_k, int) else cfg.rag.top_k[0]
    warmup = cfg.profiling.warmup_requests
    profile_n = cfg.profiling.profile_requests

    print(f"\n  [PROFILING] Warmup: {warmup} | Profile: {profile_n}")

    # Warmup
    for i in range(warmup):
        q = queries[i % len(queries)]
        query_hector(url, q, top_k, cfg.target.timeout_s, api_key)
        print(f"    warmup {i+1}/{warmup} done")

    # Profile
    results = []
    for i in range(profile_n):
        q = queries[i % len(queries)]
        r = query_hector(url, q, top_k, cfg.target.timeout_s, api_key)
        r["query_index"] = i
        r["query"] = q[:80]
        results.append(r)
        status_icon = "+" if r["status"] == "success" else "x"
        print(f"    profile {i+1}/{profile_n} [{status_icon}] {r['latency_ms']:.0f}ms")

    # Compute stats
    latencies = [r["latency_ms"] for r in results if r["status"] == "success"]
    errors = [r for r in results if r["status"] == "error"]

    stats = {}
    if latencies:
        latencies_sorted = sorted(latencies)
        stats = {
            "total_requests": len(results),
            "successful": len(latencies),
            "errors": len(errors),
            "avg_latency_ms": round(statistics.mean(latencies), 1),
            "median_latency_ms": round(statistics.median(latencies), 1),
            "p95_latency_ms": round(latencies_sorted[int(len(latencies_sorted) * 0.95)], 1) if len(latencies_sorted) >= 2 else round(latencies_sorted[-1], 1),
            "p99_latency_ms": round(latencies_sorted[int(len(latencies_sorted) * 0.99)], 1) if len(latencies_sorted) >= 2 else round(latencies_sorted[-1], 1),
            "min_latency_ms": round(min(latencies), 1),
            "max_latency_ms": round(max(latencies), 1),
            "std_dev_ms": round(statistics.stdev(latencies), 1) if len(latencies) > 1 else 0,
        }

    return {"stats": stats, "results": results, "errors": errors}


# ---------------------------------------------------------------------------
# Load testing phase
# ---------------------------------------------------------------------------

def run_load_test(
    cfg: BenchConfig,
    queries: list[str],
    concurrency: int,
    api_key: str | None = None,
) -> dict[str, Any]:
    """Run load test phase — concurrent queries at specified concurrency."""
    if not cfg.aiperf.enabled:
        return {"skipped": True}

    url = cfg.target.url + cfg.rag.endpoint
    top_k = cfg.rag.top_k if isinstance(cfg.rag.top_k, int) else cfg.rag.top_k[0]
    iterations = cfg.aiperf.iterations
    duration_s = cfg.aiperf.duration_s

    print(f"\n  [LOAD TEST] Concurrency: {concurrency} | Iterations: {iterations} | Duration: {duration_s}s")

    all_results = []
    start_time = time.time()
    query_idx = 0

    def worker():
        nonlocal query_idx
        while time.time() - start_time < duration_s:
            idx = query_idx % len(queries)
            query_idx += 1
            r = query_hector(url, queries[idx], top_k, cfg.target.timeout_s, api_key)
            all_results.append(r)

    # Launch concurrent workers
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(worker) for _ in range(concurrency)]
        for f in futures:
            f.result()

    elapsed = time.time() - start_time
    latencies = [r["latency_ms"] for r in all_results if r["status"] == "success"]
    errors = [r for r in all_results if r["status"] == "error"]

    stats = {}
    if latencies:
        latencies_sorted = sorted(latencies)
        throughput = len(latencies) / elapsed if elapsed > 0 else 0
        stats = {
            "concurrency": concurrency,
            "elapsed_s": round(elapsed, 1),
            "total_requests": len(all_results),
            "successful": len(latencies),
            "errors": len(errors),
            "error_rate": round(len(errors) / len(all_results) * 100, 1) if all_results else 0,
            "throughput_qps": round(throughput, 2),
            "avg_latency_ms": round(statistics.mean(latencies), 1),
            "median_latency_ms": round(statistics.median(latencies), 1),
            "p95_latency_ms": round(latencies_sorted[int(len(latencies_sorted) * 0.95)], 1) if len(latencies_sorted) >= 2 else round(latencies_sorted[-1], 1),
            "p99_latency_ms": round(latencies_sorted[int(len(latencies_sorted) * 0.99)], 1) if len(latencies_sorted) >= 2 else round(latencies_sorted[-1], 1),
            "min_latency_ms": round(min(latencies), 1),
            "max_latency_ms": round(max(latencies), 1),
        }

    return {"stats": stats, "results": all_results}


# ---------------------------------------------------------------------------
# Sweep
# ---------------------------------------------------------------------------

def run_sweep(
    cfg: BenchConfig,
    queries: list[str],
    api_key: str | None = None,
) -> list[dict[str, Any]]:
    """Run sweep across all axis combinations."""
    concurrencies = cfg.aiperf.concurrency if isinstance(cfg.aiperf.concurrency, list) else [cfg.aiperf.concurrency]
    top_ks = cfg.rag.top_k if isinstance(cfg.rag.top_k, list) else [cfg.rag.top_k]

    sweep_results = []
    total_points = len(concurrencies) * len(top_ks)
    point_idx = 0

    for cr in concurrencies:
        for tk in top_ks:
            point_idx += 1
            print(f"\n{'='*60}")
            print(f"  SWEEP POINT {point_idx}/{total_points}: concurrency={cr}, top_k={tk}")
            print(f"{'='*60}")

            # Temporarily override config
            orig_top_k = cfg.rag.top_k
            orig_concurrency = cfg.aiperf.concurrency
            orig_enabled = cfg.aiperf.enabled
            orig_iterations = cfg.aiperf.iterations
            orig_duration = cfg.aiperf.duration_s

            cfg.rag.top_k = tk
            cfg.aiperf.concurrency = cr
            cfg.aiperf.enabled = True
            cfg.aiperf.iterations = 1
            cfg.aiperf.duration_s = 15  # Shorter for sweep points

            result = run_load_test(cfg, queries, cr, api_key)
            result["top_k"] = tk
            result["concurrency"] = cr
            sweep_results.append(result)

            # Restore config
            cfg.rag.top_k = orig_top_k
            cfg.aiperf.concurrency = orig_concurrency
            cfg.aiperf.enabled = orig_enabled
            cfg.aiperf.iterations = orig_iterations
            cfg.aiperf.duration_s = orig_duration

            if cfg.aiperf.sleep_between_points_s > 0:
                time.sleep(cfg.aiperf.sleep_between_points_s)

    return sweep_results


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate_report(
    cfg: BenchConfig,
    profiling: dict[str, Any],
    load_results: list[dict[str, Any]] | dict[str, Any] | None,
    sweep_results: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    """Generate unified benchmark report."""
    report = {
        "config": {
            "target": cfg.target.url,
            "top_k": cfg.rag.top_k,
            "collection": cfg.rag.collection_names,
        },
        "profiling": profiling.get("stats", {}),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    if load_results and isinstance(load_results, dict) and "stats" in load_results:
        report["load_test"] = load_results["stats"]

    if sweep_results:
        report["sweep"] = [
            {
                "concurrency": s.get("concurrency"),
                "top_k": s.get("top_k"),
                **(s.get("stats", {})),
            }
            for s in sweep_results
            if s.get("stats")
        ]

    return report


def save_results(
    report: dict[str, Any],
    profiling: dict[str, Any],
    load_results: dict[str, Any] | None,
    sweep_results: list[dict[str, Any]] | None,
    output_dir: str,
    experiment_name: str,
) -> Path:
    """Save all results to disk."""
    run_dir = Path(output_dir) / f"{experiment_name}_run_{int(time.time())}"
    run_dir.mkdir(parents=True, exist_ok=True)

    # Main report
    with open(run_dir / "report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Profiling details
    if profiling.get("results"):
        with open(run_dir / "profiling_results.json", "w", encoding="utf-8") as f:
            json.dump(profiling["results"], f, indent=2, ensure_ascii=False)

    # Load test details
    if load_results and load_results.get("results"):
        with open(run_dir / "load_test_results.json", "w", encoding="utf-8") as f:
            json.dump(load_results["results"], f, indent=2, ensure_ascii=False)

    # Sweep results
    if sweep_results:
        with open(run_dir / "sweep_results.json", "w", encoding="utf-8") as f:
            json.dump(sweep_results, f, indent=2, ensure_ascii=False)

        # CSV for easy analysis
        csv_path = run_dir / "sweep_results.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            if sweep_results and sweep_results[0].get("stats"):
                writer = csv.DictWriter(f, fieldnames=list(sweep_results[0]["stats"].keys()))
                writer.writeheader()
                for s in sweep_results:
                    if s.get("stats"):
                        writer.writerow(s["stats"])

    # Human-readable report
    with open(run_dir / "report.md", "w", encoding="utf-8") as f:
        f.write(_format_markdown_report(report))

    return run_dir


def _format_markdown_report(report: dict[str, Any]) -> str:
    """Format report as markdown."""
    lines = [
        "# HECTOR Performance Benchmark Report",
        "",
        f"**Target:** {report.get('config', {}).get('target', 'unknown')}",
        f"**Timestamp:** {report.get('timestamp', 'unknown')}",
        f"**Top-K:** {report.get('config', {}).get('top_k', 'unknown')}",
        "",
    ]

    # Profiling
    prof = report.get("profiling", {})
    if prof and prof.get("total_requests"):
        lines.extend([
            "## Profiling Results",
            "",
            "| Metric | Value |",
        ...])
        for key, val in prof.items():
            lines.append(f"| {key} | {val} |")
        lines.append("")

    # Load test
    load = report.get("load_test", {})
    if load and load.get("total_requests"):
        lines.extend([
            "## Load Test Results",
            "",
            "| Metric | Value |",
            "|--------|-------|",
        ])
        for key, val in load.items():
            lines.append(f"| {key} | {val} |")
        lines.append("")

    # Sweep
    sweep = report.get("sweep", [])
    if sweep:
        lines.extend([
            "## Sweep Results",
            "",
            "| Concurrency | Top-K | Throughput (QPS) | Avg Latency (ms) | P95 Latency (ms) | Errors |",
            "|-------------|-------|-------------------|-------------------|-------------------|--------|",
        ])
        for s in sweep:
            lines.append(
                f"| {s.get('concurrency', '-')} | {s.get('top_k', '-')} | "
                f"{s.get('throughput_qps', '-')} | {s.get('avg_latency_ms', '-')} | "
                f"{s.get('p95_latency_ms', '-')} | {s.get('errors', '-')} |"
            )
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="HECTOR Performance Benchmark",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-c", "--config",
        required=True,
        help="Path to YAML config file",
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("HECTOR_API_KEY"),
        help="HECTOR API key",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="HECTOR Benchmark 1.0.0",
    )

    args = parser.parse_args()

    # Load config
    cfg = load_config(args.config)
    print(f"\n{'='*60}")
    print("  HECTOR Performance Benchmark")
    print(f"{'='*60}")
    print(f"  Target:     {cfg.target.url}")
    print(f"  Config:     {args.config}")
    print(f"  Experiment: {cfg.output.experiment_name}")
    print(f"{'='*60}")

    # Load queries
    queries = load_queries(cfg.input.file)
    print(f"  Queries loaded: {len(queries)}")

    # Phase 1: Profiling
    profiling = {"skipped": True}
    if cfg.profiling.enabled:
        profiling = run_profiling(cfg, queries, args.api_key)
        if profiling.get("stats"):
            s = profiling["stats"]
            print("\n  [PROFILING DONE]")
            print(f"    Avg: {s.get('avg_latency_ms', 0):.0f}ms | "
                  f"P95: {s.get('p95_latency_ms', 0):.0f}ms | "
                  f"Throughput: {s.get('successful', 0) / max(profiling.get('results', [{}]).__len__(), 1):.1f} QPS")

    # Phase 2: Load test (single point or sweep)
    load_results = None
    sweep_results = None

    if cfg.aiperf.enabled:
        concurrencies = cfg.aiperf.concurrency if isinstance(cfg.aiperf.concurrency, list) else [cfg.aiperf.concurrency]
        top_ks = cfg.rag.top_k if isinstance(cfg.rag.top_k, list) else [cfg.rag.top_k]

        if len(concurrencies) > 1 or len(top_ks) > 1:
            sweep_results = run_sweep(cfg, queries, args.api_key)
        else:
            load_results = run_load_test(cfg, queries, concurrencies[0], args.api_key)
            if load_results.get("stats"):
                s = load_results["stats"]
                print("\n  [LOAD TEST DONE]")
                print(f"    Throughput: {s.get('throughput_qps', 0):.1f} QPS | "
                      f"Avg: {s.get('avg_latency_ms', 0):.0f}ms | "
                      f"P95: {s.get('p95_latency_ms', 0):.0f}ms | "
                      f"Errors: {s.get('error_rate', 0):.1f}%")

    # Generate report
    report = generate_report(cfg, profiling, load_results, sweep_results)

    # Save results
    run_dir = save_results(report, profiling, load_results, sweep_results,
                           cfg.output.dir, cfg.output.experiment_name)

    print(f"\n{'='*60}")
    print("  BENCHMARK COMPLETE")
    print(f"{'='*60}")
    print(f"  Results saved to: {run_dir}")
    print(f"  Report: {run_dir / 'report.md'}")
    print(f"  JSON:   {run_dir / 'report.json'}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
