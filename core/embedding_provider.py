"""
Embedding Provider abstraction for HECTOR.

Provides a unified interface for generating embeddings, with support for:
- Local: sentence-transformers all-MiniLM-L6-v2 (default, 384-dim)
- Nemotron: NVIDIA Nemotron embed via API (2048-dim, better for legal text)

Falls back to local model if the Nemotron API is unavailable.

Configuration via environment variables:
    HECTOR_EMBEDDING_PROVIDER: "local" | "nemotron" (default: "local")
    HECTOR_NEMOTRON_EMBED_MODEL: model ID (default: "nvidia/nemotron-embed-4b-v1")
    HECTOR_NEMOTRON_API_KEY: NVIDIA API key for Nemotron
    HECTOR_EMBEDDING_DIM: embedding dimension (default: 384, Nemotron: 2048)
"""

import logging
import os

logger = logging.getLogger("hector.embedding")

# Default models
LOCAL_MODEL = "all-MiniLM-L6-v2"
LOCAL_DIM = 384
NEMOTRON_MODEL = "nvidia/nemotron-embed-4b-v1"
NEMOTRON_DIM = 2048


class LocalEmbedder:
    """Embeddings via sentence-transformers (runs locally, no API key needed)."""

    def __init__(self, model_name: str = LOCAL_MODEL):
        self.model_name = model_name
        self._embed_fn = None
        self._dimension = LOCAL_DIM

    def _load(self):
        if self._embed_fn is not None:
            return
        try:
            from chromadb.utils import embedding_functions
            os.environ.setdefault("HF_HUB_OFFLINE", "1")
            self._embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=self.model_name
            )
            self._dimension = self._embed_fn._model.get_sentence_embedding_dimension()
            logger.info(f"Loaded local embedder: {self.model_name} ({self._dimension}d)")
        except Exception as e:
            logger.error(f"Failed to load local embedder: {e}")
            raise

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of documents."""
        self._load()
        return self._embed_fn(texts)

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query."""
        self._load()
        return self._embed_fn([text])[0]

    def get_chroma_embedding_function(self):
        """Return the ChromaDB-compatible embedding function."""
        self._load()
        return self._embed_fn


class NemotronEmbedder:
    """Embeddings via NVIDIA Nemotron embed API (requires NVIDIA_API_KEY)."""

    def __init__(
        self,
        model_name: str = NEMOTRON_MODEL,
        api_key: str | None = None,
        base_url: str = "https://ai.api.nvidia.com/v1/retrieval",
    ):
        self.model_name = model_name
        self.api_key = api_key or os.getenv("NVIDIA_API_KEY", "")
        self.base_url = base_url
        self._dimension = NEMOTRON_DIM
        self._available = None  # Lazy check

    def _check_available(self) -> bool:
        """Check if the Nemotron API is reachable."""
        if self._available is not None:
            return self._available

        if not self.api_key:
            logger.warning("NVIDIA_API_KEY not set — Nemotron embed unavailable")
            self._available = False
            return False

        try:
            import requests
            resp = requests.get(
                f"{self.base_url}/nvidia/nemotron-embed-4b-v1",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10,
            )
            self._available = resp.status_code in (200, 405)  # 405 = method not allowed = endpoint exists
        except Exception as e:
            logger.warning(f"Nemotron embed health check failed: {e}")
            self._available = False

        return self._available

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of documents via Nemotron API."""
        return self._call_api(texts)

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query via Nemotron API."""
        results = self._call_api([text])
        return results[0]

    def _call_api(self, inputs: list[str]) -> list[list[float]]:
        """Call the Nemotron embedding API."""
        import requests

        if not self.api_key:
            raise ValueError("NVIDIA_API_KEY is required for Nemotron embeddings")

        # Nemotron embed processes one input at a time
        embeddings = []
        for text in inputs:
            resp = requests.post(
                f"{self.base_url}/nvidia/nemotron-embed-4b-v1",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "input": text,
                    "model": self.model_name,
                    "input_type": "query",
                    "encoding_format": "float",
                },
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            emb = data.get("data", [{}])[0].get("embedding", [])
            if not emb:
                raise ValueError(f"Empty embedding returned for input: {text[:50]}...")
            embeddings.append(emb)

        return embeddings

    def get_chroma_embedding_function(self):
        """Return a ChromaDB-compatible embedding function wrapper."""
        return NemotronChromaEmbedFn(self)


class NemotronChromaEmbedFn:
    """Adapter that wraps NemotronEmbedder for ChromaDB's embedding_functions API."""

    def __init__(self, nemotron: NemotronEmbedder):
        self._nemotron = nemotron

    def __call__(self, input: list[str]) -> list[list[float]]:
        return self._nemotron.embed_documents(input)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def get_embedding_provider(provider: str | None = None) -> LocalEmbedder | NemotronEmbedder:
    """
    Get the embedding provider based on configuration.

    Falls back to local if Nemotron is not available.
    """
    if provider is None:
        provider = os.getenv("HECTOR_EMBEDDING_PROVIDER", "local")

    if provider == "nemotron":
        embedder = NemotronEmbedder(
            model_name=os.getenv("HECTOR_NEMOTRON_EMBED_MODEL", NEMOTRON_MODEL),
        )
        if embedder._check_available():
            logger.info("Using Nemotron embed provider")
            return embedder
        else:
            logger.warning("Nemotron embed unavailable — falling back to local")
            return LocalEmbedder()

    return LocalEmbedder()
