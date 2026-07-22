"""
Persistent Query Cache — SQLite-backed with TTL and LRU eviction.

Stores serialized query responses on disk so cached results survive
server restarts. Tracks hit/miss stats and supports manual invalidation.
"""

import hashlib
import json
import logging
import os
import sqlite3
import threading
import time
from typing import Any

logger = logging.getLogger(__name__)

_DEFAULT_DB_PATH = os.getenv(
    "HECTOR_CACHE_DB", os.path.join(os.path.dirname(__file__), "..", "data", "query_cache.db")
)
_DEFAULT_TTL_SECONDS = 86400  # 24 hours
_DEFAULT_MAX_ENTRIES = 5000


class QueryCache:
    """Thread-safe persistent query cache backed by SQLite."""

    def __init__(
        self,
        db_path: str | None = None,
        ttl_seconds: int = _DEFAULT_TTL_SECONDS,
        max_entries: int = _DEFAULT_MAX_ENTRIES,
    ):
        self.db_path = db_path or _DEFAULT_DB_PATH
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self._lock = threading.Lock()
        self._local = threading.local()
        self._ensure_db()

    # ------------------------------------------------------------------
    # Connection helpers (per-thread for SQLite thread safety)
    # ------------------------------------------------------------------

    def _get_conn(self) -> sqlite3.Connection:
        conn = getattr(self._local, "conn", None)
        if conn is None:
            conn = sqlite3.connect(self.db_path, timeout=5)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            self._local.conn = conn
        return conn

    def _ensure_db(self):
        conn = self._get_conn()
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS query_cache (
                cache_key   TEXT PRIMARY KEY,
                response    TEXT NOT NULL,
                timing      TEXT,
                query_text  TEXT,
                route       TEXT,
                created_at  REAL NOT NULL,
                expires_at  REAL NOT NULL,
                hit_count   INTEGER DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_expires ON query_cache(expires_at);
            CREATE INDEX IF NOT EXISTS idx_created ON query_cache(created_at);

            CREATE TABLE IF NOT EXISTS cache_stats (
                id          INTEGER PRIMARY KEY CHECK (id = 1),
                hits        INTEGER DEFAULT 0,
                misses      INTEGER DEFAULT 0,
                evictions   INTEGER DEFAULT 0,
                last_reset  REAL
            );
            """
        )
        conn.commit()

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    @staticmethod
    def _make_key(query: str) -> str:
        normalised = query.strip().lower()
        return hashlib.sha256(normalised.encode("utf-8")).hexdigest()[:32]

    def get(self, query: str) -> dict[str, Any] | None:
        key = self._make_key(query)
        with self._lock:
            conn = self._get_conn()
            row = conn.execute(
                "SELECT response, timing, expires_at FROM query_cache WHERE cache_key = ?",
                (key,),
            ).fetchone()

            if row is None:
                self._increment_stat("misses")
                return None

            response_text, timing_text, expires_at = row
            if expires_at < time.time():
                conn.execute("DELETE FROM query_cache WHERE cache_key = ?", (key,))
                conn.commit()
                self._increment_stat("misses")
                return None

            conn.execute(
                "UPDATE query_cache SET hit_count = hit_count + 1 WHERE cache_key = ?",
                (key,),
            )
            conn.commit()
            self._increment_stat("hits")
            return {
                "response": response_text,
                "timing": json.loads(timing_text) if timing_text else {},
            }

    def set(
        self,
        query: str,
        response: str,
        timing: dict | None = None,
        route: str | None = None,
        ttl_override: int | None = None,
    ):
        key = self._make_key(query)
        now = time.time()
        ttl = ttl_override if ttl_override is not None else self.ttl_seconds
        expires = now + ttl

        with self._lock:
            conn = self._get_conn()
            conn.execute(
                """
                INSERT OR REPLACE INTO query_cache
                    (cache_key, response, timing, query_text, route, created_at, expires_at, hit_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0)
                """,
                (
                    key,
                    response,
                    json.dumps(timing) if timing else None,
                    query,
                    route,
                    now,
                    expires,
                ),
            )
            self._evict_if_needed(conn)
            conn.commit()

    def invalidate(self, query: str) -> bool:
        key = self._make_key(query)
        with self._lock:
            conn = self._get_conn()
            cursor = conn.execute(
                "DELETE FROM query_cache WHERE cache_key = ?", (key,)
            )
            conn.commit()
            return cursor.rowcount > 0

    def clear(self) -> int:
        with self._lock:
            conn = self._get_conn()
            cursor = conn.execute("DELETE FROM query_cache")
            conn.commit()
            return cursor.rowcount

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def stats(self) -> dict[str, Any]:
        with self._lock:
            conn = self._get_conn()
            total_entries = conn.execute(
                "SELECT COUNT(*) FROM query_cache"
            ).fetchone()[0]
            active_entries = conn.execute(
                "SELECT COUNT(*) FROM query_cache WHERE expires_at > ?",
                (time.time(),),
            ).fetchone()[0]
            expired_entries = total_entries - active_entries

            row = conn.execute(
                "SELECT hits, misses, evictions FROM cache_stats WHERE id = 1"
            ).fetchone()
            hits = row[0] if row else 0
            misses = row[1] if row else 0
            evictions = row[2] if row else 0

            total_requests = hits + misses
            hit_rate = (hits / total_requests * 100) if total_requests > 0 else 0.0

            popular = conn.execute(
                "SELECT query_text, hit_count FROM query_cache ORDER BY hit_count DESC LIMIT 5"
            ).fetchall()

            return {
                "total_entries": total_entries,
                "active_entries": active_entries,
                "expired_entries": expired_entries,
                "max_entries": self.max_entries,
                "hits": hits,
                "misses": misses,
                "total_requests": total_requests,
                "hit_rate_percent": round(hit_rate, 1),
                "evictions": evictions,
                "ttl_seconds": self.ttl_seconds,
                "db_path": self.db_path,
                "popular_queries": [
                    {"query": q, "hits": h} for q, h in popular if q
                ],
            }

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _increment_stat(self, field: str):
        conn = self._get_conn()
        conn.execute(
            """
            INSERT INTO cache_stats (id, hits, misses, evictions, last_reset)
            VALUES (1, 0, 0, 0, ?)
            ON CONFLICT(id) DO UPDATE SET {field} = {field} + 1
            """.format(field=field),
            (time.time(),),
        )
        conn.commit()

    def _evict_if_needed(self, conn: sqlite3.Connection):
        count = conn.execute("SELECT COUNT(*) FROM query_cache").fetchone()[0]
        if count <= self.max_entries:
            return
        to_remove = count - self.max_entries
        conn.execute(
            "DELETE FROM query_cache WHERE cache_key IN "
            "(SELECT cache_key FROM query_cache ORDER BY hit_count ASC, created_at ASC LIMIT ?)",
            (to_remove,),
        )
        self._increment_stat("evictions")


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_instance: QueryCache | None = None
_instance_lock = threading.Lock()


def get_query_cache(**kwargs) -> QueryCache:
    global _instance
    if _instance is None:
        with _instance_lock:
            if _instance is None:
                _instance = QueryCache(**kwargs)
    return _instance
