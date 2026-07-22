"""Tests for the persistent query cache module."""

import os
import sys
import tempfile
import time

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.query_cache import QueryCache


@pytest.fixture
def cache(tmp_path):
    """Create a temporary cache for each test."""
    db_path = str(tmp_path / "test_cache.db")
    return QueryCache(db_path=db_path, ttl_seconds=5, max_entries=10)


class TestQueryCache:
    def test_set_and_get(self, cache):
        cache.set("what is murder?", "Murder is defined under BNS Section 101", route="LEGAL_RESEARCH")
        result = cache.get("what is murder?")
        assert result is not None
        assert result["response"] == "Murder is defined under BNS Section 101"

    def test_case_insensitive(self, cache):
        cache.set("What Is Murder?", "response A")
        result = cache.get("what is murder?")
        assert result is not None
        assert result["response"] == "response A"

    def test_cache_miss(self, cache):
        result = cache.get("nonexistent query")
        assert result is None

    def test_ttl_expiry(self, cache):
        cache.set("expires soon", "temporary", ttl_override=0)
        time.sleep(0.01)
        result = cache.get("expires soon")
        assert result is None

    def test_invalidate(self, cache):
        cache.set("to be deleted", "bye")
        assert cache.invalidate("to be deleted") is True
        assert cache.get("to be deleted") is None

    def test_invalidate_nonexistent(self, cache):
        assert cache.invalidate("does not exist") is False

    def test_clear(self, cache):
        cache.set("q1", "a1")
        cache.set("q2", "a2")
        cleared = cache.clear()
        assert cleared == 2
        assert cache.get("q1") is None
        assert cache.get("q2") is None

    def test_stats(self, cache):
        cache.set("query a", "answer a")
        cache.get("query a")  # hit
        cache.get("query b")  # miss
        stats = cache.stats()
        assert stats["total_requests"] >= 1
        assert stats["active_entries"] >= 1
        assert "popular_queries" in stats

    def test_eviction(self, tmp_path):
        db_path = str(tmp_path / "small_cache.db")
        cache = QueryCache(db_path=db_path, ttl_seconds=60, max_entries=3)
        for i in range(5):
            cache.set(f"query {i}", f"answer {i}")
        stats = cache.stats()
        assert stats["total_entries"] <= 3
        assert stats["evictions"] >= 1

    def test_timing_stored(self, cache):
        cache.set("timed query", "response", timing={"total_ms": 123.4})
        result = cache.get("timed query")
        assert result["timing"]["total_ms"] == 123.4

    def test_popular_queries(self, cache):
        cache.set("popular", "answer")
        for _ in range(3):
            cache.get("popular")
        stats = cache.stats()
        assert len(stats["popular_queries"]) >= 1
        assert stats["popular_queries"][0]["query"] == "popular"
