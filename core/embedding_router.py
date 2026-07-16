"""
HECTOR Embedding-Based Router

Uses local embeddings + cosine similarity to classify query intent.
Faster and more accurate than keyword matching for paraphrased queries.

Pipeline:
1. Pre-computes route description embeddings on first use
2. Embeds the user query locally (~5ms)
3. Cosine similarity against route embeddings
4. Returns route with highest similarity score

Falls back gracefully if embedding model is unavailable.
"""

import logging
import os
import numpy as np
from typing import Optional

logger = logging.getLogger("hector.embedding_router")

# Route descriptions - rich text that captures the intent of each route
ROUTE_DESCRIPTIONS = {
    "LEGAL_RESEARCH": [
        "Indian law research, section lookup, act provisions, IPC BNS CRPC BNSS",
        "Legal question about punishment, offence, crime, bail, trial, appeal",
        "Statute interpretation, bare act, section 302, section 376, FIR",
        "Constitutional law, fundamental rights, Article 21, writ petition",
        "Civil law, contract, property, transfer, succession, inheritance",
        "Criminal law, murder, theft, assault, dowry, cruelty, NDPS",
        "Evidence law, admissibility, electronic evidence, confession",
        "Consumer protection, motor vehicles, industrial disputes, labour",
        "Family law, divorce, maintenance, custody, guardianship, adoption",
        "Legal remedy, compensation, damages, recovery, execution of decree",
    ],
    "STRATEGIC_ADVICE": [
        "Strategy, tactical advice, next steps, best approach, positioning",
        "Negotiation, settlement, attack, defend, argue, legal strategy",
        "What should I do next, how to approach, what is the best move",
        "Case strategy, litigation planning, dispute resolution approach",
    ],
    "DOCUMENT_ANALYSIS": [
        "Analyze this document, review this file, OCR this scan",
        "PDF upload, attachment, document inspection, evidence review",
        "Analyze contract, review agreement, check document",
        "Read this file, scan this document, extract text from image",
    ],
    "GENERAL": [
        "General question, not related to law or legal matters",
        "Weather, sports, cooking, travel, entertainment, technology",
        "Personal advice, relationship, health, fitness, finance",
        "Math, science, history, geography, general knowledge",
        "Coding, programming, software, hardware, internet",
    ],
}


class EmbeddingRouter:
    """
    Embedding-based intent router using cosine similarity.
    Uses the local sentence-transformers model for fast inference.
    """

    def __init__(self):
        self._embedder = None
        self._route_embeddings = {}
        self._route_names = list(ROUTE_DESCRIPTIONS.keys())
        self._initialized = False

    def _load_embedder(self):
        """Lazy-load the local embedding model."""
        if self._embedder is not None:
            return True

        try:
            from sentence_transformers import SentenceTransformer

            os.environ.setdefault("HF_HUB_OFFLINE", "1")
            self._embedder = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("Embedding router loaded local model (384d)")
            return True
        except Exception as e:
            logger.warning(f"Embedding router failed to load model: {e}")
            return False

    def _initialize_routes(self):
        """Pre-compute route description embeddings."""
        if self._initialized:
            return

        if not self._load_embedder():
            return

        for route, descriptions in ROUTE_DESCRIPTIONS.items():
            # Combine all descriptions into a single embedding
            combined = " ".join(descriptions)
            embedding = self._embedder.encode(combined, normalize_embeddings=True)
            self._route_embeddings[route] = embedding

        self._initialized = True
        logger.info(
            f"Embedding router initialized with {len(self._route_embeddings)} routes"
        )

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))

    def route(self, query: str) -> Optional[tuple[str, float]]:
        """
        Route a query using embedding similarity.

        Args:
            query: User's query text

        Returns:
            Tuple of (route_name, confidence) or None if unavailable
        """
        if not self._load_embedder():
            return None

        self._initialize_routes()

        if not self._initialized:
            return None

        # Embed the query
        query_embedding = self._embedder.encode(query, normalize_embeddings=True)

        # Find best matching route
        best_route = None
        best_score = -1.0

        for route, route_emb in self._route_embeddings.items():
            score = self._cosine_similarity(query_embedding, route_emb)
            if score > best_score:
                best_score = score
                best_route = route

        if best_route is None:
            return None

        # Normalize confidence to 0-1 range
        # Cosine similarity for normalized vectors is already 0-1 for positive similarities
        confidence = max(0.0, min(1.0, best_score))

        return (best_route, confidence)

    def get_route(self, query: str) -> Optional[str]:
        """Get just the route name."""
        result = self.route(query)
        return result[0] if result else None

    def get_confidence(self, query: str) -> float:
        """Get just the confidence score."""
        result = self.route(query)
        return result[1] if result else 0.0

    def explain(self, query: str) -> dict:
        """
        Get detailed routing explanation with scores for all routes.
        Useful for debugging and testing.
        """
        if not self._load_embedder():
            return {"error": "Embedding model unavailable"}

        self._initialize_routes()

        if not self._initialized:
            return {"error": "Routes not initialized"}

        query_embedding = self._embedder.encode(query, normalize_embeddings=True)

        scores = {}
        for route, route_emb in self._route_embeddings.items():
            scores[route] = round(
                self._cosine_similarity(query_embedding, route_emb), 4
            )

        best_route = max(scores, key=scores.get)

        return {
            "query": query,
            "best_route": best_route,
            "scores": scores,
            "confidence": scores[best_route],
        }


# Singleton
_embedding_router_instance = None


def get_embedding_router() -> EmbeddingRouter:
    """Get or create the singleton embedding router."""
    global _embedding_router_instance
    if _embedding_router_instance is None:
        _embedding_router_instance = EmbeddingRouter()
    return _embedding_router_instance


def route_by_embedding(query: str) -> Optional[str]:
    """Convenience function to route a query by embedding similarity."""
    return get_embedding_router().get_route(query)
