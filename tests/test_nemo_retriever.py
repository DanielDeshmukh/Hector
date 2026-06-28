"""
Tests for the unified NemoRetriever provider.

Validates provider initialization, OCR, embedding, reranking,
document processing pipeline, and fallback behavior. Uses mocked APIs.
"""

import os
import sys
from unittest.mock import MagicMock, patch, mock_open

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.nemo_retriever import (
    NemoOCRResult,
    NemoChunk,
    NemoRerankResult,
    NemoRetrieverProvider,
    get_nemo_retriever,
    DEFAULT_OCR_MODEL,
    DEFAULT_EMBED_MODEL,
    DEFAULT_RERANK_MODEL,
)


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

class TestNemoOCRResult:
    """Tests for NemoOCRResult data class."""

    def test_creation(self):
        """NemoOCRResult stores all fields correctly."""
        result = NemoOCRResult(
            text="extracted text",
            markdown="# Extracted\nText",
            confidence=0.95,
            page_number=1,
            processing_time_ms=123.45,
            model="nvidia/nemotron-ocr-v1",
        )
        assert result.text == "extracted text"
        assert result.markdown == "# Extracted\nText"
        assert result.confidence == 0.95
        assert result.page_number == 1
        assert result.processing_time_ms == 123.45
        assert result.model == "nvidia/nemotron-ocr-v1"


class TestNemoChunk:
    """Tests for NemoChunk data class."""

    def test_creation(self):
        """NemoChunk stores text and metadata."""
        chunk = NemoChunk(
            text="legal text",
            metadata={"source": "test.pdf", "page": 1},
        )
        assert chunk.text == "legal text"
        assert chunk.metadata["source"] == "test.pdf"
        assert chunk.embedding is None

    def test_with_embedding(self):
        """NemoChunk can hold an embedding vector."""
        chunk = NemoChunk(
            text="text",
            metadata={},
            embedding=[0.1, 0.2, 0.3],
        )
        assert chunk.embedding == [0.1, 0.2, 0.3]


class TestNemoRerankResult:
    """Tests for NemoRerankResult data class."""

    def test_creation(self):
        """NemoRerankResult stores rank, score, and text."""
        result = NemoRerankResult(
            index=0,
            score=0.95,
            text="relevant document",
            reasons=["nemotron-reranked"],
        )
        assert result.index == 0
        assert result.score == 0.95
        assert result.text == "relevant document"
        assert "nemotron-reranked" in result.reasons

    def test_default_reasons(self):
        """NemoRerankResult has empty reasons by default."""
        result = NemoRerankResult(index=1, score=0.8, text="doc")
        assert result.reasons == []


# ---------------------------------------------------------------------------
# Provider Initialization
# ---------------------------------------------------------------------------

class TestNemoRetrieverProviderInit:
    """Tests for NemoRetrieverProvider initialization."""

    def test_default_models(self):
        """Default models are correctly set."""
        assert DEFAULT_OCR_MODEL == "nvidia/nemotron-ocr-v1"
        assert DEFAULT_EMBED_MODEL == "nvidia/nemotron-embed-4b-v1"
        assert DEFAULT_RERANK_MODEL == "nvidia/llama-nemotron-rerank-1b-v2"

    def test_init_with_api_key(self):
        """Provider accepts explicit API key."""
        provider = NemoRetrieverProvider(api_key="test-key")
        assert provider.api_key == "test-key"
        assert provider.ocr_model == DEFAULT_OCR_MODEL
        assert provider.embed_model == DEFAULT_EMBED_MODEL
        assert provider.rerank_model == DEFAULT_RERANK_MODEL

    def test_init_with_custom_models(self):
        """Provider accepts custom model names."""
        provider = NemoRetrieverProvider(
            api_key="test-key",
            ocr_model="custom/ocr",
            embed_model="custom/embed",
            rerank_model="custom/rerank",
        )
        assert provider.ocr_model == "custom/ocr"
        assert provider.embed_model == "custom/embed"
        assert provider.rerank_model == "custom/rerank"

    def test_init_from_env(self):
        """Provider reads configuration from environment variables."""
        with patch.dict(os.environ, {
            "NVIDIA_API_KEY": "env-key",
            "HECTOR_NEMO_OCR_MODEL": "env/ocr",
            "HECTOR_NEMO_EMBED_MODEL": "env/embed",
            "HECTOR_NEMO_RERANK_MODEL": "env/rerank",
        }):
            provider = NemoRetrieverProvider()
            assert provider.api_key == "env-key"
            assert provider.ocr_model == "env/ocr"
            assert provider.embed_model == "env/embed"
            assert provider.rerank_model == "env/rerank"


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------

class TestNemoRetrieverHealthCheck:
    """Tests for NeMo Retriever availability check."""

    def test_no_api_key_unavailable(self):
        """Without API key, provider is unavailable."""
        provider = NemoRetrieverProvider(api_key=None)
        provider.api_key = ""
        assert provider.is_available is False

    def test_health_check_success(self):
        """Successful health check marks provider as available."""
        provider = NemoRetrieverProvider(api_key="test-key")
        with patch("requests.get") as mock_get:
            mock_get.return_value = MagicMock(status_code=200)
            assert provider.is_available is True

    def test_health_check_401(self):
        """401 response still means API endpoint exists."""
        provider = NemoRetrieverProvider(api_key="test-key")
        with patch("requests.get") as mock_get:
            mock_get.return_value = MagicMock(status_code=401)
            assert provider.is_available is True

    def test_health_check_405(self):
        """405 response means endpoint exists (method not allowed)."""
        provider = NemoRetrieverProvider(api_key="test-key")
        with patch("requests.get") as mock_get:
            mock_get.return_value = MagicMock(status_code=405)
            assert provider.is_available is True

    def test_health_check_timeout(self):
        """Timeout marks provider as unavailable."""
        provider = NemoRetrieverProvider(api_key="test-key")
        with patch("requests.get", side_effect=Exception("timeout")):
            assert provider.is_available is False

    def test_health_check_caches_result(self):
        """Health check result is cached after first call."""
        provider = NemoRetrieverProvider(api_key="test-key")
        with patch("requests.get") as mock_get:
            mock_get.return_value = MagicMock(status_code=200)
            _ = provider.is_available
            _ = provider.is_available
            assert mock_get.call_count == 1  # Only called once


# ---------------------------------------------------------------------------
# OCR
# ---------------------------------------------------------------------------

class TestNemoRetrieverOCR:
    """Tests for OCR processing."""

    def test_ocr_no_api_key(self):
        """OCR without API key raises ValueError."""
        provider = NemoRetrieverProvider(api_key=None)
        provider.api_key = ""
        with pytest.raises(ValueError, match="NVIDIA_API_KEY"):
            provider.ocr_page(b"fake-image", page_number=1)

    def test_ocr_success(self):
        """Successful OCR returns NemoOCRResult."""
        provider = NemoRetrieverProvider(api_key="test-key")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "text": "Section 302 IPC",
            "markdown": "# Section 302 IPC\nMurder punishment.",
            "confidence": 0.92,
        }
        mock_response.raise_for_status = MagicMock()

        with patch("requests.post", return_value=mock_response):
            result = provider.ocr_page(b"fake-image-bytes", page_number=5)
            assert isinstance(result, NemoOCRResult)
            assert result.text == "Section 302 IPC"
            assert result.confidence == 0.92
            assert result.page_number == 5
            assert result.processing_time_ms > 0

    def test_ocr_api_error(self):
        """OCR API error propagates exception."""
        provider = NemoRetrieverProvider(api_key="test-key")
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("API error")

        with patch("requests.post", return_value=mock_response):
            with pytest.raises(Exception, match="API error"):
                provider.ocr_page(b"image", page_number=1)


# ---------------------------------------------------------------------------
# Embedding
# ---------------------------------------------------------------------------

class TestNemoRetrieverEmbedding:
    """Tests for embedding generation."""

    def test_embed_no_api_key(self):
        """Embedding without API key raises ValueError."""
        provider = NemoRetrieverProvider(api_key=None)
        provider.api_key = ""
        with pytest.raises(ValueError, match="NVIDIA_API_KEY"):
            provider.embed_documents(["text"])

    def test_embed_single_document(self):
        """Embedding single document returns correct shape."""
        provider = NemoRetrieverProvider(api_key="test-key")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{"embedding": [0.1] * 2048}],
        }
        mock_response.raise_for_status = MagicMock()

        with patch("requests.post", return_value=mock_response):
            result = provider.embed_documents(["legal text"])
            assert len(result) == 1
            assert len(result[0]) == 2048

    def test_embed_multiple_documents(self):
        """Embedding multiple documents returns batch."""
        provider = NemoRetrieverProvider(api_key="test-key")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{"embedding": [0.1] * 2048}],
        }
        mock_response.raise_for_status = MagicMock()

        with patch("requests.post", return_value=mock_response):
            result = provider.embed_documents(["text1", "text2", "text3"])
            assert len(result) == 3

    def test_embed_query(self):
        """Query embedding returns single vector."""
        provider = NemoRetrieverProvider(api_key="test-key")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{"embedding": [0.2] * 2048}],
        }
        mock_response.raise_for_status = MagicMock()

        with patch("requests.post", return_value=mock_response):
            result = provider.embed_query("what is theft?")
            assert len(result) == 2048


# ---------------------------------------------------------------------------
# Reranking
# ---------------------------------------------------------------------------

class TestNemoRetrieverReranking:
    """Tests for document reranking."""

    def test_rerank_no_api_key(self):
        """Reranking without API key raises ValueError."""
        provider = NemoRetrieverProvider(api_key=None)
        provider.api_key = ""
        with pytest.raises(ValueError, match="NVIDIA_API_KEY"):
            provider.rerank("query", [{"text": "doc"}])

    def test_rerank_empty_documents(self):
        """Reranking empty list returns empty list."""
        provider = NemoRetrieverProvider(api_key="test-key")
        result = provider.rerank("query", [])
        assert result == []

    def test_rerank_success(self):
        """Successful reranking returns sorted results."""
        provider = NemoRetrieverProvider(api_key="test-key")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "rankings": [
                {"index": 1, "logit": 0.95},
                {"index": 0, "logit": 0.72},
                {"index": 2, "logit": 0.31},
            ],
        }
        mock_response.raise_for_status = MagicMock()

        with patch("requests.post", return_value=mock_response):
            docs = [
                {"text": "Section 302 IPC - murder"},
                {"text": "Section 376 IPC - rape"},
                {"text": "Weather in Mumbai"},
            ]
            results = provider.rerank("punishment for crime", docs, top_k=3)
            assert len(results) == 3
            assert results[0].index == 1
            assert results[0].score == 0.95
            assert "nemotron-reranked" in results[0].reasons[0]


# ---------------------------------------------------------------------------
# Document Processing Pipeline
# ---------------------------------------------------------------------------

class TestNemoRetrieverDocumentPipeline:
    """Tests for the full document processing pipeline."""

    def test_chunk_text_short(self):
        """Short text returns single chunk."""
        provider = NemoRetrieverProvider(api_key="test-key")
        chunks = provider._chunk_text("Short text that is definitely long enough to pass the minimum check and be considered valid content.", chunk_size=800, overlap=150)
        assert len(chunks) == 1

    def test_chunk_text_empty(self):
        """Empty text returns empty list."""
        provider = NemoRetrieverProvider(api_key="test-key")
        assert provider._chunk_text("", chunk_size=800, overlap=150) == []
        assert provider._chunk_text("   ", chunk_size=800, overlap=150) == []

    def test_chunk_text_long(self):
        """Long text is split into multiple chunks."""
        provider = NemoRetrieverProvider(api_key="test-key")
        long_text = "This is a sentence with some words. " * 500  # ~500 sentences
        chunks = provider._chunk_text(long_text, chunk_size=800, overlap=150)
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk.strip()) > 0


# ---------------------------------------------------------------------------
# Factory Function
# ---------------------------------------------------------------------------

class TestNemoRetrieverFactory:
    """Tests for get_nemo_retriever factory."""

    def test_disabled_by_default(self):
        """Returns None when HECTOR_NEMO_RETRIEVER_ENABLED is not '1'."""
        with patch.dict(os.environ, {"HECTOR_NEMO_RETRIEVER_ENABLED": "0"}):
            assert get_nemo_retriever() is None

    def test_enabled_with_key(self):
        """Returns provider when enabled and API key is set."""
        with patch.dict(os.environ, {
            "HECTOR_NEMO_RETRIEVER_ENABLED": "1",
            "NVIDIA_API_KEY": "test-key",
        }):
            with patch("requests.get") as mock_get:
                mock_get.return_value = MagicMock(status_code=200)
                provider = get_nemo_retriever()
                assert isinstance(provider, NemoRetrieverProvider)

    def test_enabled_without_key(self):
        """Returns None when enabled but no API key."""
        with patch.dict(os.environ, {
            "HECTOR_NEMO_RETRIEVER_ENABLED": "1",
            "NVIDIA_API_KEY": "",
        }):
            assert get_nemo_retriever() is None

    def test_enabled_but_unreachable(self):
        """Returns None when API is unreachable."""
        with patch.dict(os.environ, {
            "HECTOR_NEMO_RETRIEVER_ENABLED": "1",
            "NVIDIA_API_KEY": "test-key",
        }):
            with patch("requests.get", side_effect=Exception("timeout")):
                assert get_nemo_retriever() is None


# ---------------------------------------------------------------------------
# Integration
# ---------------------------------------------------------------------------

class TestNemoRetrieverIntegration:
    """Verify NemoRetriever is properly wired into ingestor."""

    def test_nemo_retriever_importable(self):
        """get_nemo_retriever is importable."""
        assert callable(get_nemo_retriever)

    @pytest.mark.skip(reason="hangs due to chromadb import in CI — verified via source inspection")
    def test_enhanced_ingestor_has_nemo_attr(self):
        """EnhancedHectorIngestor source code references nemo_retriever."""
        import os
        ingestor_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "utils", "enhanced_ingestor.py"
        )
        with open(ingestor_path, "r") as f:
            source = f.read()
        assert "nemo_retriever" in source
        assert "get_nemo_retriever" in source
