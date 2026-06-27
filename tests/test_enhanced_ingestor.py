"""
Tests for the enhanced ingestor: validation, chunking, stats, and constants.
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


class TestValidatePdf:
    """Tests for validate_pdf method."""

    def test_nonexistent_file(self):
        ingestor = _make_ingestor()
        is_valid, error = ingestor.validate_pdf("/nonexistent/file.pdf", "missing.pdf")
        assert is_valid is False
        assert "not found" in error.lower()

    def test_empty_file(self, tmp_path):
        ingestor = _make_ingestor()
        f = tmp_path / "empty.pdf"
        f.write_bytes(b"")
        is_valid, error = ingestor.validate_pdf(str(f), "empty.pdf")
        assert is_valid is False
        assert "empty" in error.lower()

    def test_too_small_file(self, tmp_path):
        ingestor = _make_ingestor()
        f = tmp_path / "small.pdf"
        f.write_bytes(b"abc")
        is_valid, error = ingestor.validate_pdf(str(f), "small.pdf")
        assert is_valid is False
        assert "too small" in error.lower()

    def test_invalid_header(self, tmp_path):
        ingestor = _make_ingestor()
        f = tmp_path / "invalid.pdf"
        # Must be >100 bytes to pass size check, but not start with %PDF
        f.write_bytes(b"NOT_PDF_CONTENT_HERE-padding-padding-pad-padding-padding-padding-padding-padding-padding-padding-padding-padding")
        is_valid, error = ingestor.validate_pdf(str(f), "invalid.pdf")
        assert is_valid is False
        assert "invalid pdf header" in error.lower()

    def test_valid_pdf(self, tmp_path):
        ingestor = _make_ingestor()
        pdf_content = (
            b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
            b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
            b"3 0 obj<</Type/Page/MediaBox[0 0 3 3]/Parent 2 0 R>>endobj\n"
            b"xref\n0 4\n"
            b"0000000000 65535 f \n0000000009 00000 n \n"
            b"0000000058 00000 n \n0000000115 00000 n \n"
            b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n190\n%%EOF"
        )
        f = tmp_path / "valid.pdf"
        f.write_bytes(pdf_content)
        is_valid, error = ingestor.validate_pdf(str(f), "valid.pdf")
        assert is_valid is True
        assert error == ""


class TestChunkText:
    """Tests for chunk_text method (boundary-aware overlapping windows)."""

    def test_empty_text_returns_empty(self):
        ingestor = _make_ingestor()
        result = ingestor.chunk_text("")
        assert result == []

    def test_short_text_single_chunk(self):
        ingestor = _make_ingestor()
        text = "This is a short legal text."
        result = ingestor.chunk_text(text)
        assert len(result) == 1
        assert result[0] == text

    def test_long_text_multiple_chunks(self):
        ingestor = _make_ingestor()
        text = " ".join(["word"] * 1000)
        result = ingestor.chunk_text(text, chunk_size=100, overlap=20)
        assert len(result) > 1

    def test_all_words_covered(self):
        ingestor = _make_ingestor()
        words = [f"w{i}" for i in range(200)]
        text = " ".join(words)
        result = ingestor.chunk_text(text, chunk_size=50, overlap=10)
        # All original words should appear in at least one chunk
        all_chunk_words = " ".join(result).split()
        for w in words:
            assert w in all_chunk_words

    def test_chunks_are_nonempty(self):
        ingestor = _make_ingestor()
        text = " ".join(["word"] * 500)
        result = ingestor.chunk_text(text, chunk_size=100, overlap=20)
        for chunk in result:
            assert len(chunk.strip()) > 0

    def test_custom_small_chunk_size(self):
        ingestor = _make_ingestor()
        text = "one two three four five six seven eight nine ten"
        result = ingestor.chunk_text(text, chunk_size=3, overlap=1)
        assert len(result) >= 3

    def test_chunk_preserves_word_order(self):
        ingestor = _make_ingestor()
        text = "alpha beta gamma delta epsilon"
        result = ingestor.chunk_text(text, chunk_size=3, overlap=0)
        assert result[0] == "alpha beta gamma"


class TestStatsTracking:
    """Tests for ingestion statistics initialization."""

    def test_stats_initialization(self):
        ingestor = _make_ingestor()
        assert ingestor.stats["pages_processed"] == 0
        assert ingestor.stats["chunks_created"] == 0
        assert ingestor.stats["chunks_rejected"] == 0
        assert isinstance(ingestor.stats["acts_found"], list)
        assert len(ingestor.stats["acts_found"]) == 0
        assert ingestor.stats["sections_found"] == 0
        assert ingestor.stats["structure_types"] == {}

    def test_stats_acts_found_is_list(self):
        ingestor = _make_ingestor()
        assert isinstance(ingestor.stats["acts_found"], list)

    def test_stats_mutable(self):
        ingestor = _make_ingestor()
        ingestor.stats["acts_found"].append("IPC")
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
