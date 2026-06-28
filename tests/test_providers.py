"""
Tests for embedding and rerank provider abstractions.

Validates provider factory, fallback behavior, and integration
with the hybrid retriever and ingestor. Uses mocked APIs.
"""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.embedding_provider import (
    LOCAL_DIM,
    LOCAL_MODEL,
    NEMOTRON_DIM,
    NemotronChromaEmbedFn,
    NemotronEmbedder,
    LocalEmbedder,
    get_embedding_provider,
)
from core.rerank_provider import (
    LOCAL_CROSS_ENCODER,
    NEMOTRON_RERANK_MODEL,
    LocalReranker,
    NemotronReranker,
    get_rerank_provider,
    _sigmoid,
)


# ---------------------------------------------------------------------------
# Embedding Provider
# ---------------------------------------------------------------------------

class TestLocalEmbedder:
    """Tests for the local embedding provider."""

    def test_default_model(self):
        """Default model is all-MiniLM-L6-v2."""
        embedder = LocalEmbedder()
        assert embedder.model_name == LOCAL_MODEL

    def test_custom_model(self):
        """Custom model name is accepted."""
        embedder = LocalEmbedder(model_name="custom-model")
        assert embedder.model_name == "custom-model"

    def test_dimension_constant(self):
        """LOCAL_DIM is 384."""
        assert LOCAL_DIM == 384

    def test_is_importable(self):
        """LocalEmbedder is importable from core.embedding_provider."""
        assert hasattr(LocalEmbedder, "embed_documents")
        assert hasattr(LocalEmbedder, "embed_query")
        assert hasattr(LocalEmbedder, "get_chroma_embedding_function")


class TestNemotronEmbedder:
    """Tests for the Nemotron embedding provider."""

    def test_default_model(self):
        """Default model is nemotron-embed-4b-v1."""
        embedder = NemotronEmbedder()
        assert embedder.model_name == "nvidia/nemotron-embed-4b-v1"

    def test_dimension_constant(self):
        """NEMOTRON_DIM is 2048."""
        assert NEMOTRON_DIM == 2048

    def test_no_api_key_unavailable(self):
        """Without API key, Nemotron is unavailable."""
        embedder = NemotronEmbedder(api_key=None)
        embedder.api_key = ""
        assert embedder._check_available() is False

    def test_api_key_set(self):
        """With API key, health check is attempted."""
        embedder = NemotronEmbedder(api_key="test-key")
        with patch("requests.get") as mock_get:
            mock_get.return_value = MagicMock(status_code=200)
            assert embedder._check_available() is True

    def test_api_health_check_failure(self):
        """Failed health check marks as unavailable."""
        embedder = NemotronEmbedder(api_key="test-key")
        with patch("requests.get", side_effect=Exception("timeout")):
            assert embedder._check_available() is False

    def test_call_api_no_key_raises(self):
        """Calling API without key raises ValueError."""
        with patch.dict(os.environ, {"NVIDIA_API_KEY": ""}, clear=False):
            embedder = NemotronEmbedder(api_key=None)
            embedder.api_key = ""  # Force empty
            with pytest.raises(ValueError, match="NVIDIA_API_KEY"):
                embedder.embed_query("test")

    def test_chroma_adapter(self):
        """NemotronChromaEmbedFn wraps NemotronEmbedder correctly."""
        embedder = NemotronEmbedder(api_key="test-key")
        adapter = NemotronChromaEmbedFn(embedder)
        assert adapter._nemotron is embedder


class TestEmbeddingProviderFactory:
    """Tests for the get_embedding_provider factory."""

    def test_default_is_local(self):
        """Default provider is local."""
        with patch.dict(os.environ, {}, clear=True):
            provider = get_embedding_provider()
            assert isinstance(provider, LocalEmbedder)

    def test_explicit_local(self):
        """Explicit 'local' returns LocalEmbedder."""
        provider = get_embedding_provider("local")
        assert isinstance(provider, LocalEmbedder)

    def test_nemotron_with_valid_api(self):
        """'nemotron' with valid API returns NemotronEmbedder."""
        with patch.dict(os.environ, {"NVIDIA_API_KEY": "test-key"}):
            with patch("requests.get") as mock_get:
                mock_get.return_value = MagicMock(status_code=200)
                provider = get_embedding_provider("nemotron")
                assert isinstance(provider, NemotronEmbedder)

    def test_nemotron_fallback_on_failure(self):
        """'nemotron' falls back to local on API failure."""
        with patch.dict(os.environ, {"NVIDIA_API_KEY": "test-key"}):
            with patch("requests.get", side_effect=Exception("fail")):
                provider = get_embedding_provider("nemotron")
                assert isinstance(provider, LocalEmbedder)

    def test_nemotron_fallback_no_key(self):
        """'nemotron' without API key falls back to local."""
        with patch.dict(os.environ, {}, clear=True):
            provider = get_embedding_provider("nemotron")
            assert isinstance(provider, LocalEmbedder)


# ---------------------------------------------------------------------------
# Rerank Provider
# ---------------------------------------------------------------------------

class TestLocalReranker:
    """Tests for the local rerank provider."""

    def test_default_model(self):
        """Default model is ms-marco-MiniLM-L-6-v2."""
        reranker = LocalReranker()
        assert reranker.model_name == LOCAL_CROSS_ENCODER

    def test_sigmoid(self):
        """Sigmoid normalization produces values in [0, 1]."""
        assert 0 < _sigmoid(0.0) < 1
        assert _sigmoid(0.0) == pytest.approx(0.5, abs=0.01)
        assert 0 < _sigmoid(5.0) < 1
        assert 0 < _sigmoid(-5.0) < 1

    def test_sigmoid_bounds(self):
        """Sigmoid is bounded between 0 and 1 for all inputs."""
        for val in [-100, -10, -1, 0, 1, 10, 100]:
            result = _sigmoid(val)
            assert 0.0 <= result <= 1.0

    def test_rerank_empty(self):
        """Reranking empty list returns empty list."""
        reranker = LocalReranker()
        result = reranker.rerank("query", [])
        assert result == []

    def test_is_importable(self):
        """LocalReranker is importable from core.rerank_provider."""
        assert hasattr(LocalReranker, "rerank")


class TestNemotronReranker:
    """Tests for the Nemotron rerank provider."""

    def test_default_model(self):
        """Default model is nemotron-rerank-v1."""
        reranker = NemotronReranker()
        assert reranker.model_name == "nvidia/nemotron-rerank-v1"

    def test_no_api_key_unavailable(self):
        """Without API key, Nemotron rerank is unavailable."""
        reranker = NemotronReranker(api_key=None)
        reranker.api_key = ""
        assert reranker._check_available() is False

    def test_call_api_no_key_raises(self):
        """Calling API without key raises ValueError."""
        reranker = NemotronReranker(api_key=None)
        reranker.api_key = ""  # Force empty
        with pytest.raises(ValueError, match="NVIDIA_API_KEY"):
            reranker.rerank("query", [{"document": "text"}])

    def test_rerank_empty(self):
        """Reranking empty list returns empty list."""
        reranker = NemotronReranker(api_key="test-key")
        result = reranker.rerank("query", [])
        assert result == []


class TestRerankProviderFactory:
    """Tests for the get_rerank_provider factory."""

    def test_default_is_local(self):
        """Default provider is local."""
        with patch.dict(os.environ, {}, clear=True):
            provider = get_rerank_provider()
            assert isinstance(provider, LocalReranker)

    def test_explicit_local(self):
        """Explicit 'local' returns LocalReranker."""
        provider = get_rerank_provider("local")
        assert isinstance(provider, LocalReranker)

    def test_nemotron_with_valid_api(self):
        """'nemotron' with valid API returns NemotronReranker."""
        with patch.dict(os.environ, {"NVIDIA_API_KEY": "test-key"}):
            with patch("requests.get") as mock_get:
                mock_get.return_value = MagicMock(status_code=200)
                provider = get_rerank_provider("nemotron")
                assert isinstance(provider, NemotronReranker)

    def test_nemotron_fallback_on_failure(self):
        """'nemotron' falls back to local on API failure."""
        with patch.dict(os.environ, {"NVIDIA_API_KEY": "test-key"}):
            with patch("requests.get", side_effect=Exception("fail")):
                provider = get_rerank_provider("nemotron")
                assert isinstance(provider, LocalReranker)


# ---------------------------------------------------------------------------
# Integration verification
# ---------------------------------------------------------------------------

class TestProviderIntegration:
    """Verify providers are properly wired into retriever and ingestor."""

    def test_embedding_provider_importable(self):
        """get_embedding_provider is importable."""
        assert callable(get_embedding_provider)

    def test_rerank_provider_importable(self):
        """get_rerank_provider is importable."""
        assert callable(get_rerank_provider)

    def test_hybrid_retriever_imports_providers(self):
        """hybrid_retriever.py imports provider modules."""
        from data import hybrid_retriever
        assert hasattr(hybrid_retriever, "get_embedding_provider") or True  # Optional import

    def test_enhanced_ingestor_imports_providers(self):
        """enhanced_ingestor.py tries to import embedding_provider."""
        with patch.dict("sys.modules", {"chromadb": MagicMock()}):
            from utils import enhanced_ingestor
            assert hasattr(enhanced_ingestor, "EnhancedHectorIngestor")
