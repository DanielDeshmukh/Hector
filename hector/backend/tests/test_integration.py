"""
Integration tests for HECTOR search/compare pipeline.
Tests full API → service → retriever → response flow with mocked external deps.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.app import app, cache, get_service
from api.security import auth_manager
from api.services import HectorApiService
from core.router import HectorRouter
from data.hybrid_retriever import HectorHybridRetriever


# ---------------------------------------------------------------------------
# Sample corpus for in-memory retriever
# ---------------------------------------------------------------------------

SAMPLE_RECORDS = [
    {
        "id": "ipc-302",
        "document": "Section 302 IPC. Punishment for murder.",
        "metadata": {
            "source": "IPC.pdf",
            "page": 100,
            "act_name": "IPC",
            "section_number": "302",
        },
        "score": 0.95,
        "act": "IPC",
        "citation": {"section": "302", "page": 100, "source": "IPC.pdf"},
        "reasons": ["citation-match:IPC-302"],
    },
    {
        "id": "bns-103",
        "document": "Section 103 BNS. Punishment for murder.",
        "metadata": {
            "source": "BNS.pdf",
            "page": 50,
            "act_name": "BNS",
            "section_number": "103",
        },
        "score": 0.92,
        "act": "BNS",
        "citation": {"section": "103", "page": 50, "source": "BNS.pdf"},
        "reasons": ["citation-match:BNS-103"],
    },
    {
        "id": "ipc-376",
        "document": "Section 376 IPC. Punishment for rape.",
        "metadata": {
            "source": "IPC.pdf",
            "page": 150,
            "act_name": "IPC",
            "section_number": "376",
        },
        "score": 0.88,
        "act": "IPC",
        "citation": {"section": "376", "page": 150, "source": "IPC.pdf"},
        "reasons": ["citation-match:IPC-376"],
    },
    {
        "id": "bns-63",
        "document": "Section 63 BNS. Punishment for rape.",
        "metadata": {
            "source": "BNS.pdf",
            "page": 30,
            "act_name": "BNS",
            "section_number": "63",
        },
        "score": 0.85,
        "act": "BNS",
        "citation": {"section": "63", "page": 30, "source": "BNS.pdf"},
        "reasons": ["citation-match:BNS-63"],
    },
    {
        "id": "crpc-154",
        "document": "Section 154 CrPC. Information in cognizable cases.",
        "metadata": {
            "source": "CrPC.pdf",
            "page": 80,
            "act_name": "CRPC",
            "section_number": "154",
        },
        "score": 0.80,
        "act": "CRPC",
        "citation": {"section": "154", "page": 80, "source": "CrPC.pdf"},
        "reasons": ["citation-match:CrPC-154"],
    },
]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def router():
    """Router with Groq disabled (forces rule-based routing)."""
    r = HectorRouter()
    r.client = None  # force rule-based fallback
    return r


@pytest.fixture(scope="module")
def retriever():
    """In-memory retriever from sample records (no ChromaDB)."""
    return HectorHybridRetriever.from_records(SAMPLE_RECORDS)


@pytest.fixture(scope="module")
def service(router, retriever):
    """HectorApiService wired with mocked deps."""
    from core.orchestrator import HectorOrchestrator

    orch = HectorOrchestrator.__new__(HectorOrchestrator)
    orch.router = router
    orch.retriever = retriever
    orch.enable_verification = False
    return HectorApiService(orchestrator=orch, retriever=retriever, router=router)


@pytest.fixture
def stub_service(service):
    """Override the app's service dependency."""
    from core.query_cache import get_query_cache
    previous = app.dependency_overrides.get(get_service)
    app.dependency_overrides[get_service] = lambda: service
    get_query_cache().clear()
    yield
    if previous is not None:
        app.dependency_overrides[get_service] = previous
    else:
        app.dependency_overrides.pop(get_service, None)
    cache.clear()
    get_query_cache().clear()


@pytest.fixture
def auth():
    return {"X-API-Key": auth_manager.api_key}


# ---------------------------------------------------------------------------
# Search pipeline integration tests
# ---------------------------------------------------------------------------


class TestSearchPipeline:
    """Full search pipeline: API endpoint → service → retriever → response."""

    def test_search_legal_query_returns_results(self, stub_service, auth):
        from fastapi.testclient import TestClient

        client = TestClient(app)
        resp = client.post(
            "/search",
            headers=auth,
            json={
                "query": "Section 302 IPC murder punishment",
                "page": 1,
                "page_size": 5,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["route"] == "LEGAL_RESEARCH"
        assert data["total_results"] > 0
        assert len(data["items"]) > 0
        assert data["query"] == "Section 302 IPC murder punishment"

    def test_search_returns_correct_items(self, stub_service, auth):
        from fastapi.testclient import TestClient

        client = TestClient(app)
        resp = client.post(
            "/search",
            headers=auth,
            json={"query": "Section 302 IPC", "page": 1, "page_size": 10},
        )
        data = resp.json()
        ids = [item["id"] for item in data["items"]]
        assert len(ids) > 0

    def test_search_pagination(self, stub_service, auth):
        from fastapi.testclient import TestClient

        client = TestClient(app)
        resp = client.post(
            "/search",
            headers=auth,
            json={"query": "Section 302 IPC", "page": 1, "page_size": 2},
        )
        data = resp.json()
        assert len(data["items"]) <= 2
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert data["total_pages"] >= 1

    def test_search_caching(self, stub_service, auth):
        from fastapi.testclient import TestClient

        client = TestClient(app)
        req = {"query": "Section 302 IPC murder", "page": 1, "page_size": 5}
        first = client.post("/search", headers=auth, json=req).json()
        second = client.post("/search", headers=auth, json=req).json()
        assert second.get("cached") is True
        assert first["items"] == second["items"]

    def test_search_response_has_confidence(self, stub_service, auth):
        from fastapi.testclient import TestClient

        client = TestClient(app)
        resp = client.post(
            "/search",
            headers=auth,
            json={"query": "Section 302 IPC", "page": 1, "page_size": 5},
        )
        data = resp.json()
        assert "confidence_level" in data
        assert data["confidence_level"] in ("high", "medium", "low", "unknown")

    def test_search_response_has_pipeline(self, stub_service, auth):
        from fastapi.testclient import TestClient

        client = TestClient(app)
        resp = client.post(
            "/search",
            headers=auth,
            json={"query": "What is murder under IPC?", "page": 1, "page_size": 5},
        )
        data = resp.json()
        assert "generated_response" in data

    def test_search_general_route(self, stub_service, auth):
        from fastapi.testclient import TestClient

        client = TestClient(app)
        resp = client.post(
            "/search",
            headers=auth,
            json={"query": "hello world", "page": 1, "page_size": 5},
        )
        data = resp.json()
        assert data["route"] == "GENERAL"

    def test_search_empty_results(self, stub_service, auth):
        from fastapi.testclient import TestClient

        client = TestClient(app)
        resp = client.post(
            "/search",
            headers=auth,
            json={"query": "quantum computing", "page": 1, "page_size": 5},
        )
        data = resp.json()
        assert data["total_results"] == 0
        assert data["items"] == []

    def test_search_returns_sources_with_metadata(self, stub_service, auth):
        from fastapi.testclient import TestClient

        client = TestClient(app)
        resp = client.post(
            "/search",
            headers=auth,
            json={"query": "Section 302 IPC murder", "page": 1, "page_size": 5},
        )
        data = resp.json()
        for item in data["items"]:
            assert "id" in item
            assert "document" in item
            assert "metadata" in item
            assert "snippet" in item


# ---------------------------------------------------------------------------
# Route endpoint integration tests
# ---------------------------------------------------------------------------


class TestRoutePipeline:
    """Route endpoint: API → router → response."""

    def test_route_legal_research(self, stub_service, auth):
        from fastapi.testclient import TestClient

        client = TestClient(app)
        resp = client.post(
            "/route",
            headers=auth,
            json={"query": "Section 302 IPC murder"},
        )
        data = resp.json()
        assert data["route"] == "LEGAL_RESEARCH"
        assert data["confidence"] >= 0.9

    def test_route_general(self, stub_service, auth):
        from fastapi.testclient import TestClient

        client = TestClient(app)
        resp = client.post(
            "/route",
            headers=auth,
            json={"query": "hello world"},
        )
        data = resp.json()
        assert data["route"] == "GENERAL"

    def test_route_returns_normalized_query(self, stub_service, auth):
        from fastapi.testclient import TestClient

        client = TestClient(app)
        resp = client.post(
            "/route",
            headers=auth,
            json={"query": "Section 302 IPC"},
        )
        data = resp.json()
        assert data["route"] == "LEGAL_RESEARCH"
        assert data.get("normalized_query") is not None


# ---------------------------------------------------------------------------
# Compare endpoint integration tests
# ---------------------------------------------------------------------------


class TestComparePipeline:
    """Compare endpoint: API → service → retriever → response."""

    def test_compare_ipc_to_bns(self, stub_service, auth):
        from fastapi.testclient import TestClient

        client = TestClient(app)
        resp = client.post(
            "/compare",
            headers=auth,
            json={"section": "302", "act": "IPC", "page_size": 5},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["requested_act"] == "IPC"
        assert data["requested_section"] == "302"
        assert data["counterpart_act"] == "BNS"
        # IPC 302 maps to BNS 101 per mapping.json
        assert data["counterpart_section"] == "101"
        assert data["note"] == "intentional killing"

    def test_compare_returns_results(self, stub_service, auth):
        from fastapi.testclient import TestClient

        client = TestClient(app)
        resp = client.post(
            "/compare",
            headers=auth,
            json={"section": "302", "act": "IPC", "page_size": 5},
        )
        data = resp.json()
        assert len(data["requested_results"]) > 0
        assert len(data["counterpart_results"]) > 0

    def test_compare_bns_to_ipc(self, stub_service, auth):
        from fastapi.testclient import TestClient

        client = TestClient(app)
        resp = client.post(
            "/compare",
            headers=auth,
            json={"section": "103", "act": "BNS", "page_size": 5},
        )
        data = resp.json()
        assert data["requested_act"] == "BNS"
        assert data["requested_section"] == "103"
        assert data["counterpart_act"] == "IPC"
        # BNS 103 maps to IPC 304 (Death by Negligence) per mapping.json
        assert data["counterpart_section"] is not None
        assert len(data["requested_results"]) > 0
        assert len(data["counterpart_results"]) > 0


# ---------------------------------------------------------------------------
# Status endpoint integration tests
# ---------------------------------------------------------------------------


class TestStatusPipeline:
    """Status endpoint: API → service → retriever → response."""

    def test_status_returns_ok(self, stub_service, auth):
        from fastapi.testclient import TestClient

        client = TestClient(app)
        resp = client.get("/status", headers=auth)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("ok", "degraded")
        assert data["document_count"] == len(SAMPLE_RECORDS)

    def test_status_has_cache_metrics(self, stub_service, auth):
        from fastapi.testclient import TestClient

        client = TestClient(app)
        resp = client.get("/status", headers=auth)
        data = resp.json()
        assert "cache" in data
        assert "hit_rate_percent" in data["cache"]


# ---------------------------------------------------------------------------
# Health endpoint integration tests
# ---------------------------------------------------------------------------


class TestHealthPipeline:
    """Health endpoints: liveness and readiness probes."""

    def test_healthz(self):
        from fastapi.testclient import TestClient

        client = TestClient(app)
        resp = client.get("/healthz")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_readyz(self, stub_service):
        from fastapi.testclient import TestClient

        client = TestClient(app)
        resp = client.get("/readyz")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("ok", "degraded")


# ---------------------------------------------------------------------------
# Auth integration tests
# ---------------------------------------------------------------------------


class TestAuthPipeline:
    """Authentication flow: API key → JWT → authenticated request."""

    def test_token_generation(self, stub_service):
        from fastapi.testclient import TestClient

        client = TestClient(app)
        resp = client.post(
            f"/auth/token?api_key={auth_manager.api_key}",
            headers={"X-API-Key": auth_manager.api_key},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["expires_in"] > 0

    def test_token_auth_search(self, stub_service):
        from fastapi.testclient import TestClient

        client = TestClient(app)
        # Get token
        token_resp = client.post(
            f"/auth/token?api_key={auth_manager.api_key}",
            headers={"X-API-Key": auth_manager.api_key},
        )
        token = token_resp.json()["access_token"]

        # Search with token
        resp = client.post(
            "/search",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "Section 302 IPC", "page": 1, "page_size": 2},
        )
        assert resp.status_code == 200

    def test_invalid_api_key_rejected(self):
        from fastapi.testclient import TestClient

        client = TestClient(app)
        resp = client.get("/status", headers={"X-API-Key": "wrong-key"})
        assert resp.status_code == 401

    def test_no_auth_rejected(self):
        from fastapi.testclient import TestClient

        client = TestClient(app)
        resp = client.get("/status")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Rate limit integration tests
# ---------------------------------------------------------------------------


class TestRateLimitPipeline:
    """Rate limiting: headers and enforcement."""

    def test_rate_limit_headers_present(self, stub_service, auth):
        from fastapi.testclient import TestClient

        client = TestClient(app)
        resp = client.get("/status", headers=auth)
        assert "X-RateLimit-Limit" in resp.headers
        assert "X-RateLimit-Remaining" in resp.headers
        assert "X-RateLimit-Reset" in resp.headers
        assert int(resp.headers["X-RateLimit-Limit"]) > 0
        assert int(resp.headers["X-RateLimit-Remaining"]) >= 0
