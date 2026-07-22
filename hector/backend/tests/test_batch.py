"""Tests for the batch query processor module."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "api"))

from core.batch import BatchQueryProcessor, BatchJob


@pytest.fixture
def processor():
    return BatchQueryProcessor()


class TestBatchQueryProcessor:
    def test_parse_csv(self, processor):
        text = "query one\nquery two\nquery three"
        queries = processor.parse_csv(text)
        assert queries == ["query one", "query two", "query three"]

    def test_parse_csv_with_quotes(self, processor):
        text = '"quoted query"\n\'single quoted\''
        queries = processor.parse_csv(text)
        assert queries == ["quoted query", "single quoted"]

    def test_parse_csv_skips_comments(self, processor):
        text = "# comment\nactual query\n# another comment"
        queries = processor.parse_csv(text)
        assert queries == ["actual query"]

    def test_parse_csv_skips_empty_lines(self, processor):
        text = "query one\n\n\nquery two\n"
        queries = processor.parse_csv(text)
        assert queries == ["query one", "query two"]

    def test_parse_text(self, processor):
        text = "line one\nline two"
        queries = processor.parse_text(text)
        assert queries == ["line one", "line two"]

    def test_empty_input(self, processor):
        assert processor.parse_csv("") == []
        assert processor.parse_text("") == []

    def test_to_export_data(self, processor):
        job = BatchJob(
            job_id="test-123",
            queries=["q1", "q2"],
            total=2,
            status="completed",
            started_at=1000,
            completed_at=1002,
            completed_count=2,
            failed_count=0,
        )
        from core.batch import BatchQueryResult
        job.results = [
            BatchQueryResult(index=0, query="q1", route="LEGAL_RESEARCH", confidence=85, response_ms=500),
            BatchQueryResult(index=1, query="q2", route="GENERAL", error="timeout"),
        ]
        data = processor.to_export_data(job)
        assert data["job_id"] == "test-123"
        assert data["total"] == 2
        assert data["completed"] == 2
        assert len(data["results"]) == 2
        assert data["results"][0]["route"] == "LEGAL_RESEARCH"
        assert data["results"][1]["error"] == "timeout"
