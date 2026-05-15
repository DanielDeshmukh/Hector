import threading
import time
from collections import defaultdict, deque


class RateLimitExceeded(Exception):
    """Raised when a client crosses the configured request budget."""


class InMemoryRateLimiter:
    def __init__(self, limit: int = 60, window_seconds: int = 60):
        self.limit = limit
        self.window_seconds = window_seconds
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str):
        with self._lock:
            now = time.time()
            bucket = self._events[key]

            while bucket and bucket[0] <= now - self.window_seconds:
                bucket.popleft()

            if len(bucket) >= self.limit:
                raise RateLimitExceeded(
                    f"Rate limit exceeded: max {self.limit} requests per {self.window_seconds} seconds."
                )

            bucket.append(now)
