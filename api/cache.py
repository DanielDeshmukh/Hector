import threading
import time
from typing import Any


class TTLCache:
    """Small in-memory TTL cache with hit/miss metrics."""

    def __init__(self, ttl_seconds: int = 60, max_items: int = 256):
        self.ttl_seconds = ttl_seconds
        self.max_items = max_items
        self._data: dict[str, tuple[float, Any]] = {}
        self._lock = threading.Lock()
        # Metrics
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def get(self, key: str) -> Any | None:
        with self._lock:
            item = self._data.get(key)
            if item is None:
                self._misses += 1
                return None

            expires_at, value = item
            if expires_at < time.time():
                self._data.pop(key, None)
                self._misses += 1
                return None
            self._hits += 1
            return value

    def set(self, key: str, value: Any):
        with self._lock:
            self._prune_expired()
            if len(self._data) >= self.max_items:
                oldest_key = min(
                    self._data, key=lambda item_key: self._data[item_key][0]
                )
                self._data.pop(oldest_key, None)
                self._evictions += 1
            self._data[key] = (time.time() + self.ttl_seconds, value)

    def clear(self):
        with self._lock:
            self._data.clear()

    def get_metrics(self) -> dict[str, Any]:
        """Return cache performance metrics."""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total * 100) if total > 0 else 0.0
            return {
                "size": len(self._data),
                "max_size": self.max_items,
                "hits": self._hits,
                "misses": self._misses,
                "total_requests": total,
                "hit_rate_percent": round(hit_rate, 1),
                "evictions": self._evictions,
                "ttl_seconds": self.ttl_seconds,
            }

    def _prune_expired(self):
        now = time.time()
        expired = [
            key for key, (expires_at, _) in self._data.items() if expires_at < now
        ]
        for key in expired:
            self._data.pop(key, None)
