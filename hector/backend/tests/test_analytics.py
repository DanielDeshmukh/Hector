"""Tests for the search analytics module."""

import os
import sys
import time

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "api"))

from core.analytics import SearchAnalytics


@pytest.fixture
def analytics(tmp_path):
    db_path = str(tmp_path / "test_analytics.db")
    return SearchAnalytics(db_path=db_path)


class TestSearchAnalytics:
    def test_record_and_overview(self, analytics):
        analytics.record_search("what is murder?", route="LEGAL_RESEARCH", confidence=85, result_count=5, response_ms=1200)
        overview = analytics.get_overview(days=1)
        assert overview["total_queries"] == 1
        assert overview["avg_response_ms"] == 1200.0

    def test_multiple_queries(self, analytics):
        for i in range(5):
            analytics.record_search(f"query {i}", route="LEGAL_RESEARCH", response_ms=100 * i)
        overview = analytics.get_overview(days=1)
        assert overview["total_queries"] == 5

    def test_cache_hit_tracking(self, analytics):
        analytics.record_search("cached query", cache_hit=True, response_ms=0)
        analytics.record_search("fresh query", cache_hit=False, response_ms=500)
        overview = analytics.get_overview(days=1)
        assert overview["total_queries"] == 2
        assert overview["cache_hit_rate"] == 50.0

    def test_popular_queries(self, analytics):
        for _ in range(3):
            analytics.record_search("popular query")
        analytics.record_search("rare query")
        popular = analytics.get_popular_queries(limit=5, days=1)
        assert len(popular) == 2
        assert popular[0]["query"] == "popular query"
        assert popular[0]["count"] == 3

    def test_domain_breakdown(self, analytics):
        analytics.record_search("q1", route="LEGAL_RESEARCH")
        analytics.record_search("q2", route="LEGAL_RESEARCH")
        analytics.record_search("q3", route="GENERAL")
        domains = analytics.get_domain_breakdown(days=1)
        assert len(domains) == 2
        lr = next(d for d in domains if d["route"] == "LEGAL_RESEARCH")
        assert lr["count"] == 2

    def test_confidence_distribution(self, analytics):
        analytics.record_search("q1", confidence=85)
        analytics.record_search("q2", confidence=60)
        analytics.record_search("q3", confidence=30)
        conf = analytics.get_confidence_distribution(days=1)
        assert conf.get("high", 0) == 1
        assert conf.get("medium", 0) == 1
        assert conf.get("low", 0) == 1

    def test_recent_queries(self, analytics):
        analytics.record_search("latest query", route="LEGAL_RESEARCH", confidence=90, response_ms=800)
        recent = analytics.get_recent_queries(limit=5)
        assert len(recent) == 1
        assert recent[0]["query"] == "latest query"
        assert recent[0]["route"] == "LEGAL_RESEARCH"

    def test_empty_analytics(self, analytics):
        overview = analytics.get_overview(days=1)
        assert overview["total_queries"] == 0
        assert overview["cache_hit_rate"] == 0
        assert analytics.get_popular_queries() == []
        assert analytics.get_domain_breakdown() == []
        assert analytics.get_recent_queries() == []

    def test_query_patterns_update(self, analytics):
        analytics.record_search("same query", response_ms=100)
        analytics.record_search("same query", response_ms=200)
        popular = analytics.get_popular_queries(limit=5, days=1)
        assert popular[0]["count"] == 2
        assert popular[0]["avg_ms"] == 150.0
