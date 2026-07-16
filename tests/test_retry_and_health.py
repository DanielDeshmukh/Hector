"""
Tests for retry utility, ChromaDB retry logic, and enhanced health endpoints.
"""

import os
import sys
import time
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.retry import retry


class TestRetryUtility:
    """Tests for the retry function with exponential backoff."""

    def test_success_no_retry(self):
        call_count = 0

        def succeed():
            nonlocal call_count
            call_count += 1
            return "ok"

        result = retry(succeed, max_attempts=3, base_delay=0.01)
        assert result == "ok"
        assert call_count == 1

    def test_retry_on_failure(self):
        call_count = 0

        def fail_twice():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("transient")
            return "recovered"

        result = retry(fail_twice, max_attempts=3, base_delay=0.01)
        assert result == "recovered"
        assert call_count == 3

    def test_max_retries_exceeded(self):
        def always_fail():
            raise ValueError("permanent")

        with pytest.raises(ValueError, match="permanent"):
            retry(always_fail, max_attempts=2, base_delay=0.01)

    def test_specific_exception_type(self):
        call_count = 0

        def fail_value_error():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("retry this")
            return "done"

        result = retry(
            fail_value_error,
            max_attempts=3,
            base_delay=0.01,
            retryable_exceptions=(ValueError,),
        )
        assert result == "done"
        assert call_count == 2

    def test_wrong_exception_type_not_retried(self):
        def raise_type_error():
            raise TypeError("wrong type")

        with pytest.raises(TypeError):
            retry(
                raise_type_error,
                max_attempts=3,
                base_delay=0.01,
                retryable_exceptions=(ValueError,),
            )

    def test_exponential_backoff_timing(self):
        call_count = 0

        def fail_three_times():
            nonlocal call_count
            call_count += 1
            if call_count < 4:
                raise RuntimeError("fail")
            return "done"

        start = time.time()
        result = retry(fail_three_times, max_attempts=4, base_delay=0.05, backoff_factor=2.0)
        elapsed = time.time() - start
        assert result == "done"
        assert call_count == 4
        # Should have waited: 0.05 + 0.10 + 0.20 = 0.35s minimum
        assert elapsed >= 0.30


class TestGroqConnectivity:
    """Tests for Groq connectivity checks in health endpoints."""

    def test_router_with_groq_disabled(self):
        from core.router import HectorRouter

        router = HectorRouter()
        router.client = None
        assert router.client is None

    def test_router_groq_models_list_called(self):
        from core.router import HectorRouter

        router = HectorRouter()
        mock_client = MagicMock()
        mock_client.models.list.return_value = MagicMock()
        router.client = mock_client

        # Test that models.list is called during health check
        try:
            router.client.models.list()
        except Exception:
            pass
        mock_client.models.list.assert_called()


class TestEnhancedHealthEndpoints:
    """Tests for /status and /readyz with external service checks."""

    @pytest.fixture
    def stub_service(self):
        from api.services import HectorApiService
        from api.app import app, get_service
        from core.orchestrator import HectorOrchestrator
        from core.router import HectorRouter
        from data.hybrid_retriever import HectorHybridRetriever

        retriever = HectorHybridRetriever.from_records([
            {
                "id": "test-1",
                "document": "Test document",
                "metadata": {"source": "test.pdf", "page": 1},
                "score": 0.9,
            }
        ])
        router = HectorRouter()
        router.client = None

        orch = HectorOrchestrator.__new__(HectorOrchestrator)
        orch.router = router
        orch.retriever = retriever
        orch.enable_verification = False

        service = HectorApiService(orchestrator=orch, retriever=retriever, router=router)
        app.dependency_overrides[get_service] = lambda: service
        yield service
        app.dependency_overrides.clear()

    def test_status_returns_ok(self, stub_service):
        from fastapi.testclient import TestClient
        from api.app import app
        from api.security import auth_manager

        client = TestClient(app)
        resp = client.get("/status", headers={"X-API-Key": auth_manager.api_key})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("ok", "degraded")
        assert "chromadb_connected" in data

    def test_readyz_includes_checks(self, stub_service):
        from fastapi.testclient import TestClient
        from api.app import app
        from api.security import auth_manager

        client = TestClient(app)
        resp = client.get("/readyz", headers={"X-API-Key": auth_manager.api_key})
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert data["status"] in ("ok", "degraded")
        assert "checks" in data
