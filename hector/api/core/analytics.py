"""
Search Analytics — tracks query patterns, response times, and usage metrics.

Stores analytics in SQLite for persistence across restarts. Provides
aggregated stats for the dashboard (popular queries, domain breakdown,
response time trends, etc.).
"""

import json
import logging
import os
import sqlite3
import threading
import time
from collections import defaultdict
from typing import Any

logger = logging.getLogger(__name__)

_DEFAULT_DB_PATH = os.getenv(
    "HECTOR_ANALYTICS_DB",
    os.path.join(os.path.dirname(__file__), "..", "data", "analytics.db"),
)


class SearchAnalytics:
    """Thread-safe search analytics tracker backed by SQLite."""

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or _DEFAULT_DB_PATH
        self._lock = threading.Lock()
        self._local = threading.local()
        self._ensure_db()

    # ------------------------------------------------------------------
    # Connection helpers
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
            CREATE TABLE IF NOT EXISTS search_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                query       TEXT NOT NULL,
                route       TEXT,
                confidence  REAL,
                result_count INTEGER,
                response_ms REAL,
                cache_hit   INTEGER DEFAULT 0,
                created_at  REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_log_created ON search_log(created_at);
            CREATE INDEX IF NOT EXISTS idx_log_route ON search_log(route);

            CREATE TABLE IF NOT EXISTS query_patterns (
                query_text  TEXT PRIMARY KEY,
                count       INTEGER DEFAULT 1,
                avg_ms      REAL,
                last_seen   REAL
            );
            """
        )
        conn.commit()

    # ------------------------------------------------------------------
    # Recording
    # ------------------------------------------------------------------

    def record_search(
        self,
        query: str,
        route: str | None = None,
        confidence: float | None = None,
        result_count: int | None = None,
        response_ms: float | None = None,
        cache_hit: bool = False,
    ):
        now = time.time()
        with self._lock:
            conn = self._get_conn()
            conn.execute(
                """
                INSERT INTO search_log (query, route, confidence, result_count, response_ms, cache_hit, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (query, route, confidence, result_count, response_ms, int(cache_hit), now),
            )

            # Update query patterns
            conn.execute(
                """
                INSERT INTO query_patterns (query_text, count, avg_ms, last_seen)
                VALUES (?, 1, ?, ?)
                ON CONFLICT(query_text) DO UPDATE SET
                    count = count + 1,
                    avg_ms = (avg_ms * count + ?) / (count + 1),
                    last_seen = ?
                """,
                (query, response_ms, now, response_ms, now),
            )
            conn.commit()

    # ------------------------------------------------------------------
    # Analytics queries
    # ------------------------------------------------------------------

    def get_overview(self, days: int = 30) -> dict[str, Any]:
        with self._lock:
            conn = self._get_conn()
            cutoff = time.time() - (days * 86400)

            total = conn.execute(
                "SELECT COUNT(*) FROM search_log WHERE created_at > ?", (cutoff,)
            ).fetchone()[0]

            avg_ms = conn.execute(
                "SELECT AVG(response_ms) FROM search_log WHERE created_at > ? AND response_ms IS NOT NULL",
                (cutoff,),
            ).fetchone()[0]

            cache_hits = conn.execute(
                "SELECT COUNT(*) FROM search_log WHERE created_at > ? AND cache_hit = 1",
                (cutoff,),
            ).fetchone()[0]

            return {
                "total_queries": total,
                "avg_response_ms": round(avg_ms, 1) if avg_ms else 0,
                "cache_hit_rate": round(cache_hits / total * 100, 1) if total > 0 else 0,
                "period_days": days,
            }

    def get_popular_queries(self, limit: int = 10, days: int = 30) -> list[dict]:
        with self._lock:
            conn = self._get_conn()
            cutoff = time.time() - (days * 86400)
            rows = conn.execute(
                """
                SELECT query_text, count, avg_ms, last_seen
                FROM query_patterns
                WHERE last_seen > ?
                ORDER BY count DESC
                LIMIT ?
                """,
                (cutoff, limit),
            ).fetchall()
            return [
                {"query": r[0], "count": r[1], "avg_ms": round(r[2], 1) if r[2] else 0}
                for r in rows
            ]

    def get_domain_breakdown(self, days: int = 30) -> list[dict]:
        with self._lock:
            conn = self._get_conn()
            cutoff = time.time() - (days * 86400)
            rows = conn.execute(
                """
                SELECT route, COUNT(*) as cnt
                FROM search_log
                WHERE created_at > ? AND route IS NOT NULL
                GROUP BY route
                ORDER BY cnt DESC
                """,
                (cutoff,),
            ).fetchall()
            total = sum(r[1] for r in rows) or 1
            return [
                {"route": r[0], "count": r[1], "percent": round(r[1] / total * 100, 1)}
                for r in rows
            ]

    def get_hourly_distribution(self, days: int = 7) -> list[dict]:
        with self._lock:
            conn = self._get_conn()
            cutoff = time.time() - (days * 86400)
            rows = conn.execute(
                """
                SELECT CAST(created_at AS INTEGER) / 3600 as hour_bucket, COUNT(*) as cnt
                FROM search_log
                WHERE created_at > ?
                GROUP BY hour_bucket
                ORDER BY hour_bucket
                """,
                (cutoff,),
            ).fetchall()
            return [{"hour": r[0], "count": r[1]} for r in rows]

    def get_confidence_distribution(self, days: int = 30) -> dict[str, int]:
        with self._lock:
            conn = self._get_conn()
            cutoff = time.time() - (days * 86400)
            rows = conn.execute(
                """
                SELECT
                    CASE
                        WHEN confidence >= 75 THEN 'high'
                        WHEN confidence >= 50 THEN 'medium'
                        WHEN confidence >= 25 THEN 'low'
                        ELSE 'very_low'
                    END as level,
                    COUNT(*) as cnt
                FROM search_log
                WHERE created_at > ? AND confidence IS NOT NULL
                GROUP BY level
                """,
                (cutoff,),
            ).fetchall()
            return {r[0]: r[1] for r in rows}

    def get_response_time_trend(self, days: int = 7, bucket_hours: int = 6) -> list[dict]:
        with self._lock:
            conn = self._get_conn()
            cutoff = time.time() - (days * 86400)
            bucket_size = bucket_hours * 3600
            rows = conn.execute(
                """
                SELECT
                    (CAST(created_at AS INTEGER) / ?) * ? as bucket,
                    AVG(response_ms) as avg_ms,
                    COUNT(*) as cnt
                FROM search_log
                WHERE created_at > ? AND response_ms IS NOT NULL
                GROUP BY bucket
                ORDER BY bucket
                """,
                (bucket_size, bucket_size, cutoff),
            ).fetchall()
            return [
                {"timestamp": r[0], "avg_ms": round(r[1], 1), "count": r[2]}
                for r in rows
            ]

    def get_recent_queries(self, limit: int = 20) -> list[dict]:
        with self._lock:
            conn = self._get_conn()
            rows = conn.execute(
                """
                SELECT query, route, confidence, result_count, response_ms, cache_hit, created_at
                FROM search_log
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return [
                {
                    "query": r[0],
                    "route": r[1],
                    "confidence": r[2],
                    "result_count": r[3],
                    "response_ms": round(r[4], 1) if r[4] else None,
                    "cache_hit": bool(r[5]),
                    "timestamp": r[6],
                }
                for r in rows
            ]


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_instance: SearchAnalytics | None = None
_instance_lock = threading.Lock()


def get_analytics(**kwargs) -> SearchAnalytics:
    global _instance
    if _instance is None:
        with _instance_lock:
            if _instance is None:
                _instance = SearchAnalytics(**kwargs)
    return _instance
