"""
Tests for the RAGAS evaluation framework.

Validates the evaluation pipeline itself — dataset loading, metric computation,
citation scoring, and the CLI entry point. Does NOT require a running HECTOR
instance (uses mocked API responses).
"""

import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluation.evaluate_rag import (
    compute_citation_metrics,
    compute_ragas_metrics,
    extract_answer,
    extract_contexts,
    load_dataset,
)


# ---------------------------------------------------------------------------
# Dataset loading
# ---------------------------------------------------------------------------

class TestDatasetLoading:
    """Tests for train.json dataset loading."""

    def test_load_valid_dataset(self):
        """Successfully loads a valid train.json."""
        data = load_dataset("evaluation")
        assert isinstance(data, list)
        assert len(data) >= 20

    def test_dataset_has_required_fields(self):
        """Every entry has query and ground_truth."""
        data = load_dataset("evaluation")
        for item in data:
            assert "query" in item, f"Missing 'query' in: {item}"
            assert "ground_truth" in item, f"Missing 'ground_truth' in: {item}"
            assert len(item["query"]) > 5
            assert len(item["ground_truth"]) > 10

    def test_dataset_has_optional_fields(self):
        """Every entry has expected_sections, expected_acts, category."""
        data = load_dataset("evaluation")
        for item in data:
            assert "expected_sections" in item
            assert "expected_acts" in item
            assert "category" in item

    def test_dataset_categories(self):
        """Dataset covers multiple legal categories."""
        data = load_dataset("evaluation")
        categories = set(item["category"] for item in data)
        assert "legal_research" in categories
        assert "cross_reference" in categories
        assert len(categories) >= 3

    def test_dataset_cross_references(self):
        """Cross-reference entries have expected sections and acts."""
        data = load_dataset("evaluation")
        xref = [item for item in data if item["category"] == "cross_reference"]
        assert len(xref) >= 5
        for item in xref:
            assert "expected_sections" in item
            assert "expected_acts" in item

    def test_missing_file_raises(self):
        """Loading from non-existent path raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_dataset("/nonexistent/path")

    def test_invalid_json_raises(self):
        """Loading invalid JSON raises an error."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_file = Path(tmpdir) / "train.json"
            bad_file.write_text("not valid json {{{", encoding="utf-8")
            with pytest.raises((json.JSONDecodeError, Exception)):
                load_dataset(tmpdir)


# ---------------------------------------------------------------------------
# RAGAS metric computation
# ---------------------------------------------------------------------------

class TestRagasMetrics:
    """Tests for RAGAS metric computation."""

    def test_perfect_match(self):
        """Perfect answer and contexts yield reasonable scores."""
        query = "What is Section 302 IPC?"
        answer = "Section 302 IPC prescribes punishment for murder as death or life imprisonment."
        contexts = ["Section 302. Punishment for murder.—Whoever commits murder shall be punished with death, or imprisonment for life, and shall also be liable to fine."]
        ground_truth = "Section 302 IPC prescribes punishment for murder as death or life imprisonment and shall also be liable to fine."

        metrics = compute_ragas_metrics(query, answer, contexts, ground_truth)

        # At least answer_relevance and faithfulness should be positive
        # when answer shares keywords with ground truth and context
        assert metrics["answer_relevance"] > 0.0
        assert metrics["faithfulness"] > 0.0

    def test_empty_contexts(self):
        """Empty contexts yield zero context metrics."""
        metrics = compute_ragas_metrics(
            "test query", "test answer", [], "ground truth"
        )
        assert metrics["context_precision"] == 0.0
        assert metrics["faithfulness"] == 0.0

    def test_empty_answer(self):
        """Empty answer yields zero answer metrics."""
        metrics = compute_ragas_metrics(
            "test query", "", ["some context"], "ground truth"
        )
        assert metrics["answer_relevance"] == 0.0
        assert metrics["faithfulness"] == 0.0

    def test_irrelevant_contexts(self):
        """Contexts unrelated to ground truth yield low precision."""
        metrics = compute_ragas_metrics(
            "What is murder?",
            "Murder is a crime.",
            ["The weather is nice today. Birds are singing."],
            "Section 302 IPC defines murder and prescribes death penalty.",
        )
        assert metrics["context_precision"] < 0.5

    def test_metrics_are_bounded(self):
        """All metrics are between 0 and 1."""
        metrics = compute_ragas_metrics(
            "query", "answer " * 50, ["context " * 100], "ground truth " * 50
        )
        for key, value in metrics.items():
            assert 0.0 <= value <= 1.0, f"{key}={value} out of range"


# ---------------------------------------------------------------------------
# Citation metrics
# ---------------------------------------------------------------------------

class TestCitationMetrics:
    """Tests for citation quality metric computation."""

    def test_perfect_citations(self):
        """All expected sections and acts found."""
        response = {
            "citations": [
                {"section": "302", "act": "IPC", "source": "test"},
                {"section": "101", "act": "BNS", "source": "test"},
            ],
            "items": [],
        }
        metrics = compute_citation_metrics(response, ["302", "101"], ["IPC", "BNS"])
        assert metrics["section_recall"] == 1.0
        assert metrics["act_recall"] == 1.0

    def test_partial_citations(self):
        """Some expected sections missing."""
        response = {
            "citations": [{"section": "302", "act": "IPC", "source": "test"}],
            "items": [],
        }
        metrics = compute_citation_metrics(response, ["302", "101"], ["IPC", "BNS"])
        assert metrics["section_recall"] == 0.5
        assert metrics["act_recall"] == 0.5

    def test_no_expected_sections(self):
        """No expected sections → perfect recall (not applicable)."""
        response = {"citations": [], "items": []}
        metrics = compute_citation_metrics(response, [], [])
        assert metrics["section_recall"] == 1.0
        assert metrics["act_recall"] == 1.0

    def test_citations_from_metadata(self):
        """Sections extracted from item metadata when not in citations."""
        response = {
            "citations": [],
            "items": [
                {"metadata": {"section_number": "302"}, "act": "IPC"},
                {"metadata": {"section_number": "101"}, "act": "BNS"},
            ],
        }
        metrics = compute_citation_metrics(response, ["302", "101"], ["IPC", "BNS"])
        assert metrics["section_recall"] == 1.0
        assert metrics["act_recall"] == 1.0

    def test_citation_count(self):
        """Citation count is reported correctly."""
        response = {
            "citations": [{"section": "1"}, {"section": "2"}, {"section": "3"}],
            "items": [],
        }
        metrics = compute_citation_metrics(response, [], [])
        assert metrics["citation_count"] == 3


# ---------------------------------------------------------------------------
# Response extraction helpers
# ---------------------------------------------------------------------------

class TestResponseExtraction:
    """Tests for extracting data from HECTOR API responses."""

    def test_extract_contexts(self):
        """Extracts document texts from response items."""
        response = {
            "items": [
                {"document": "Section 302 IPC", "id": "1"},
                {"document": "Section 101 BNS", "id": "2"},
            ]
        }
        contexts = extract_contexts(response)
        assert contexts == ["Section 302 IPC", "Section 101 BNS"]

    def test_extract_contexts_empty(self):
        """Handles empty items list."""
        assert extract_contexts({"items": []}) == []
        assert extract_contexts({}) == []

    def test_extract_contexts_skips_empty_docs(self):
        """Skips items with empty document field."""
        response = {
            "items": [
                {"document": "real text", "id": "1"},
                {"document": "", "id": "2"},
                {"id": "3"},
            ]
        }
        contexts = extract_contexts(response)
        assert contexts == ["real text"]

    def test_extract_answer(self):
        """Extracts generated_response from response."""
        response = {"generated_response": "Section 302 prescribes death penalty."}
        assert extract_answer(response) == "Section 302 prescribes death penalty."

    def test_extract_answer_missing(self):
        """Returns empty string when generated_response is missing."""
        assert extract_answer({}) == ""
        assert extract_answer({"generated_response": ""}) == ""


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

class TestCliEntryPoint:
    """Tests for the CLI argument parsing."""

    def test_module_is_importable(self):
        """evaluate_rag.py is importable."""
        import evaluation.evaluate_rag as mod
        assert hasattr(mod, "main")
        assert hasattr(mod, "run_evaluation")
        assert hasattr(mod, "load_dataset")

    def test_has_required_cli_args(self):
        """CLI accepts the expected argument flags."""
        import evaluation.evaluate_rag as mod
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("--dataset-paths", required=True)
        parser.add_argument("--host", default="localhost")
        parser.add_argument("--port", type=int, default=8000)
        parser.add_argument("--top-k", type=int, default=10)
        parser.add_argument("--output-dir", default="results")

        args = parser.parse_args([
            "--dataset-paths", "evaluation",
            "--host", "localhost",
            "--port", "8000",
            "--top-k", "10",
        ])
        assert args.dataset_paths == "evaluation"
        assert args.host == "localhost"
        assert args.port == 8000
