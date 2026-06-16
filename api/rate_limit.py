import threading
import time
from collections import defaultdict, deque
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


class InMemoryRateLimiter:
    def __init__(self, limit: int = 60, window_seconds: int = 60):
        self.limit = limit
        self.window_seconds = window_seconds
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str) -> RateLimitInfo:
        with self._lock:
            now = time.time()
            bucket = self._events[key]

            while bucket and bucket[0] <= now - self.window_seconds:
                bucket.popleft()

            current = len(bucket)
            remaining = max(0, self.limit - current)

            if current >= self.limit:
                oldest = bucket[0] if bucket else now
                retry_after = int(self.window_seconds - (now - oldest)) + 1
                raise RateLimitExceeded(
                    f"Rate limit exceeded: max {self.limit} requests per {self.window_seconds} seconds.",
                    retry_after=retry_after,
                )

            bucket.append(now)
            return RateLimitInfo(
                limit=self.limit,
                remaining=remaining,
                reset_seconds=self.window_seconds,
            )
