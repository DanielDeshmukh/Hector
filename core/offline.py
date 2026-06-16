"""
Offline Capability Module for HECTOR.
Enables legal research without internet connection.
"""

from __future__ import annotations
import os
import json
import pickle
import hashlib
from pathlib import Path
from dataclasses import dataclass
from typing import Callable, list
import logging
import numpy as np

# Offline embedding model configuration
OFFLINE_EMBEDDING_CONFIG = {
    "model_name": "sentence-transformers/all-MiniLM-L6-v2",
    "dimension": 384,
    "max_seq_length": 256,
    "pooling_mode": "mean",
}

# Compressed bundle configuration
BUNDLE_VERSION = "1.0.0"
BUNDLE_METADATA_FILE = "metadata.json"
LEGAL_ACTS_INCLUDED = [
    "BNS",
    "BNSS",
    "BSA",
    "IPC",
    "CRPC",
    "IEA",
    "CPC",
    "Contract Act",
    "Transfer of Property Act",
    "Hindu Marriage Act",
    "Hindu Succession Act",
]


@dataclass
class OfflineBundle:
    """Represents an offline legal database bundle."""

    version: str
    created_at: str
    acts_included: list[str]
    total_documents: int
    index_size_mb: float
    checksum: str


@dataclass
class OfflineConfig:
    """Configuration for offline mode."""

    bundle_path: str | None = None
    embedding_model_path: str | None = None
    use_gpu: bool = False
    cache_size_mb: int = 512


class OfflineEmbeddingModel:
    """Local embedding model for offline use."""

    def __init__(self, config: OfflineConfig):
        self.config = config
        self.model = None
        self.embedding_dimension = OFFLINE_EMBEDDING_CONFIG["dimension"]

    def load(self) -> bool:
        """Load the offline embedding model."""
        try:
            from sentence_transformers import SentenceTransformer

            if self.config.embedding_model_path:
                self.model = SentenceTransformer(self.config.embedding_model_path)
            else:
                # Use local model (cached or bundled)
                self.model = SentenceTransformer(
                    OFFLINE_EMBEDDING_CONFIG["model_name"],
                    cache_folder=self._get_cache_folder(),
                )
            return True
        except Exception as e:
            print(f"[!] Failed to load offline model: {e}")
            return False

    def _get_cache_folder(self) -> str:
        """Get local cache folder for model."""
        return os.path.join(os.path.dirname(__file__), "..", "models", "offline")

    def encode(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        """Encode texts to embeddings."""
        if self.model is None:
            if not self.load():
                raise RuntimeError("Offline embedding model not available")

        return self.model.encode(
            texts, batch_size=batch_size, show_progress_bar=False, convert_to_numpy=True
        )


class OfflineVectorStore:
    """Offline vector database using local storage."""

    def __init__(self, bundle_path: str | None = None):
        self.bundle_path = bundle_path
        self.embeddings: list[np.ndarray] = []
        self.documents: list[dict] = []
        self.metadata: dict = {}
        self._index: dict = {}

    def load_bundle(self, bundle_path: str) -> bool:
        """Load an offline bundle."""
        try:
            path = Path(bundle_path)
            if not path.exists():
                return False

            # Load metadata
            meta_file = path / BUNDLE_METADATA_FILE
            if meta_file.exists():
                with open(meta_file, "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)

            # Load index file
            index_file = path / "index.pkl"
            if index_file.exists():
                with open(index_file, "rb") as f:
                    data = pickle.load(f)
                    self.embeddings = data.get("embeddings", [])
                    self.documents = data.get("documents", [])
                    self._index = data.get("index", {})

            return True
        except Exception as e:
            print(f"[!] Failed to load bundle: {e}")
            return False

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10,
        filter_fn: Callable[[dict], bool] | None = None,
    ) -> list[dict]:
        """Search the offline vector store."""
        if not self.embeddings:
            return []

        # Calculate similarities
        scores = []
        for i, emb in enumerate(self.embeddings):
            # Cosine similarity
            sim = np.dot(query_embedding, emb) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(emb) + 1e-8
            )
            if filter_fn is None or filter_fn(self.documents[i]):
                scores.append((i, sim))

        # Sort by score
        scores.sort(key=lambda x: x[1], reverse=True)

        # Return top-k
        results = []
        for i, score in scores[:top_k]:
            result = self.documents[i].copy()
            result["score"] = float(score)
            results.append(result)

        return results

    def get_count(self) -> int:
        """Get total document count."""
        return len(self.documents)


class OfflineLegalBundle:
    """Manages offline legal text bundles."""

    def __init__(self, bundle_dir: str | None = None):
        self.bundle_dir = bundle_dir or self._get_default_bundle_dir()
        self.available_bundles: list[OfflineBundle] = []

    def _get_default_bundle_dir(self) -> str:
        """Get default bundle directory."""
        return os.path.join(os.path.dirname(__file__), "..", "bundles")

    def discover_bundles(self) -> list[OfflineBundle]:
        """Discover available offline bundles."""
        bundles = []

        if not os.path.exists(self.bundle_dir):
            return bundles

        for item in os.listdir(self.bundle_dir):
            bundle_path = os.path.join(self.bundle_dir, item)
            if os.path.isdir(bundle_path):
                meta_file = os.path.join(bundle_path, BUNDLE_METADATA_FILE)
                if os.path.exists(meta_file):
                    try:
                        with open(meta_file, "r", encoding="utf-8") as f:
                            meta = json.load(f)
                            bundles.append(
                                OfflineBundle(
                                    version=meta.get("version", "1.0.0"),
                                    created_at=meta.get("created_at", "unknown"),
                                    acts_included=meta.get("acts_included", []),
                                    total_documents=meta.get("total_documents", 0),
                                    index_size_mb=meta.get("index_size_mb", 0.0),
                                    checksum=meta.get("checksum", ""),
                                )
                            )
                    except Exception:
                        logging.debug(
                            "Failed to load bundle metadata from %s",
                            meta_file,
                            exc_info=True,
                        )

        self.available_bundles = bundles
        return bundles

    def create_bundle(
        self, source_dir: str, output_path: str, include_acts: list[str] | None = None
    ) -> bool:
        """Create a new offline bundle from source documents."""
        try:
            from sentence_transformers import SentenceTransformer

            # Initialize embedding model
            model = SentenceTransformer(OFFLINE_EMBEDDING_CONFIG["model_name"])

            documents = []
            embeddings = []
            index = {}

            # Process documents
            source_path = Path(source_dir)
            for doc_file in source_path.rglob("*.txt"):
                try:
                    with open(doc_file, "r", encoding="utf-8") as f:
                        content = f.read()
                        # Split into chunks
                        chunks = self._chunk_text(content, chunk_size=500)

                        for i, chunk in enumerate(chunks):
                            doc = {
                                "id": f"{doc_file.stem}_{i}",
                                "source": str(doc_file),
                                "content": chunk,
                                "chunk_index": i,
                            }
                            documents.append(doc)

                            # Create embedding
                            emb = model.encode(chunk, convert_to_numpy=True)
                            embeddings.append(emb)

                            # Add to index
                            act_name = doc_file.stem.split("_")[0]
                            if act_name not in index:
                                index[act_name] = []
                            index[act_name].append(len(documents) - 1)

                except Exception as e:
                    print(f"[!] Error processing {doc_file}: {e}")

            # Create output directory
            os.makedirs(output_path, exist_ok=True)

            # Save index
            index_data = {
                "embeddings": embeddings,
                "documents": documents,
                "index": index,
            }
            with open(os.path.join(output_path, "index.pkl"), "wb") as f:
                pickle.dump(index_data, f)

            # Calculate checksum
            checksum = hashlib.sha256(pickle.dumps(index_data)).hexdigest()[:16]

            # Save metadata
            metadata = {
                "version": BUNDLE_VERSION,
                "created_at": str(Path(output_path).stat().st_ctime),
                "acts_included": include_acts or LEGAL_ACTS_INCLUDED,
                "total_documents": len(documents),
                "index_size_mb": sum(e.nbytes for e in embeddings) / (1024 * 1024),
                "checksum": checksum,
            }
            with open(os.path.join(output_path, BUNDLE_METADATA_FILE), "w") as f:
                json.dump(metadata, f, indent=2)

            print(f"[+] Created offline bundle: {output_path}")
            print(f"    Documents: {len(documents)}")
            print(f"    Size: {metadata['index_size_mb']:.2f} MB")
            return True

        except Exception as e:
            print(f"[!] Failed to create bundle: {e}")
            return False

    def _chunk_text(self, text: str, chunk_size: int = 500) -> list[str]:
        """Split text into chunks."""
        # Split by paragraphs first
        paragraphs = text.split("\n\n")
        chunks = []
        current = ""

        for para in paragraphs:
            if len(current) + len(para) <= chunk_size:
                current += para + "\n\n"
            else:
                if current:
                    chunks.append(current.strip())
                current = para + "\n\n"

        if current:
            chunks.append(current.strip())

        return chunks if chunks else [text[:chunk_size]]


class OfflineMode:
    """Main offline mode controller."""

    def __init__(self, config: OfflineConfig | None = None):
        self.config = config or OfflineConfig()
        self.embedding_model = OfflineEmbeddingModel(self.config)
        self.vector_store = OfflineVectorStore(self.config.bundle_path)
        self.bundle_manager = OfflineLegalBundle()
        self.is_online = True

    def enable_offline_mode(self, bundle_path: str) -> bool:
        """Enable offline mode with a specific bundle."""
        print("[*] Enabling offline mode...")

        # Load bundle
        if not self.vector_store.load_bundle(bundle_path):
            print("[!] Failed to load offline bundle")
            return False

        # Load embedding model
        if not self.embedding_model.load():
            print("[!] Failed to load offline embedding model")
            return False

        self.is_online = False
        print("[+] Offline mode enabled")
        print(f"    Documents: {self.vector_store.get_count()}")
        return True

    def disable_offline_mode(self) -> None:
        """Disable offline mode and revert to online."""
        self.is_online = True
        self.embedding_model = None
        print("[+] Online mode enabled")

    def search_offline(
        self, query: str, top_k: int = 10, filter_act: str | None = None
    ) -> list[dict]:
        """Search in offline mode."""
        if self.is_online:
            print("[!] Not in offline mode")
            return []

        # Encode query
        query_embedding = self.embedding_model.encode([query])[0]

        # Search
        def filter_fn(doc):
            return doc.get("source", "").startswith(filter_act)

        if not filter_act:
            filter_fn = None

        return self.vector_store.search(query_embedding, top_k, filter_fn)

    def get_bundle_info(self) -> dict:
        """Get current bundle information."""
        if not self.vector_store.metadata:
            return {"status": "no_bundle"}

        return {
            "status": "loaded",
            "version": self.vector_store.metadata.get("version"),
            "documents": self.vector_store.metadata.get("total_documents"),
            "acts": self.vector_store.metadata.get("acts_included", []),
        }


def create_offline_bundle(
    source_dir: str, output_dir: str, include_acts: list[str] | None = None
) -> bool:
    """Helper function to create an offline bundle."""
    manager = OfflineLegalBundle()
    return manager.create_bundle(source_dir, output_dir, include_acts)


def get_available_bundles() -> list[OfflineBundle]:
    """Helper function to get available bundles."""
    manager = OfflineLegalBundle()
    return manager.discover_bundles()


# Offline mode singleton
_offline_mode: OfflineMode | None = None


def get_offline_mode() -> OfflineMode:
    """Get the global offline mode instance."""
    global _offline_mode
    if _offline_mode is None:
        _offline_mode = OfflineMode()
    return _offline_mode


def is_offline() -> bool:
    """Check if running in offline mode."""
    return not get_offline_mode().is_online


def search_offline(query: str, top_k: int = 10) -> list[dict]:
    """Convenience function for offline search."""
    return get_offline_mode().search_offline(query, top_k)
