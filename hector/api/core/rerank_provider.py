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

import json
import logging
import math
import os
from typing import Any

logger = logging.getLogger("hector.rerank")

# Default models
LOCAL_CROSS_ENCODER = "cross-encoder/ms-marco-MiniLM-L-6-v2"
NEMOTRON_RERANK_MODEL = "nvidia/nemotron-rerank-v1"

# Shared cache of loaded cross-encoder models so each new provider instance
# reuses an already-loaded model instead of reloading from disk per query.
_shared_cross_encoders: dict[str, Any] = {}


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
        cached = _shared_cross_encoders.get(self.model_name)
        if cached is not None:
            self._model = cached
            return
        try:
            from sentence_transformers import CrossEncoder

            os.environ.setdefault("HF_HUB_OFFLINE", "1")
            self._model = CrossEncoder(self.model_name)
            _shared_cross_encoders[self.model_name] = self._model
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
        base_url: str | None = None,
    ):
        self.model_name = model_name
        self.api_key = (
            api_key
            or os.getenv("NVIDIA_API_KEY", "")
            or os.getenv("NIM_API_KEY", "")
        )
        if base_url:
            self.base_url = base_url
        else:
            raw = os.getenv("NIM_BASE_URL", "https://ai.api.nvidia.com/v1")
            self.base_url = raw.rstrip("/") + "/retrieval"
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
            import httpx

            resp = httpx.get(
                f"{self.base_url}/nvidia/nemotron-rerank-v1",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10,
            )
            self._available = resp.status_code in (200, 405)
            if not self._available:
                logger.warning(
                    f"Nemotron health check returned {resp.status_code}: "
                    f"{resp.text[:200]}"
                )
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

        import httpx

        if not self.api_key:
            raise ValueError("NVIDIA_API_KEY is required for Nemotron reranking")

        # Build passages list for the API (truncate long docs)
        passages = []
        for doc in documents:
            text = doc.get("document", "")
            if len(text) > 512:
                text = text[:512] + "..."
            passages.append(text)

        resp = httpx.post(
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
        logger.info(
            f"Nemotron rerank returned {len(data.get('rankings', []))} rankings "
            f"for {len(documents)} passages"
        )

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


class GroqReranker:
    """Reranking via Groq chat model with JSON scoring.

    Works on Vercel: no local weights, uses the already-deployed GROQ_API_KEY.
    The model sees the query plus every candidate passage and returns a
    0-100 relevance score per passage id; scores are normalized to 0-1.
    """

    def __init__(
        self,
        model_name: str | None = None,
        api_key: str | None = None,
    ):
        self.model_name = model_name or os.getenv(
            "HECTOR_GROQ_RERANK_MODEL", "qwen/qwen3.8-27b"
        )
        self.api_key = api_key or os.getenv("GROQ_API_KEY", "")

    def _check_available(self) -> bool:
        if not self.api_key:
            logger.warning("GROQ_API_KEY not set — Groq rerank unavailable")
            return False
        return True

    def rerank(
        self, query: str, documents: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        if not documents:
            return documents
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is required for Groq reranking")

        from groq import Groq

        client = Groq(api_key=self.api_key)
        passages = []
        for doc in documents:
            text = doc.get("document", "")
            if len(text) > 200:
                text = text[:200] + "..."
            # Positional numbering keeps the model's output tiny
            # (~150 tokens instead of ~900 for an id->score map), which
            # matters because Groq enforces a 1000 output-TPM pre-flight
            # limit on this model.
            passages.append(text)

        numbered = "\n".join(
            f"{i + 1}. {text}" for i, text in enumerate(passages)
        )
        user_prompt = (
            f"Query: {query}\n\nPassages:\n{numbered}\n\n"
            "Respond ONLY with JSON: {\"scores\":[<0-100>, ...]} — one integer "
            "per passage, in the same order. Higher = more relevant to the "
            "query. Output JSON only, no reasoning, no commentary."
        )
        response = client.chat.completions.create(
            model=self.model_name,
            temperature=0,
            max_tokens=400,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": "You are a legal passage relevance reranker. "
                    "Score how useful each passage is for answering the query. "
                    "Output strict JSON only.",
                },
                {"role": "user", "content": user_prompt},
            ],
        )
        payload = json.loads(response.choices[0].message.content or "{}")

        # Accept {"scores":[...]} positional, numeric-keyed maps, and
        # legacy id->score maps (some models drop the wrapper).
        positional: list[float] = []
        scores = payload.get("scores") if isinstance(payload, dict) else None
        id_scores: dict[str, Any] = {}
        if isinstance(scores, list):
            positional = scores
        elif isinstance(scores, dict):
            id_scores = {str(k): v for k, v in scores.items()}
        elif isinstance(payload, dict):
            numeric_keys = sorted(
                (k for k in payload if str(k).isdigit()),
                key=lambda k: int(k),
            )
            if numeric_keys and len(numeric_keys) >= len(payload) // 2:
                positional = [payload[k] for k in numeric_keys]
            else:
                id_scores = {
                    str(k): v for k, v in payload.items()
                    if isinstance(v, (int, float))
                }

        def _as_score(value) -> float:
            try:
                return max(0.0, min(1.0, float(value) / 100.0))
            except (TypeError, ValueError):
                return 0.0

        for index, doc in enumerate(documents):
            if index < len(positional):
                score = _as_score(positional[index])
            else:
                raw = id_scores.get(str(doc.get("id", "")))
                # Unparsed entries keep their retrieval-derived score
                # instead of collapsing to 0.0.
                score = _as_score(raw) if raw is not None else _as_score(
                    float(doc.get("hybrid_score") or doc.get("pre_rerank_score") or 0.0)
                )
            doc["reranker_score"] = round(score, 6)
            doc["score"] = doc["reranker_score"]
            doc["similarity_score"] = doc["reranker_score"]
            doc["reasons"] = [*doc.get("reasons", []), "groq-reranked"]

        documents.sort(key=lambda d: d.get("reranker_score", 0), reverse=True)
        return documents


class NimReranker:
    """NeMo Retriever NIM 2.x rerank API (hosted, purpose-built cross-encoder).

    Target: nvidia/llama-nemotron-rerank-vl-1b-v2 on ai.api.nvidia.com —
    the current production endpoint of NVIDIA's rerank line (the older
    /retrieval/nv-rerankqa-* endpoints are 410 EOL). Native logits, no
    JSON prompting, ~1s latency, works with the existing NIM_API_KEY.
    """

    DEFAULT_URL = (
        "https://ai.api.nvidia.com/v1/retrieval"
        "/nvidia/llama-nemotron-rerank-vl-1b-v2/reranking"
    )

    def __init__(
        self,
        model_name: str | None = None,
        api_key: str | None = None,
        url: str | None = None,
    ):
        self.model_name = model_name or os.getenv(
            "HECTOR_NIM_RERANK_MODEL",
            "nvidia/llama-nemotron-rerank-vl-1b-v2",
        )
        self.api_key = api_key or os.getenv(
            "NIM_API_KEY", ""
        ) or os.getenv("NVIDIA_API_KEY", "")
        self.url = url or os.getenv("HECTOR_NIM_RERANK_URL") or self.DEFAULT_URL

    def _check_available(self) -> bool:
        if not self.api_key:
            logger.warning("NIM_API_KEY not set — NIM rerank unavailable")
            return False
        return True

    def rerank(
        self, query: str, documents: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        if not documents:
            return documents
        if not self.api_key:
            raise ValueError("NIM_API_KEY is required for NIM reranking")

        import httpx

        passages = []
        for doc in documents:
            text = doc.get("document", "")
            if len(text) > 1000:
                text = text[:1000] + "..."
            passages.append({"text": text})

        resp = httpx.post(
            self.url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json={
                "model": self.model_name,
                "query": {"text": query},
                "passages": passages,
                "truncate": "END",
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        rankings = data.get("rankings") or data.get("results") or []

        raw_scores: dict[int, float] = {}
        for rank in rankings:
            if isinstance(rank, dict) and "index" in rank:
                raw = rank.get("logit")
                if raw is None:
                    raw = rank.get("relevance_score", rank.get("score", 0.0))
                raw_scores[int(rank["index"])] = float(raw)

        # NIM logits are uncalibrated and often deeply negative (-4 to -10)
        # even for perfect matches; a plain sigmoid then lands at ~0.009 and
        # the relevance floor (0.06) drops the entire result set. Min-max
        # normalize within the batch (monotonic => order preserved) and sqrt
        # squash so runner-ups stay above downstream similarity cutoffs,
        # matching the cross-encoder's calibrated 0-1 range.
        values = list(raw_scores.values())
        lo = min(values) if values else 0.0
        hi = max(values) if values else 0.0
        span = hi - lo

        def _norm(logit: float) -> float:
            if span < 1e-9:
                return _sigmoid(logit)
            return max(0.0, min(1.0, math.sqrt((logit - lo) / span)))

        for i, doc in enumerate(documents):
            if i in raw_scores:
                score = _norm(raw_scores[i])
            else:
                # Unparsed entries keep their retrieval-derived score
                # instead of collapsing to 0.0.
                score = _sigmoid(
                    float(
                        doc.get("hybrid_score")
                        or doc.get("pre_rerank_score")
                        or 0.0
                    )
                )
            doc["reranker_score"] = round(score, 6)
            doc["score"] = doc["reranker_score"]
            doc["similarity_score"] = doc["reranker_score"]
            doc["reasons"] = [*doc.get("reasons", []), "nim-reranked"]

        documents.sort(key=lambda d: d.get("reranker_score", 0), reverse=True)
        return documents


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def get_rerank_provider(
    provider: str | None = None,
) -> LocalReranker | NemotronReranker | GroqReranker | NimReranker:
    """
    Get the rerank provider based on configuration.

    Falls back to local if the requested API provider is not available.
    """
    if provider is None:
        provider = os.getenv("HECTOR_RERANK_PROVIDER", "local")

    if provider == "nim":
        reranker = NimReranker()
        if reranker._check_available():
            logger.info("Using NIM rerank provider")
            return reranker
        logger.warning("NIM rerank unavailable — falling back to local")
        return LocalReranker()

    if provider == "groq":
        reranker = GroqReranker()
        if reranker._check_available():
            logger.info("Using Groq rerank provider")
            return reranker
        logger.warning("Groq rerank unavailable — falling back to local")
        return LocalReranker()

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


def warmup_reranker(provider: str | None = None) -> bool:
    """
    Pre-load the reranker (and its model weights) before the first query so
    search latency does not include model-load time.

    Returns True when warmup completed (or the provider needs no loading).
    """
    try:
        if provider is None:
            provider = os.getenv("HECTOR_RERANK_PROVIDER", "nemotron")
        reranker = get_rerank_provider(provider)
        if isinstance(reranker, LocalReranker):
            reranker._load()
            logger.info("Reranker warm-up complete: %s", reranker.model_name)
        else:
            logger.info("Reranker warm-up complete: %s (API)", reranker.model_name)
        return True
    except Exception as exc:
        logger.warning("Reranker warm-up failed: %s", exc)
        return False
