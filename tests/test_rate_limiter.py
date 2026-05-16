"""
Unit tests for Rate Limiter Module.
Tests rate limiting algorithms and configurations.
"""

import pytest
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.enterprise.rate_limiter import (
    RateLimitConfig,
    TokenBucket,
    SlidingWindowRateLimiter,
    RateLimitManager,
    IPRateLimiter,
    APIClientRateLimiter,
)


class TestTokenBucket:
    """Test token bucket algorithm."""

    def test_token_bucket_initialization(self):
        """Test token bucket initializes with correct capacity."""
        bucket = TokenBucket(capacity=10, refill_rate=1.0)
        assert bucket.capacity == 10
        assert bucket.tokens == 10

    def test_token_bucket_consume_success(self):
        """Test successful token consumption."""
        bucket = TokenBucket(capacity=10, refill_rate=1.0)
        result = bucket.consume(5)
        assert result is True
        assert bucket.tokens == 5

    def test_token_bucket_consume_failure(self):
        """Test failed token consumption when empty."""
        bucket = TokenBucket(capacity=5, refill_rate=0.1)
        bucket.consume(5)
        result = bucket.consume(1)
        assert result is False

    def test_token_bucket_refill(self):
        """Test token bucket refill over time."""
        bucket = TokenBucket(capacity=10, refill_rate=2.0)  # 2 tokens/sec
        bucket.consume(10)  # Empty bucket
        time.sleep(0.6)  # Wait for ~1.2 tokens
        result = bucket.consume(1)
        assert result is True


class TestSlidingWindowRateLimiter:
    """Test sliding window rate limiter."""

    def test_sliding_window_initialization(self):
        """Test limiter initializes correctly."""
        limiter = SlidingWindowRateLimiter(max_requests=10, window_seconds=60)
        assert limiter.max_requests == 10
        assert limiter.window_seconds == 60

    def test_sliding_window_allows_requests(self):
        """Test requests are allowed under limit."""
        limiter = SlidingWindowRateLimiter(max_requests=5, window_seconds=60)
        allowed_count = 0
        for _ in range(5):
            allowed, _ = limiter.is_allowed("client1")
            if allowed:
                allowed_count += 1
        assert allowed_count == 5

    def test_sliding_window_blocks_excess(self):
        """Test excess requests are blocked."""
        limiter = SlidingWindowRateLimiter(max_requests=3, window_seconds=60)
        # Make 3 requests (should all be allowed)
        for _ in range(3):
            allowed, _ = limiter.is_allowed("client2")
            assert allowed is True
        # 4th request should be blocked
        allowed, info = limiter.is_allowed("client2")
        assert allowed is False
        assert info['current'] == 3

    def test_sliding_window_different_clients(self):
        """Test different clients have separate limits."""
        limiter = SlidingWindowRateLimiter(max_requests=2, window_seconds=60)
        allowed1, _ = limiter.is_allowed("clientA")
        allowed2, _ = limiter.is_allowed("clientB")
        allowed3, _ = limiter.is_allowed("clientA")  # Should be blocked
        assert allowed1 is True
        assert allowed2 is True
        assert allowed3 is False


class TestIPRateLimiter:
    """Test IP-based rate limiter."""

    def test_ip_limiter_initialization(self):
        """Test IP limiter initializes with default config."""
        limiter = IPRateLimiter()
        assert limiter.config.requests_per_minute == 60

    def test_ip_limiter_allows_requests(self):
        """Test IP limiter allows requests."""
        limiter = IPRateLimiter(RateLimitConfig(requests_per_minute=60))
        allowed, info = limiter.check("192.168.1.1")
        assert allowed is True

    def test_ip_limiter_tracks_multiple_time_windows(self):
        """Test multiple time windows are tracked."""
        limiter = IPRateLimiter(RateLimitConfig(
            requests_per_minute=60,
            requests_per_hour=1000,
            requests_per_day=10000
        ))
        # Should have all three limiters
        assert limiter.limiter_minute is not None
        assert limiter.limiter_hour is not None
        assert limiter.limiter_day is not None


class TestAPIClientRateLimiter:
    """Test API client rate limiter."""

    def test_api_client_limiter_initialization(self):
        """Test API client limiter initializes."""
        limiter = APIClientRateLimiter()
        assert limiter.clients == {}

    def test_register_client(self):
        """Test client registration."""
        limiter = APIClientRateLimiter()
        result = limiter.register_client("client1", 100, 10000)
        assert result['client_id'] == "client1"
        assert result['limits']['per_minute'] == 100

    def test_check_registered_client(self):
        """Test checking registered client."""
        limiter = APIClientRateLimiter()
        limiter.register_client("client1", 10, 100)
        allowed, info = limiter.check("client1")
        assert allowed is True

    def test_check_unregistered_client(self):
        """Test unregistered client gets default access."""
        limiter = APIClientRateLimiter()
        allowed, info = limiter.check("unknown_client")
        assert allowed is True
        assert info['tier'] == "default"

    def test_client_usage_tracking(self):
        """Test client usage is tracked."""
        limiter = APIClientRateLimiter()
        limiter.register_client("client1", 10, 100)
        limiter.check("client1")
        limiter.check("client1")
        usage = limiter.get_client_usage("client1")
        assert usage['total_requests'] == 2


class TestRateLimitManager:
    """Test rate limit manager."""

    def test_manager_initialization(self):
        """Test manager initializes with default limiters."""
        manager = RateLimitManager()
        assert 'search' in manager.limiters
        assert 'api' in manager.limiters

    def test_add_limiter(self):
        """Test adding custom limiter."""
        manager = RateLimitManager()
        manager.add_limiter("custom", 50, 60)
        assert "custom" in manager.limiters

    def test_check_rate_limit(self):
        """Test rate limit checking."""
        manager = RateLimitManager()
        allowed, info = manager.check_rate_limit("client1", "search")
        assert 'allowed' in info

    def test_record_violation(self):
        """Test recording violations."""
        manager = RateLimitManager()
        manager.record_violation("client1", 60)
        # Should be blocked now
        allowed, info = manager.check_rate_limit("client1", "search")
        assert allowed is False


class TestRateLimitConfig:
    """Test rate limit configuration."""

    def test_config_defaults(self):
        """Test default configuration values."""
        config = RateLimitConfig()
        assert config.requests_per_minute == 60
        assert config.block_duration_seconds == 300


if __name__ == "__main__":
    pytest.main([__file__, "-v"])