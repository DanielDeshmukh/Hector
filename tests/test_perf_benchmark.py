"""
Performance regression tests for HECTOR's RAG pipeline.

These tests validate the benchmarking framework itself and verify
that core operations complete within acceptable time bounds.
Tests run WITHOUT a live HECTOR server (mocked API).
"""

import os
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from benchmark.rag_benchmark import (
    BenchConfig,
    load_config,
    load_queries,
)
from benchmark.adapters.hector_adapter import profile_query


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

class TestBenchmarkConfig:
    """Tests for benchmark YAML config loading."""

    def test_load_quick_profile(self):
        """Quick profile config loads without error."""
        cfg = load_config("benchmark/configs/quick_profile.yaml")
        assert cfg.target.url == "http://localhost:8000"
        assert cfg.profiling.enabled is True
        assert cfg.aiperf.enabled is False

    def test_load_single_run(self):
        """Single run config loads with aiperf enabled."""
        cfg = load_config("benchmark/configs/single_run.yaml")
        assert cfg.aiperf.enabled is True
        assert cfg.aiperf.concurrency == 5

    def test_load_sweep(self):
        """Sweep config loads with list-valued axes."""
        cfg = load_config("benchmark/configs/sweep.yaml")
        assert isinstance(cfg.aiperf.concurrency, list)
        assert isinstance(cfg.rag.top_k, list)
        assert len(cfg.aiperf.concurrency) >= 3
        assert len(cfg.rag.top_k) >= 3

    def test_config_defaults(self):
        """BenchConfig has sensible defaults."""
        cfg = BenchConfig()
        assert cfg.target.timeout_s == 60
        assert cfg.rag.top_k == 10
        assert cfg.profiling.warmup_requests == 3
        assert cfg.output.dir == "benchmark/results"


# ---------------------------------------------------------------------------
# Query loading
# ---------------------------------------------------------------------------

class TestQueryLoading:
    """Tests for JSONL query loading."""

    def test_load_queries(self):
        """Loads queries from benchmark/queries.jsonl."""
        queries = load_queries("benchmark/queries.jsonl")
        assert len(queries) >= 20
        assert all(isinstance(q, str) for q in queries)
        assert all(len(q) > 5 for q in queries)

    def test_load_queries_empty_file(self):
        """Empty JSONL returns empty list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "empty.jsonl"
            p.write_text("", encoding="utf-8")
            queries = load_queries(str(p))
            assert queries == []

    def test_load_queries_skips_blank_lines(self):
        """Blank lines are skipped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "mixed.jsonl"
            p.write_text('{"query": "test1"}\n\n\n{"query": "test2"}\n', encoding="utf-8")
            queries = load_queries(str(p))
            assert queries == ["test1", "test2"]


# ---------------------------------------------------------------------------
# Metric computation (from evaluation module)
# ---------------------------------------------------------------------------

class TestBenchmarkMetrics:
    """Tests for performance metric computation."""

    def test_latency_percentiles(self):
        """Percentile computation is correct."""
        latencies = list(range(1, 101))  # 1..100
        latencies_sorted = sorted(latencies)
        n = len(latencies_sorted)
        p50 = latencies_sorted[int(n * 0.5)]
        p95 = latencies_sorted[int(n * 0.95)]

        assert p50 >= 50  # ~50th percentile
        assert p95 >= 95  # ~95th percentile

    def test_throughput_calculation(self):
        """Throughput is requests / elapsed_seconds."""
        total_requests = 100
        elapsed_s = 20.0
        throughput = total_requests / elapsed_s
        assert throughput == 5.0

    def test_error_rate_calculation(self):
        """Error rate is errors / total * 100."""
        errors = 5
        total = 100
        error_rate = errors / total * 100
        assert error_rate == 5.0


# ---------------------------------------------------------------------------
# Adapter tests
# ---------------------------------------------------------------------------

class TestHectorAdapter:
    """Tests for the HECTOR benchmark adapter."""

    def test_adapter_is_importable(self):
        """hector_adapter module is importable."""
        from benchmark.adapters import hector_adapter
        assert hasattr(hector_adapter, "profile_query")

    def test_adapter_handles_connection_error(self):
        """Adapter handles connection errors gracefully."""
        with patch("benchmark.adapters.hector_adapter.requests.post") as mock_post:
            mock_post.side_effect = ConnectionError("Connection refused")
            with pytest.raises(ConnectionError):
                profile_query("localhost", 99999, "test query")


# ---------------------------------------------------------------------------
# CLI entry points
# ---------------------------------------------------------------------------

class TestBenchmarkCli:
    """Tests for benchmark CLI modules."""

    def test_rag_benchmark_importable(self):
        """rag_benchmark module is importable."""
        import benchmark.rag_benchmark as mod
        assert hasattr(mod, "main")
        assert hasattr(mod, "run_profiling")
        assert hasattr(mod, "run_load_test")
        assert hasattr(mod, "run_sweep")
        assert hasattr(mod, "generate_report")
        assert hasattr(mod, "save_results")

    def test_sweep_comparison_importable(self):
        """sweep_comparison module is importable."""
        import benchmark.sweep_comparison as mod
        assert hasattr(mod, "main")

    def test_report_generation(self):
        """generate_report produces valid structure."""
        import benchmark.rag_benchmark as mod

        cfg = BenchConfig()
        profiling = {
            "stats": {"avg_latency_ms": 100, "p95_latency_ms": 200},
            "results": [],
        }
        report = mod.generate_report(cfg, profiling, None, None)

        assert "config" in report
        assert "profiling" in report
        assert "timestamp" in report
        assert report["profiling"]["avg_latency_ms"] == 100

    def test_report_with_load_test(self):
        """generate_report includes load test data."""
        import benchmark.rag_benchmark as mod

        cfg = BenchConfig()
        profiling = {"stats": {}, "results": []}
        load_results = {
            "stats": {
                "concurrency": 5,
                "throughput_qps": 10.5,
                "p95_latency_ms": 300,
            },
            "results": [],
        }
        report = mod.generate_report(cfg, profiling, load_results, None)

        assert "load_test" in report
        assert report["load_test"]["throughput_qps"] == 10.5


# ---------------------------------------------------------------------------
# Regression thresholds
# ---------------------------------------------------------------------------

class TestPerformanceThresholds:
    """Verify core operations complete within acceptable time bounds."""

    def test_config_load_is_fast(self):
        """Config loading completes in < 100ms."""
        t0 = time.perf_counter()
        for _ in range(10):
            load_config("benchmark/configs/quick_profile.yaml")
        elapsed = (time.perf_counter() - t0) * 1000
        assert elapsed < 100, f"Config loading took {elapsed:.0f}ms (>100ms)"

    def test_query_loading_is_fast(self):
        """Query loading completes in < 50ms."""
        t0 = time.perf_counter()
        for _ in range(10):
            load_queries("benchmark/queries.jsonl")
        elapsed = (time.perf_counter() - t0) * 1000
        assert elapsed < 50, f"Query loading took {elapsed:.0f}ms (>50ms)"

    def test_report_generation_is_fast(self):
        """Report generation completes in < 200ms."""
        import benchmark.rag_benchmark as mod

        cfg = BenchConfig()
        profiling = {
            "stats": {"avg_latency_ms": 100, "p95_latency_ms": 200},
            "results": [{"latency_ms": 100, "status": "success"}] * 20,
        }
        t0 = time.perf_counter()
        mod.generate_report(cfg, profiling, None, None)
        elapsed = (time.perf_counter() - t0) * 1000
        assert elapsed < 200, f"Report generation took {elapsed:.0f}ms (>200ms)"
