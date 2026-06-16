import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from api.app import app, cache, get_service
from api.security import auth_manager
from api.services import HectorApiService


class StubRouter:
    def __init__(self):
        self.model = "stub-router"
        self.legal_map = {
            "302": {"new": "103", "name": "Murder", "note": "homicide mapping"},
        }

    def get_route(self, query):
        lowered = query.lower()
        if "section" in lowered or "ipc" in lowered or "bns" in lowered:
            return {
                "route": "LEGAL_RESEARCH",
                "hector_response": "Legal route selected.",
                "confidence": 0.98,
            }
        return {
            "route": "GENERAL",
            "hector_response": "General route selected.",
            "confidence": 0.75,
        }

    def normalize_query(self, query):
        if "302" in query:
            return f"{query} Murder BNS 103", ["BNS Section 103 (Murder)"]
        return query, []


class StubRetriever:
    def __init__(self):
        self.collection_name = "stub_collection"
        self.semantic_disabled = False
        self.records = [
            {
                "id": "1",
                "document": "Section 302 IPC punishment for murder.",
                "metadata": {"source": "IPC Bare Act", "page": 10},
                "score": 0.91,
                "act": "IPC",
                "citation": {"section": "302", "page": 10, "source": "IPC Bare Act"},
                "reasons": ["citation-match:IPC-302"],
            },
            {
                "id": "2",
                "document": "Section 103 BNS addresses murder.",
                "metadata": {"source": "BNS Bare Act", "page": 12},
                "score": 0.88,
                "act": "BNS",
                "citation": {"section": "103", "page": 12, "source": "BNS Bare Act"},
                "reasons": ["citation-match:BNS-103"],
            },
        ]

    def search(self, query, top_k=5, candidate_pool=20):
        query_lower = query.lower()
        if "103" in query_lower and "302" not in query_lower:
            return [self.records[1]][:top_k]
        return self.records[:top_k]

    def format_results(self, results):
        return "\n".join(item["document"] for item in results)

    def refresh_index(self):
        return None


class StubOrchestrator:
    def __init__(self):
        self.router = StubRouter()
        self.retriever = StubRetriever()
        self.enable_verification = True

    def execute(self, query):
        return f"Structured answer for: {query}"


def build_stub_service():
    return HectorApiService(
        orchestrator=StubOrchestrator(),
        retriever=StubRetriever(),
        router=StubRouter(),
    )


app.dependency_overrides[get_service] = build_stub_service
client = TestClient(app)
HEADERS = {"X-API-Key": auth_manager.api_key}


def setup_function():
    cache.clear()


def test_status_endpoint_requires_auth_and_returns_health():
    response = client.get("/status", headers=HEADERS)
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["document_count"] == 2


def test_route_endpoint_normalizes_legacy_query():
    response = client.post("/route", headers=HEADERS, json={"query": "Section 302 IPC"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["route"] == "LEGAL_RESEARCH"
    assert payload["normalized_query"].endswith("Murder BNS 103")
    assert payload["mappings"] == ["BNS Section 103 (Murder)"]


def test_search_endpoint_supports_pagination_and_caching():
    request = {"query": "Section 302 IPC", "page": 1, "page_size": 1, "verify": True}
    first = client.post("/search", headers=HEADERS, json=request)
    assert first.status_code == 200
    first_payload = first.json()
    assert first_payload["total_results"] == 2
    assert first_payload["page_size"] == 1
    assert len(first_payload["items"]) == 1
    assert first_payload["cached"] is False

    second = client.post("/search", headers=HEADERS, json=request)
    second_payload = second.json()
    assert second_payload["cached"] is True


def test_compare_endpoint_returns_counterpart_mapping():
    response = client.post(
        "/compare",
        headers=HEADERS,
        json={"section": "302", "act": "IPC", "page_size": 2},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["counterpart_act"] == "BNS"
    assert payload["counterpart_section"] == "103"
    assert payload["note"] == "homicide mapping"


def test_token_auth_and_websocket_streaming_work():
    token_response = client.post("/auth/token?api_key=hector-dev-key")
    assert token_response.status_code == 200
    token = token_response.json()["access_token"]

    search_response = client.post(
        "/search",
        headers={"Authorization": f"Bearer {token}"},
        json={"query": "Section 302 IPC", "page": 1, "page_size": 1, "verify": False},
    )
    assert search_response.status_code == 200

    with client.websocket_connect(
        "/ws/search", headers={"X-API-Key": auth_manager.api_key}
    ) as websocket:
        websocket.send_json(
            {"query": "Section 302 IPC", "page": 1, "page_size": 1, "verify": False}
        )
        route_event = websocket.receive_json()
        summary_event = websocket.receive_json()
        result_event = websocket.receive_json()
        complete_event = websocket.receive_json()

    assert route_event["event"] == "route"
    assert summary_event["event"] == "summary"
    assert result_event["event"] == "result"
    assert complete_event["event"] == "complete"
