"""
Tests for the enhanced ingestor: validation, chunking, stats, and constants.
Uses mocking to avoid chromadb dependency.
"""

import os
import sys
from unittest.mock import MagicMock, patch

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
        f.write_bytes(
            b"NOT_PDF_CONTENT_HERE-padding-padding-pad-padding-padding-padding-padding-padding-padding-padding-padding-padding"
        )
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


class TestProcessTxtBook:
    """Tests for the OCR .txt file ingestion path."""

    def test_process_txt_book_basic(self, tmp_path):
        """A non-empty .txt file is chunked and added to ChromaDB."""
        txt = tmp_path / "Test_Act.txt"
        txt.write_text("Section 1. Definitions.\n" * 50, encoding="utf-8")

        ingestor = _make_ingestor()

        mock_col = MagicMock()
        mock_col.get.return_value = {"ids": []}
        mock_col.add.return_value = None
        ingestor.collection = mock_col
        ingestor._completed_books = set()

        result = ingestor.process_txt_book("Test_Act.txt", str(txt))

        assert result["status"] == "completed"
        assert result["pages"] == 1
        assert result["chunks"] > 0
        mock_col.add.assert_called_once()

    def test_process_txt_book_skips_empty(self, tmp_path):
        """An empty .txt file is reported as empty."""
        txt = tmp_path / "Empty.txt"
        txt.write_text("", encoding="utf-8")

        ingestor = _make_ingestor()
        result = ingestor.process_txt_book("Empty.txt", str(txt))

        assert result["status"] == "empty"
        assert result["chunks"] == 0

    def test_process_txt_book_skips_short(self, tmp_path):
        """A .txt file with < 20 chars is reported as empty."""
        txt = tmp_path / "Short.txt"
        txt.write_text("Hello", encoding="utf-8")

        ingestor = _make_ingestor()
        result = ingestor.process_txt_book("Short.txt", str(txt))

        assert result["status"] == "empty"

    def test_process_txt_book_uses_pdf_metadata_name(self, tmp_path):
        """Chunks created from .txt use .pdf extension in metadata."""
        txt = tmp_path / "Family_Courts_Act.txt"
        txt.write_text("Section 1. Application.\n" * 50, encoding="utf-8")

        ingestor = _make_ingestor()

        mock_col = MagicMock()
        mock_col.get.return_value = {"ids": []}
        ingestor.collection = mock_col
        ingestor._completed_books = set()

        ingestor.process_txt_book("Family_Courts_Act.txt", str(txt))

        call_kwargs = mock_col.add.call_args
        metadatas = call_kwargs[1]["metadatas"]
        for m in metadatas:
            assert m["source"] == "Family_Courts_Act.pdf"

    def test_process_txt_book_already_ingested(self, tmp_path):
        """Skips a .txt book that is in the completed set."""
        txt = tmp_path / "Already_Done.txt"
        txt.write_text("Section 1.\n" * 50, encoding="utf-8")

        ingestor = _make_ingestor()
        ingestor.reindex_mode = False
        ingestor._completed_books = {"Already_Done.txt"}

        result = ingestor.process_txt_book("Already_Done.txt", str(txt))
        assert result["status"] == "skipped"

    def test_process_txt_book_chroma_already_has_hash(self, tmp_path):
        """Skips when ChromaDB already has the page hash."""
        txt = tmp_path / "Duplicate.txt"
        txt.write_text("Section 1. Application of Act.\n" * 50, encoding="utf-8")

        ingestor = _make_ingestor()
        ingestor.reindex_mode = False
        ingestor._completed_books = set()

        mock_col = MagicMock()
        mock_col.get.return_value = {"ids": ["existing-id"]}
        ingestor.collection = mock_col

        result = ingestor.process_txt_book("Duplicate.txt", str(txt))
        assert result["status"] == "skipped"
        mock_col.add.assert_not_called()

    def test_process_txt_book_handles_read_error(self, tmp_path):
        """Reports error when file cannot be read."""
        ingestor = _make_ingestor()
        result = ingestor.process_txt_book("Missing.txt", str(tmp_path / "Missing.txt"))
        assert result["status"] == "error"


class TestNvidiaOcrFallback:
    """Tests for the NVIDIA OCR fallback method."""

    def test_no_api_key_returns_empty(self):
        """Returns empty string when NVIDIA_API_KEY is not set."""
        ingestor = _make_ingestor()
        env = {k: v for k, v in os.environ.items() if k != "NVIDIA_API_KEY"}
        with patch.dict(os.environ, env, clear=True):
            result = ingestor._nvidia_ocr_fallback("dummy.pdf", 1)
            assert result == ""

    def test_exception_caught_returns_empty(self):
        """Returns empty string when internal error occurs (missing pdf2image)."""
        ingestor = _make_ingestor()
        with patch.dict(os.environ, {"NVIDIA_API_KEY": "test-key"}):
            result = ingestor._nvidia_ocr_fallback("dummy.pdf", 1)
        assert result == ""

    def test_method_exists(self):
        """Verify _nvidia_ocr_fallback method is present."""
        ingestor = _make_ingestor()
        assert hasattr(ingestor, "_nvidia_ocr_fallback")
        assert callable(ingestor._nvidia_ocr_fallback)
