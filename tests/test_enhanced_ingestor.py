"""
Tests for the enhanced ingestor: chunking, stats, and constants.
Uses mocking to avoid chromadb dependency.
"""

import os
import sys
import tempfile
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _make_ingestor():
    """Create EnhancedHectorIngestor with mocked chromadb."""
    with patch.dict("sys.modules", {"chromadb": MagicMock()}):
        from utils.enhanced_ingestor import EnhancedHectorIngestor

        return EnhancedHectorIngestor(reindex_mode=True)


class TestChunkText:
    """Tests for chunk_text method (sliding window tokenization)."""

    def test_empty_text_returns_empty(self):
        ingestor = _make_ingestor()
        result = ingestor.chunk_text("")
        assert result == []

    def test_short_text_single_chunk(self):
        ingestor = _make_ingestor()
        # Default chunk_size=800 tokens, so short text fits in one chunk
        text = "This is a short legal text."
        result = ingestor.chunk_text(text)
        assert len(result) == 1
        assert result[0] == text

    def test_long_text_multiple_chunks(self):
        ingestor = _make_ingestor()
        # Create text with >800 words to force multiple chunks
        text = " ".join(["word"] * 1000)
        result = ingestor.chunk_text(text, chunk_size=100, overlap=20)
        assert len(result) > 1

    def test_overlap_produces_repeated_tokens(self):
        ingestor = _make_ingestor()
        text = " ".join(["word"] * 200)
        result = ingestor.chunk_text(text, chunk_size=50, overlap=10)
        # With overlap, consecutive chunks share tokens
        assert len(result) > 1
        # Check overlap: last tokens of chunk[0] should appear in chunk[1]
        chunk0_words = result[0].split()
        chunk1_words = result[1].split()
        overlap_area = chunk0_words[-10:]
        assert any(w in chunk1_words for w in overlap_area)

    def test_step_calculation(self):
        ingestor = _make_ingestor()
        # step = max(chunk_size - overlap, 1)
        text = " ".join(["a"] * 100)
        result = ingestor.chunk_text(text, chunk_size=50, overlap=10)
        # step=40, so indices: 0,40,80 -> 3 chunks (last one shorter)
        assert len(result) == 3

    def test_custom_small_chunk_size(self):
        ingestor = _make_ingestor()
        text = "one two three four five six seven eight nine ten"
        result = ingestor.chunk_text(text, chunk_size=3, overlap=1)
        # step=2, indices: 0,2,4,6,8 -> 5 chunks
        assert len(result) == 5

    def test_chunk_preserves_word_order(self):
        ingestor = _make_ingestor()
        text = "alpha beta gamma delta epsilon"
        result = ingestor.chunk_text(text, chunk_size=3, overlap=0)
        # First chunk should be "alpha beta gamma"
        assert result[0] == "alpha beta gamma"


class TestStatsTracking:
    """Tests for ingestion statistics initialization."""

    def test_stats_initialization(self):
        ingestor = _make_ingestor()
        assert ingestor.stats["pages_processed"] == 0
        assert ingestor.stats["chunks_created"] == 0
        assert ingestor.stats["chunks_rejected"] == 0
        assert isinstance(ingestor.stats["acts_found"], set)
        assert len(ingestor.stats["acts_found"]) == 0
        assert ingestor.stats["sections_found"] == 0
        assert ingestor.stats["structure_types"] == {}

    def test_stats_acts_found_is_set(self):
        ingestor = _make_ingestor()
        assert isinstance(ingestor.stats["acts_found"], set)

    def test_stats_mutable(self):
        ingestor = _make_ingestor()
        ingestor.stats["acts_found"].add("IPC")
        ingestor.stats["pages_processed"] += 1
        assert "IPC" in ingestor.stats["acts_found"]
        assert ingestor.stats["pages_processed"] == 1


class TestConstants:
    """Tests for module-level constants (via mocked import)."""

    def test_constants_exist(self):
        with patch.dict("sys.modules", {"chromadb": MagicMock()}):
            import importlib
            mod = importlib.import_module("utils.enhanced_ingestor")
            assert hasattr(mod, "CHUNK_SIZE_TOKENS")
            assert hasattr(mod, "CHUNK_OVERLAP_TOKENS")
            assert hasattr(mod, "MIN_CHUNK_CHARS")

    def test_chunk_size_tokens_value(self):
        with patch.dict("sys.modules", {"chromadb": MagicMock()}):
            import importlib
            mod = importlib.import_module("utils.enhanced_ingestor")
            assert mod.CHUNK_SIZE_TOKENS == 800
            assert isinstance(mod.CHUNK_SIZE_TOKENS, int)

    def test_chunk_overlap_tokens_value(self):
        with patch.dict("sys.modules", {"chromadb": MagicMock()}):
            import importlib
            mod = importlib.import_module("utils.enhanced_ingestor")
            assert mod.CHUNK_OVERLAP_TOKENS == 150
            assert isinstance(mod.CHUNK_OVERLAP_TOKENS, int)

    def test_min_chunk_chars_value(self):
        with patch.dict("sys.modules", {"chromadb": MagicMock()}):
            import importlib
            mod = importlib.import_module("utils.enhanced_ingestor")
            assert mod.MIN_CHUNK_CHARS == 50
            assert isinstance(mod.MIN_CHUNK_CHARS, int)

    def test_overlap_less_than_chunk_size(self):
        with patch.dict("sys.modules", {"chromadb": MagicMock()}):
            import importlib
            mod = importlib.import_module("utils.enhanced_ingestor")
            assert mod.CHUNK_OVERLAP_TOKENS < mod.CHUNK_SIZE_TOKENS


class TestParserIntegration:
    """Tests that the legal structure parser is initialized."""

    def test_parser_initialized(self):
        ingestor = _make_ingestor()
        assert ingestor.parser is not None

    def test_enricher_initialized(self):
        ingestor = _make_ingestor()
        assert ingestor.enricher is not None
