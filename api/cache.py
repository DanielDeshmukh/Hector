import threading
import time
from typing import Any


class TTLCache:
    """Small in-memory TTL cache for API responses."""

    def __init__(self, ttl_seconds: int = 60, max_items: int = 256):
        self.ttl_seconds = ttl_seconds
        self.max_items = max_items
        self._data: dict[str, tuple[float, Any]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Any | None:
        with self._lock:
            item = self._data.get(key)
            if item is None:
                return None

            expires_at, value = item
            if expires_at < time.time():
                self._data.pop(key, None)
                return None
            return value

    def set(self, key: str, value: Any):
        with self._lock:
            self._prune_expired()
            if len(self._data) >= self.max_items:
                oldest_key = min(self._data, key=lambda item_key: self._data[item_key][0])
                self._data.pop(oldest_key, None)
            self._data[key] = (time.time() + self.ttl_seconds, value)

    def clear(self):
        with self._lock:
            self._data.clear()

    def _prune_expired(self):
        now = time.time()
        expired = [key for key, (expires_at, _) in self._data.items() if expires_at < now]
        for key in expired:
            self._data.pop(key, None)
