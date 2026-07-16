import threading
import time
from collections import defaultdict
from dataclasses import dataclass


class RateLimitExceeded(Exception):
    """Raised when a client crosses the configured request budget."""

    def __init__(self, message: str, retry_after: int = 60):
        super().__init__(message)
        self.retry_after = retry_after


@dataclass
class RateLimitInfo:
    """Rate limit state for a single key."""

    limit: int
    remaining: int
    reset_seconds: int


class _TokenBucket:
    """Token bucket for a single rate-limit key."""

    __slots__ = ("tokens", "max_tokens", "refill_rate", "last_refill")

    def __init__(self, max_tokens: int, refill_rate: float):
        self.tokens = float(max_tokens)
        self.max_tokens = max_tokens
        self.refill_rate = refill_rate  # tokens per second
        self.last_refill = time.monotonic()

    def consume(self, now: float) -> bool:
        """Try to consume one token. Returns True if allowed."""
        elapsed = now - self.last_refill
        self.tokens = min(self.max_tokens, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True
        return False

    def retry_after(self, now: float) -> int:
        """Seconds until the next token is available."""
        if self.tokens >= 1.0:
            return 0
        deficit = 1.0 - self.tokens
        return int(deficit / self.refill_rate) + 1


class InMemoryRateLimiter:
    def __init__(self, limit: int = 60, window_seconds: int = 60):
        self.limit = limit
        self.window_seconds = window_seconds
        self._buckets: dict[str, _TokenBucket] = defaultdict(
            lambda: _TokenBucket(limit, limit / window_seconds)
        )
        self._lock = threading.Lock()

    def check(self, key: str) -> RateLimitInfo:
        with self._lock:
            now = time.monotonic()
            bucket = self._buckets[key]

            if not bucket.consume(now):
                retry = bucket.retry_after(now)
                raise RateLimitExceeded(
                    f"Rate limit exceeded: max {self.limit} requests per {self.window_seconds} seconds.",
                    retry_after=retry,
                )

            remaining = int(bucket.tokens)
            return RateLimitInfo(
                limit=self.limit,
                remaining=remaining,
                reset_seconds=self.window_seconds,
            )
