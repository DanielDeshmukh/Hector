"""
Rerank Provider abstraction for HECTOR.

Provides a unified interface for reranking retrieved documents, with support for:
- Local: cross-encoder/ms-marco-MiniLM-L-6-v2 (default)
- Nemotron: NVIDIA Nemotron rerank via API (better for legal text)

Falls back to local cross-encoder if the Nemotron API is unavailable.

Configuration via environment variables:
    HECTOR_RERANK_PROVIDER: "local" | "nemotron" (default: "local")
    HECTOR_NEMOTRON_RERANK_MODEL: model ID (default: "nvidia/nemotron-rerank-v1")
    HECTOR_NEMOTRON_API_KEY: NVIDIA API key for Nemotron
"""

import logging
import math
import os
from typing import Any

logger = logging.getLogger("hector.rerank")

# Default models
LOCAL_CROSS_ENCODER = "cross-encoder/ms-marco-MiniLM-L-6-v2"
NEMOTRON_RERANK_MODEL = "nvidia/nemotron-rerank-v1"


def _sigmoid(value: float) -> float:
    """Sigmoid normalization for raw scores."""
    if value >= 0:
        z = math.exp(-value)
        return 1 / (1 + z)
    z = math.exp(value)
    return z / (1 + z)


class LocalReranker:
    """Reranking via sentence-transformers CrossEncoder (runs locally)."""

    def __init__(self, model_name: str = LOCAL_CROSS_ENCODER):
        self.model_name = model_name
        self._model = None

    def _load(self):
        if self._model is not None:
            return
        try:
            from sentence_transformers import CrossEncoder
            os.environ.setdefault("HF_HUB_OFFLINE", "1")
            self._model = CrossEncoder(self.model_name)
            logger.info(f"Loaded local reranker: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to load local reranker: {e}")
            raise

    def rerank(
        self, query: str, documents: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Rerank documents by relevance to query.

        Args:
            query: The search query
            documents: List of document dicts with at least 'document' key

        Returns:
            Same list with 'reranker_score' added, sorted by score desc
        """
        if not documents:
            return documents

        self._load()
        pairs = [(query, doc.get("document", "")) for doc in documents]
        raw_scores = self._model.predict(pairs)

        for doc, raw_score in zip(documents, raw_scores):
            score = _sigmoid(float(raw_score))
            doc["reranker_score"] = round(score, 6)
            doc["score"] = doc["reranker_score"]
            doc["similarity_score"] = doc["reranker_score"]
            doc["reasons"] = [*doc.get("reasons", []), "cross-encoder-reranked"]

        documents.sort(key=lambda d: d.get("reranker_score", 0), reverse=True)
        return documents


class NemotronReranker:
    """Reranking via NVIDIA Nemotron rerank API (requires NVIDIA_API_KEY)."""

    def __init__(
        self,
        model_name: str = NEMOTRON_RERANK_MODEL,
        api_key: str | None = None,
        base_url: str = "https://ai.api.nvidia.com/v1/retrieval",
    ):
        self.model_name = model_name
        self.api_key = api_key or os.getenv("NVIDIA_API_KEY", "")
        self.base_url = base_url
        self._available = None

    def _check_available(self) -> bool:
        """Check if the Nemotron rerank API is reachable."""
        if self._available is not None:
            return self._available

        if not self.api_key:
            logger.warning("NVIDIA_API_KEY not set — Nemotron rerank unavailable")
            self._available = False
            return False

        try:
            import requests
            resp = requests.get(
                f"{self.base_url}/nvidia/nemotron-rerank-v1",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10,
            )
            self._available = resp.status_code in (200, 405)
        except Exception as e:
            logger.warning(f"Nemotron rerank health check failed: {e}")
            self._available = False

        return self._available

    def rerank(
        self, query: str, documents: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Rerank documents via Nemotron rerank API.

        Args:
            query: The search query
            documents: List of document dicts with at least 'document' key

        Returns:
            Same list with 'reranker_score' added, sorted by score desc
        """
        if not documents:
            return documents

        import requests

        if not self.api_key:
            raise ValueError("NVIDIA_API_KEY is required for Nemotron reranking")

        # Build passages list for the API
        passages = [doc.get("document", "") for doc in documents]

        resp = requests.post(
            f"{self.base_url}/nvidia/nemotron-rerank-v1",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model_name,
                "query": query,
                "passages": passages,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        # Parse scores from response
        ranked = data.get("rankings", data.get("data", []))
        if ranked and isinstance(ranked[0], dict) and "index" in ranked[0]:
            # Rankings format: [{"index": int, "score": float}, ...]
            score_map = {r["index"]: r.get("score", 0.0) for r in ranked}
        else:
            # Fallback: assume same order as input
            scores = data.get("scores", data.get("similarities", []))
            score_map = {i: s for i, s in enumerate(scores)}

        for i, doc in enumerate(documents):
            raw_score = score_map.get(i, 0.0)
            # Normalize to 0-1 range (Nemotron scores are typically 0-1 already)
            score = max(0.0, min(1.0, float(raw_score)))
            doc["reranker_score"] = round(score, 6)
            doc["score"] = doc["reranker_score"]
            doc["similarity_score"] = doc["reranker_score"]
            doc["reasons"] = [*doc.get("reasons", []), "nemotron-reranked"]

        documents.sort(key=lambda d: d.get("reranker_score", 0), reverse=True)
        return documents


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def get_rerank_provider(provider: str | None = None) -> LocalReranker | NemotronReranker:
    """
    Get the rerank provider based on configuration.

    Falls back to local if Nemotron is not available.
    """
    if provider is None:
        provider = os.getenv("HECTOR_RERANK_PROVIDER", "local")

    if provider == "nemotron":
        reranker = NemotronReranker(
            model_name=os.getenv("HECTOR_NEMOTRON_RERANK_MODEL", NEMOTRON_RERANK_MODEL),
        )
        if reranker._check_available():
            logger.info("Using Nemotron rerank provider")
            return reranker
        else:
            logger.warning("Nemotron rerank unavailable — falling back to local")
            return LocalReranker()

    return LocalReranker()
