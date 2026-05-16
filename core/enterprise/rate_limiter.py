"""
Rate Limiting for HECTOR Enterprise.
Provides token bucket and sliding window rate limiters.
"""

from __future__ import annotations
import time
import threading
from dataclasses import dataclass, field
from typing import Callable
from collections import defaultdict
import hashlib


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst_size: int = 10
    block_duration_seconds: int = 300  # 5 minutes


class TokenBucket:
    """Token bucket algorithm for rate limiting."""

    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.tokens = capacity
        self.last_refill = time.time()
        self._lock = threading.Lock()

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        new_tokens = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_refill = now

    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens. Returns True if allowed."""
        with self._lock:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False


class SlidingWindowRateLimiter:
    """Sliding window rate limiter."""

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: dict[str, list[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def _get_client_key(self, identifier: str) -> str:
        """Generate a unique key for the client."""
        return hashlib.sha256(identifier.encode()).hexdigest()[:16]

    def is_allowed(self, identifier: str) -> tuple[bool, dict]:
        """Check if request is allowed. Returns (allowed, info)."""
        key = self._get_client_key(identifier)
        now = time.time()
        window_start = now - self.window_seconds

        with self._lock:
            # Remove old requests outside the window
            self.requests[key] = [
                t for t in self.requests[key]
                if t > window_start
            ]

            # Check if under limit
            current_count = len(self.requests[key])
            remaining = self.max_requests - current_count

            if current_count >= self.max_requests:
                return False, {
                    "allowed": False,
                    "current": current_count,
                    "max": self.max_requests,
                    "window_seconds": self.window_seconds,
                    "retry_after": int(self.requests[key][0] - window_start + 1) if self.requests[key] else 0
                }

            # Allow request
            self.requests[key].append(now)
            return True, {
                "allowed": True,
                "current": current_count + 1,
                "max": self.max_requests,
                "remaining": remaining - 1
            }

    def reset(self, identifier: str) -> None:
        """Reset rate limit for a client."""
        key = self._get_client_key(identifier)
        with self._lock:
            if key in self.requests:
                del self.requests[key]


class RateLimitManager:
    """Manages multiple rate limiters."""

    def __init__(self):
        self.limiters: dict[str, SlidingWindowRateLimiter] = {}
        self.blocked_clients: dict[str, float] = {}
        self._lock = threading.Lock()

    def add_limiter(
        self,
        name: str,
        max_requests: int,
        window_seconds: int
    ) -> None:
        """Add a named rate limiter."""
        with self._lock:
            self.limiters[name] = SlidingWindowRateLimiter(
                max_requests, window_seconds
            )

    def check_rate_limit(
        self,
        client_id: str,
        limiter_name: str = "default"
    ) -> tuple[bool, dict]:
        """Check rate limit for a client."""
        with self._lock:
            # Check if blocked
            if client_id in self.blocked_clients:
                block_until = self.blocked_clients[client_id]
                if time.time() < block_until:
                    return False, {
                        "error": "blocked",
                        "blocked_until": int(block_until - time.time()),
                        "reason": "Too many violations"
                    }
                else:
                    del self.blocked_clients[client_id]

            # Get limiter
            limiter = self.limiters.get(limiter_name)
            if not limiter:
                return True, {"allowed": True, "message": "No limiter configured"}

            # Check limit
            return limiter.is_allowed(client_id)

    def record_violation(self, client_id: str, block_duration: int = 300) -> None:
        """Record a rate limit violation and block the client."""
        with self._lock:
            self.blocked_clients[client_id] = time.time() + block_duration

    def get_client_stats(self, client_id: str) -> dict:
        """Get rate limit statistics for a client."""
        stats = {}
        with self._lock:
            for name, limiter in self.limiters.items():
                key = limiter._get_client_key(client_id)
                if key in limiter.requests:
                    stats[name] = {
                        "requests": len(limiter.requests[key]),
                        "oldest": min(limiter.requests[key]) if limiter.requests[key] else 0
                    }
        return stats


class IPRateLimiter:
    """Rate limiter specifically for IP addresses."""

    def __init__(self, config: RateLimitConfig | None = None):
        self.config = config or RateLimitConfig()
        self.limiter_minute = SlidingWindowRateLimiter(
            self.config.requests_per_minute, 60
        )
        self.limiter_hour = SlidingWindowRateLimiter(
            self.config.requests_per_hour, 3600
        )
        self.limiter_day = SlidingWindowRateLimiter(
            self.config.requests_per_day, 86400
        )

    def check(self, ip_address: str) -> tuple[bool, dict]:
        """Check rate limit for an IP address."""
        # Check all time windows
        allowed, info = self.limiter_minute.is_allowed(f"min_{ip_address}")
        if not allowed:
            self._record_violation(ip_address, "minute")
            return False, {**info, "scope": "per minute"}

        allowed, info = self.limiter_hour.is_allowed(f"hour_{ip_address}")
        if not allowed:
            self._record_violation(ip_address, "hour")
            return False, {**info, "scope": "per hour"}

        allowed, info = self.limiter_day.is_allowed(f"day_{ip_address}")
        if not allowed:
            self._record_violation(ip_address, "day")
            return False, {**info, "scope": "per day"}

        return True, {"allowed": True}

    def _record_violation(self, ip_address: str, scope: str) -> None:
        """Record a violation (could integrate with blocklist)."""
        pass  # Could add to blocked list if needed


class APIClientRateLimiter:
    """Rate limiter for API clients using API keys."""

    def __init__(self):
        self.clients: dict[str, dict] = {}
        self._lock = threading.Lock()

    def register_client(
        self,
        client_id: str,
        requests_per_minute: int = 60,
        requests_per_day: int = 10000
    ) -> dict:
        """Register a new API client with rate limits."""
        with self._lock:
            self.clients[client_id] = {
                "requests_per_minute": requests_per_minute,
                "requests_per_day": requests_per_day,
                "limiter_minute": SlidingWindowRateLimiter(requests_per_minute, 60),
                "limiter_day": SlidingWindowRateLimiter(requests_per_day, 86400),
                "total_requests": 0,
                "created_at": time.time()
            }
            return {
                "client_id": client_id,
                "limits": {
                    "per_minute": requests_per_minute,
                    "per_day": requests_per_day
                }
            }

    def check(self, client_id: str) -> tuple[bool, dict]:
        """Check rate limit for an API client."""
        with self._lock:
            client = self.clients.get(client_id)
            if not client:
                # Unregistered clients get default limits
                return True, {"allowed": True, "tier": "default"}

            # Check minute limit
            allowed, info = client["limiter_minute"].is_allowed(client_id)
            if not allowed:
                return False, {**info, "limit_type": "per_minute"}

            # Check day limit
            allowed, info = client["limiter_day"].is_allowed(f"day_{client_id}")
            if not allowed:
                return False, {**info, "limit_type": "per_day"}

            # Update total
            client["total_requests"] += 1

            return True, {
                "allowed": True,
                "tier": "premium",
                "total_requests": client["total_requests"]
            }

    def get_client_usage(self, client_id: str) -> dict:
        """Get usage statistics for a client."""
        with self._lock:
            client = self.clients.get(client_id)
            if not client:
                return {"error": "Client not found"}

            return {
                "total_requests": client["total_requests"],
                "limits": {
                    "per_minute": client["requests_per_minute"],
                    "per_day": client["requests_per_day"]
                },
                "created_at": client["created_at"]
            }


# Global rate limit manager instance
_rate_limit_manager: RateLimitManager | None = None


def get_rate_limit_manager() -> RateLimitManager:
    """Get the global rate limit manager."""
    global _rate_limit_manager
    if _rate_limit_manager is None:
        _rate_limit_manager = RateLimitManager()
        # Add default limiters
        _rate_limit_manager.add_limiter("search", 60, 60)  # 60 searches per minute
        _rate_limit_manager.add_limiter("api", 100, 60)    # 100 API calls per minute
        _rate_limit_manager.add_limiter("ingest", 10, 3600) # 10 uploads per hour
    return _rate_limit_manager


def check_rate_limit(
    client_id: str,
    limiter_name: str = "default"
) -> tuple[bool, dict]:
    """Convenience function to check rate limit."""
    return get_rate_limit_manager().check_rate_limit(client_id, limiter_name)