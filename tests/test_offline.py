"""
Unit tests for Offline Capability Module.
Tests offline mode, bundling, and search.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.offline import (
    OfflineBundle,
    OfflineConfig,
    OfflineEmbeddingModel,
    OfflineVectorStore,
    OfflineLegalBundle,
    OfflineMode,
    get_offline_mode,
    is_offline,
    get_available_bundles,
)


class TestOfflineConfig:
    """Test offline configuration."""

    def test_config_defaults(self):
        """Test default configuration values."""
        config = OfflineConfig()
        assert config.bundle_path is None
        assert config.embedding_model_path is None
        assert config.use_gpu is False
        assert config.cache_size_mb == 512

    def test_config_custom_values(self):
        """Test custom configuration."""
        config = OfflineConfig(
            bundle_path="/path/to/bundle",
            use_gpu=True,
            cache_size_mb=1024
        )
        assert config.bundle_path == "/path/to/bundle"
        assert config.use_gpu is True
        assert config.cache_size_mb == 1024


class TestOfflineBundle:
    """Test offline bundle dataclass."""

    def test_bundle_creation(self):
        """Test bundle creation."""
        bundle = OfflineBundle(
            version="1.0.0",
            created_at="2024-01-01",
            acts_included=["BNS", "IPC"],
            total_documents=1000,
            index_size_mb=50.0,
            checksum="abc123"
        )
        assert bundle.version == "1.0.0"
        assert bundle.total_documents == 1000


class TestOfflineEmbeddingModel:
    """Test offline embedding model."""

    def test_model_initialization(self):
        """Test model initializes."""
        model = OfflineEmbeddingModel(OfflineConfig())
        assert model is not None
        assert model.embedding_dimension == 384

    def test_model_has_encode_method(self):
        """Test model has encode method."""
        model = OfflineEmbeddingModel(OfflineConfig())
        assert hasattr(model, 'encode')


class TestOfflineVectorStore:
    """Test offline vector store."""

    def test_store_initialization(self):
        """Test store initializes."""
        store = OfflineVectorStore()
        assert store is not None
        assert store.embeddings == []
        assert store.documents == []

    def test_store_load_bundle_nonexistent(self):
        """Test loading nonexistent bundle."""
        result = store.load_bundle("/nonexistent/path")
        assert result is False

    def test_store_search_empty(self):
        """Test search on empty store."""
        store = OfflineVectorStore()
        import numpy as np
        result = store.search(np.array([0.1] * 384))
        assert result == []

    def test_store_get_count(self):
        """Test document count."""
        store = OfflineVectorStore()
        count = store.get_count()
        assert count == 0


class TestOfflineLegalBundle:
    """Test offline legal bundle manager."""

    def test_bundle_manager_initialization(self):
        """Test bundle manager initializes."""
        manager = OfflineLegalBundle()
        assert manager is not None

    def test_discover_bundles_empty(self):
        """Test discovering bundles when none exist."""
        manager = OfflineLegalBundle()
        bundles = manager.discover_bundles()
        assert isinstance(bundles, list)

    def test_get_default_bundle_dir(self):
        """Test default bundle directory path."""
        manager = OfflineLegalBundle()
        bundle_dir = manager._get_default_bundle_dir()
        assert bundle_dir is not None
        assert "offline" in bundle_dir.lower() or "bundle" in bundle_dir.lower()


class TestOfflineMode:
    """Test offline mode controller."""

    def test_offline_mode_initialization(self):
        """Test offline mode initializes."""
        mode = OfflineMode()
        assert mode is not None
        assert hasattr(mode, 'config')
        assert hasattr(mode, 'embedding_model')

    def test_offline_mode_default_online(self):
        """Test default mode is online."""
        mode = OfflineMode()
        assert mode.is_online is True

    def test_enable_offline_mode_fails_gracefully(self):
        """Test enable offline fails gracefully."""
        mode = OfflineMode()
        # Should fail gracefully when no bundle exists
        result = mode.enable_offline_mode("/nonexistent")
        assert result is False

    def test_disable_offline_mode(self):
        """Test disabling offline mode."""
        mode = OfflineMode()
        mode.is_online = False
        mode.disable_offline_mode()
        assert mode.is_online is True

    def test_search_offline_fails_when_online(self):
        """Test offline search fails when online."""
        mode = OfflineMode()
        result = mode.search_offline("test query")
        assert result == []

    def test_get_bundle_info_no_bundle(self):
        """Test bundle info when no bundle loaded."""
        mode = OfflineMode()
        info = mode.get_bundle_info()
        assert info['status'] == "no_bundle"


class TestModuleFunctions:
    """Test module-level functions."""

    def test_get_offline_mode_singleton(self):
        """Test get_offline_mode returns singleton."""
        mode1 = get_offline_mode()
        mode2 = get_offline_mode()
        assert mode1 is mode2

    def test_is_offline_default(self):
        """Test is_offline returns False by default."""
        result = is_offline()
        assert result is False

    def test_get_available_bundles(self):
        """Test get_available_bundles returns list."""
        bundles = get_available_bundles()
        assert isinstance(bundles, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])