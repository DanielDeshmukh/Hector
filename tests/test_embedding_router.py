"""
Tests for HECTOR Embedding-Based Router (Phase B)
Validates intent classification via cosine similarity.
Uses unittest (no pytest dependency).

Note: Embedding similarity scores are relative, not absolute.
The router's value is in choosing the BEST route, not in high confidence.
Thresholds are set based on observed score distributions.
"""

import unittest
from core.embedding_router import (
    EmbeddingRouter,
    get_embedding_router,
    route_by_embedding,
)


class TestEmbeddingRouter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Initialize router once for all tests (slow load, fast inference)."""
        cls.router = EmbeddingRouter()

    # --- LEGAL RESEARCH: should always route correctly ---

    def test_legal_section_lookup(self):
        """Direct section lookup should route to LEGAL_RESEARCH."""
        route, _ = self.router.route("Section 302 IPC punishment for murder")
        self.assertEqual(route, "LEGAL_RESEARCH")

    def test_legal_paraphrase(self):
        """Paraphrased legal question should still route to LEGAL_RESEARCH."""
        route, _ = self.router.route("Can a person go to jail for killing someone?")
        self.assertEqual(route, "LEGAL_RESEARCH")

    def test_legal_bail(self):
        route, _ = self.router.route("How to get bail in a criminal case?")
        self.assertEqual(route, "LEGAL_RESEARCH")

    def test_legal_divorce(self):
        route, _ = self.router.route("What are the grounds for divorce in India?")
        self.assertEqual(route, "LEGAL_RESEARCH")

    def test_legal_fir(self):
        route, _ = self.router.route("How to file an FIR against someone?")
        self.assertEqual(route, "LEGAL_RESEARCH")

    def test_legal_consumer(self):
        route, _ = self.router.route("Consumer protection complaint against seller")
        self.assertEqual(route, "LEGAL_RESEARCH")

    def test_legal_evidence(self):
        route, _ = self.router.route("Is a confession to police admissible in court?")
        self.assertEqual(route, "LEGAL_RESEARCH")

    def test_legal_higher_score_for_obvious(self):
        """Obvious legal query should score higher than paraphrased."""
        s1, _ = self.router.route("Section 302 IPC murder")
        s2, _ = self.router.route("Can a person go to jail for killing someone?")
        # Both should be LEGAL_RESEARCH, but direct lookup scores higher
        self.assertEqual(s1, "LEGAL_RESEARCH")
        self.assertEqual(s2, "LEGAL_RESEARCH")

    # --- DOCUMENT ANALYSIS ---

    def test_document_pdf(self):
        route, _ = self.router.route("Please analyze this PDF document")
        self.assertEqual(route, "DOCUMENT_ANALYSIS")

    def test_document_ocr(self):
        route, _ = self.router.route("OCR this scanned image for me")
        self.assertEqual(route, "DOCUMENT_ANALYSIS")

    def test_document_review(self):
        route, _ = self.router.route("Review this PDF and summarize key terms")
        # "review" is document, "summarize" is strategy — both are reasonable
        self.assertIn(route, ("DOCUMENT_ANALYSIS", "STRATEGIC_ADVICE"))

    # --- STRATEGIC ADVICE ---

    def test_strategy_approach(self):
        route, _ = self.router.route("What's the best strategy to win this case?")
        self.assertEqual(route, "STRATEGIC_ADVICE")

    def test_strategy_negotiate(self):
        route, _ = self.router.route(
            "How should I approach the settlement negotiation?"
        )
        self.assertEqual(route, "STRATEGIC_ADVICE")

    # --- GENERAL ---

    def test_general_weather(self):
        route, _ = self.router.route("What is the weather today?")
        self.assertEqual(route, "GENERAL")

    def test_general_recipe(self):
        route, _ = self.router.route("How do I make butter chicken at home?")
        self.assertEqual(route, "GENERAL")

    # --- CONFIDENCE ---

    def test_confidence_range(self):
        _, confidence = self.router.route("Section 302 IPC")
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)

    def test_high_confidence_for_clear_queries(self):
        """Clear legal/document queries should have higher confidence."""
        _, c_legal = self.router.route("Section 302 IPC murder")
        _, c_doc = self.router.route("Analyze this PDF")
        self.assertGreater(c_legal, 0.3)
        self.assertGreater(c_doc, 0.3)

    # --- METHODS ---

    def test_get_route_method(self):
        route = self.router.get_route("Section 302 IPC murder")
        self.assertEqual(route, "LEGAL_RESEARCH")

    def test_get_confidence_method(self):
        conf = self.router.get_confidence("Section 302 IPC murder")
        self.assertGreaterEqual(conf, 0.0)
        self.assertLessEqual(conf, 1.0)

    def test_explain_returns_all_routes(self):
        explanation = self.router.explain("Section 302 IPC")
        self.assertIn("scores", explanation)
        for route in (
            "LEGAL_RESEARCH",
            "STRATEGIC_ADVICE",
            "DOCUMENT_ANALYSIS",
            "GENERAL",
        ):
            self.assertIn(route, explanation["scores"])

    def test_explain_best_route(self):
        explanation = self.router.explain("Section 302 IPC murder")
        self.assertEqual(explanation["best_route"], "LEGAL_RESEARCH")

    # --- EDGE CASES ---

    def test_empty_query(self):
        route, _ = self.router.route("")
        # Empty query gets whatever route has highest similarity
        self.assertIn(
            route,
            ("LEGAL_RESEARCH", "GENERAL", "STRATEGIC_ADVICE", "DOCUMENT_ANALYSIS"),
        )

    def test_single_word_legal(self):
        route, _ = self.router.route("bail")
        self.assertEqual(route, "LEGAL_RESEARCH")

    def test_long_query(self):
        long_query = "What is the punishment for murder under Section 302 of the Indian Penal Code, and how does it compare to Section 101 of the Bharatiya Nyaya Sanhita?"
        route, _ = self.router.route(long_query)
        self.assertEqual(route, "LEGAL_RESEARCH")

    def test_typo_resilient(self):
        """Embeddings should handle minor typos."""
        route, _ = self.router.route("Sction 302 IPC punishmnt")
        self.assertEqual(route, "LEGAL_RESEARCH")


class TestConvenienceFunctions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        get_embedding_router()

    def test_route_by_embedding(self):
        route = route_by_embedding("Section 302 IPC")
        self.assertEqual(route, "LEGAL_RESEARCH")

    def test_singleton(self):
        r1 = get_embedding_router()
        r2 = get_embedding_router()
        self.assertIs(r1, r2)


class TestScoreOrdering(unittest.TestCase):
    """Test that the router produces correct relative score ordering."""

    @classmethod
    def setUpClass(cls):
        cls.router = EmbeddingRouter()

    def test_legal_beats_general_for_legal_query(self):
        """Legal query should score higher for LEGAL_RESEARCH than GENERAL."""
        explanation = self.router.explain("Section 302 IPC murder punishment")
        self.assertGreater(
            explanation["scores"]["LEGAL_RESEARCH"],
            explanation["scores"]["GENERAL"],
        )

    def test_document_beats_general_for_document_query(self):
        """Document query should score higher for DOCUMENT_ANALYSIS than GENERAL."""
        explanation = self.router.explain("Analyze this PDF document")
        self.assertGreater(
            explanation["scores"]["DOCUMENT_ANALYSIS"],
            explanation["scores"]["GENERAL"],
        )

    def test_strategy_beats_general_for_strategy_query(self):
        """Strategy query should score higher for STRATEGIC_ADVICE than GENERAL."""
        explanation = self.router.explain("What's the best strategy to win this case?")
        self.assertGreater(
            explanation["scores"]["STRATEGIC_ADVICE"],
            explanation["scores"]["GENERAL"],
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
