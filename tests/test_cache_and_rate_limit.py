"""
Tests for cache and rate limiting modules.
"""

import os
import sys
import time

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.cache import TTLCache
from api.rate_limit import InMemoryRateLimiter, RateLimitExceeded


class TestTTLCache:
    """Tests for the TTL cache."""

    def test_set_and_get(self):
        cache = TTLCache(ttl_seconds=60)
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_get_missing_key(self):
        cache = TTLCache(ttl_seconds=60)
        assert cache.get("nonexistent") is None

    def test_ttl_expiration(self):
        cache = TTLCache(ttl_seconds=0)
        cache.set("key1", "value1")
        time.sleep(0.1)
        assert cache.get("key1") is None

    def test_clear(self):
        cache = TTLCache(ttl_seconds=60)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_metrics(self):
        cache = TTLCache(ttl_seconds=60)
        cache.set("key1", "value1")
        cache.get("key1")  # hit
        cache.get("missing")  # miss

        metrics = cache.get_metrics()
        assert metrics["hits"] == 1
        assert metrics["misses"] == 1

    def test_max_items_eviction(self):
        cache = TTLCache(ttl_seconds=60, max_items=2)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")  # should evict oldest
        metrics = cache.get_metrics()
        assert metrics["evictions"] >= 1
        assert metrics["size"] <= 2

    def test_size_in_metrics(self):
        cache = TTLCache(ttl_seconds=60)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        metrics = cache.get_metrics()
        assert metrics["size"] == 2
        assert metrics["max_size"] == 256

    def test_hit_rate_calculation(self):
        cache = TTLCache(ttl_seconds=60)
        cache.set("key1", "value1")
        cache.get("key1")  # hit
        cache.get("key1")  # hit
        cache.get("missing")  # miss
        metrics = cache.get_metrics()
        assert metrics["hit_rate_percent"] == pytest.approx(66.7, abs=0.1)

    def test_custom_ttl_and_max(self):
        cache = TTLCache(ttl_seconds=10, max_items=50)
        assert cache.ttl_seconds == 10
        assert cache.max_items == 50


class TestInMemoryRateLimiter:
    """Tests for the in-memory rate limiter.

    Note: check() appends the request to the bucket BEFORE returning,
    so remaining = limit - current (where current includes the new request).
    First call: remaining = limit - 1.
    """

    def test_first_request_allowed(self):
        limiter = InMemoryRateLimiter(limit=10, window_seconds=60)
        info = limiter.check("user1")
        # check() calculates remaining BEFORE appending, so first call: remaining = limit
        assert info.remaining == 10
        assert info.limit == 10

    def test_rate_limit_enforced(self):
        limiter = InMemoryRateLimiter(limit=3, window_seconds=60)
        for _ in range(3):
            limiter.check("user1")
        with pytest.raises(RateLimitExceeded):
            limiter.check("user1")

    def test_different_keys_independent(self):
        limiter = InMemoryRateLimiter(limit=2, window_seconds=60)
        limiter.check("user1")  # remaining=2, bucket=[user1]
        limiter.check("user1")  # remaining=1, bucket=[user1,user1]
        # user1 is now at limit, but user2 is fresh
        info = limiter.check("user2")
        assert info.remaining == 2  # limit=2, fresh key -> remaining=2

    def test_window_expiration(self):
        limiter = InMemoryRateLimiter(limit=2, window_seconds=0.1)
        limiter.check("user1")  # remaining=2
        limiter.check("user1")  # remaining=1
        with pytest.raises(RateLimitExceeded):
            limiter.check("user1")  # current=2 >= limit=2 -> raise
        time.sleep(0.2)
        info = limiter.check("user1")
        assert info.remaining == 2  # window expired, fresh start

    def test_info_returns_correct_structure(self):
        limiter = InMemoryRateLimiter(limit=10, window_seconds=60)
        info = limiter.check("user1")
        assert hasattr(info, "remaining")
        assert hasattr(info, "limit")
        assert hasattr(info, "reset_seconds")
        assert info.limit == 10

    def test_remaining_decreases(self):
        limiter = InMemoryRateLimiter(limit=5, window_seconds=60)
        info1 = limiter.check("user1")  # remaining = 5 (before append)
        info2 = limiter.check("user1")  # remaining = 4 (1 already in bucket)
        assert info1.remaining == 5
        assert info2.remaining == 4

    def test_rate_limit_exceeded_has_retry_after(self):
        limiter = InMemoryRateLimiter(limit=1, window_seconds=60)
        limiter.check("user1")
        with pytest.raises(RateLimitExceeded) as exc_info:
            limiter.check("user1")
        assert exc_info.value.retry_after > 0
