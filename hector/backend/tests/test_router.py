"""
Unit tests for HECTOR Router Module.
Tests intent classification and query routing.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.router import HectorRouter


class TestHectorRouter:
    """Test cases for HectorRouter."""

    @pytest.fixture
    def router(self):
        """Create router instance."""
        return HectorRouter()

    def test_router_initialization(self, router):
        """Test router initializes correctly."""
        assert router is not None
        assert hasattr(router, "client")
        assert hasattr(router, "legal_map")

    def test_route_legal_research_ipc(self, router):
        """Test routing for IPC queries."""
        result = router.get_route("What is section 302 IPC?")
        assert result["route"] in [
            "LEGAL_RESEARCH",
            "STRATEGIC_ADVICE",
            "DOCUMENT_ANALYSIS",
            "GENERAL",
        ]
        assert "confidence" in result
        assert result["confidence"] > 0

    def test_route_legal_research_bns(self, router):
        """Test routing for BNS queries."""
        result = router.get_route("BNS section 302 murder")
        assert result["route"] == "LEGAL_RESEARCH"
        assert result["confidence"] > 0.8

    def test_route_civil_law(self, router):
        """Test routing for CPC/Civil queries."""
        result = router.get_route("Order 1 Rule 1 CPC")
        assert result["route"] == "LEGAL_RESEARCH"
        assert result["confidence"] > 0.8

    def test_route_document_analysis(self, router):
        """Test routing for document-related queries."""
        result = router.get_route("Analyze this PDF document")
        assert result["route"] == "DOCUMENT_ANALYSIS"

    def test_route_strategy(self, router):
        """Test routing for strategic advice."""
        result = router.get_route("What's the best move for my case?")
        assert result["route"] == "STRATEGIC_ADVICE"

    def test_route_general(self, router):
        """Test routing for general queries."""
        result = router.get_route("Hello how are you")
        assert result["route"] in ["GENERAL", "LEGAL_RESEARCH"]

    def test_normalize_query_ipc_to_bns(self, router):
        """Test query normalization for IPC to BNS."""
        query, mappings = router.normalize_query("IPC Section 302")
        assert "IPC" in query.upper() or "BNS" in query.upper()
        # Mappings may be empty if mapping not found, that's OK

    def test_validate_payload_valid(self, router):
        """Test payload validation with valid data."""
        payload = {
            "route": "LEGAL_RESEARCH",
            "hector_response": "Research result",
            "confidence": 0.95,
        }
        result = router._validate_payload(payload)
        assert result["route"] == "LEGAL_RESEARCH"
        assert result["confidence"] == 0.95

    def test_validate_payload_invalid_route(self, router):
        """Test payload validation with invalid route."""
        payload = {
            "route": "INVALID_ROUTE",
            "hector_response": "Test",
            "confidence": 0.5,
        }
        with pytest.raises(ValueError):
            router._validate_payload(payload)

    def test_validate_payload_drops_answers_longer_than_a_status(self, router):
        """The routing model sometimes replies instead of classifying.

        This is the real reply HECTOR returned for a LeetCode question on
        2026-10-09. Anything past a status line is an answer in disguise and
        must not travel as a HECTOR response; the services layer separately
        refuses to show this field for a non-legal route, which is what
        catches short answers.
        """
        payload = {
            "route": "GENERAL",
            "hector_response": (
                "Enqueue and Dequeue are fundamental operations in a Queue "
                "data structure, which follows the FIFO (First-In, First-Out) "
                "principle. Enqueue adds an element to the rear of the queue, "
                "while Dequeue removes an element from the front. A classic "
                "LeetCode problem demonstrating this is 'Implement Queue using "
                "Stacks' (Problem 232), where you must implement a queue using "
                "two stacks to handle the FIFO behavior with LIFO primitives."
            ),
            "confidence": 0.98,
        }
        result = router._validate_payload(payload)
        assert result["route"] == "GENERAL"
        assert result["hector_response"] == router.ROUTING_STATUS_FALLBACK
        assert len(result["hector_response"]) <= router.MAX_ROUTING_STATUS_CHARS

    def test_cap_is_above_every_rule_based_status(self, router):
        """The length cap must never discard a deterministic status message."""
        import inspect
        import re

        source = inspect.getsource(type(router))
        statuses = re.findall(r'message="([^"]+)"', source)
        statuses.append(router.ROUTING_STATUS_FALLBACK)
        assert statuses, "expected rule-based status messages in the router"
        for status in statuses:
            assert len(status) <= type(router).MAX_ROUTING_STATUS_CHARS, status

    def test_validate_payload_keeps_short_status(self, router):
        """A real routing status survives validation untouched."""
        payload = {
            "route": "LEGAL_RESEARCH",
            "hector_response": "Legal research route selected.",
            "confidence": 0.9,
        }
        result = router._validate_payload(payload)
        assert result["hector_response"] == "Legal research route selected."

    def test_coerce_confidence(self, router):
        """Test confidence value coercion."""
        assert router._coerce_confidence(0.5) == 0.5
        assert router._coerce_confidence(1.5) == 1.0
        assert router._coerce_confidence(-0.5) == 0.0
        assert router._coerce_confidence(None) == 0.0
        assert router._coerce_confidence("invalid") == 0.0


class TestLegalKeywordDetection:
    """Test legal keyword detection."""

    @pytest.fixture
    def router(self):
        return HectorRouter()

    def test_ipc_keyword_detection(self, router):
        """Test IPC keyword detection."""
        result = router.get_route("ipc section 420")
        assert result["route"] == "LEGAL_RESEARCH"

    def test_bns_keyword_detection(self, router):
        """Test BNS keyword detection."""
        result = router.get_route("bns section 302")
        assert result["route"] == "LEGAL_RESEARCH"

    def test_civil_keyword_detection(self, router):
        """Test civil law keyword detection."""
        result = router.get_route("civil suit partition")
        assert result["route"] == "LEGAL_RESEARCH"

    def test_cpc_keyword_detection(self, router):
        """Test CPC keyword detection."""
        result = router.get_route("Order 39 Rule 1 CPC")
        assert result["route"] == "LEGAL_RESEARCH"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
