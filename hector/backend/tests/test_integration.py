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
            "section_title": "Punishment for murder",
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
            "section_title": "Punishment for rape",
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
    # Counterpart sections of mapping.json: IPC 302 -> BNS 103 and
    # BNS 103 -> IPC 302 (both records are in this corpus). Compare panels
    # are exact-section only (see HectorApiService._select_compare_panel),
    # so the mapped counterpart section must exist in the sample corpus for
    # panel assertions to pass. BNS 101 below is an extra corpus record.
    {
        "id": "bns-101",
        "document": "Section 101 BNS. Culpable homicide amounting to murder.",
        "metadata": {
            "source": "BNS.pdf",
            "page": 40,
            "act_name": "BNS",
            "section_number": "101",
        },
        "score": 0.9,
        "act": "BNS",
        "citation": {"section": "101", "page": 40, "source": "BNS.pdf"},
        "reasons": ["citation-match:BNS-101"],
    },
    {
        "id": "ipc-304",
        "document": "Section 304 IPC. Punishment for culpable homicide not amounting to murder.",
        "metadata": {
            "source": "IPC.pdf",
            "page": 105,
            "act_name": "IPC",
            "section_number": "304",
            "section_title": "Punishment for culpable homicide not amounting to murder",
        },
        "score": 0.89,
        "act": "IPC",
        "citation": {"section": "304", "page": 105, "source": "IPC.pdf"},
        "reasons": ["citation-match:IPC-304"],
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
        # IPC 302 maps to BNS 103 per mapping.json (no sub-section note)
        assert data["counterpart_section"] == "103"
        assert data["note"] is None

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
        # BNS 103 ("Punishment for murder") has a single official counterpart
        # in mapping.json: IPC 302 "Punishment for murder".
        assert data["counterpart_section"] == "302"
        assert len(data["requested_results"]) > 0
        assert len(data["counterpart_results"]) > 0

    def test_compare_panels_contain_only_exact_section(self, stub_service, auth):
        """Panels must never mix acts or show neighbouring sections.

        Regression guard for the 2026-10-03 compare fix: raw hybrid ranking
        put the wrong act at top-1 22.5% of the time and showed neighbours
        (BNS 394 -> BNS 39) when a section was absent from an act.
        """
        from fastapi.testclient import TestClient

        client = TestClient(app)
        resp = client.post(
            "/compare",
            headers=auth,
            json={"section": "302", "act": "IPC", "page_size": 5},
        )
        assert resp.status_code == 200
        data = resp.json()
        requested = data["requested_results"]
        counterpart = data["counterpart_results"]
        assert requested, "requested panel must hold IPC 302"
        assert counterpart, "counterpart panel must hold BNS 103"
        for hit in requested:
            assert hit["act"] == "IPC"
            assert str(hit["metadata"]["section_number"]) == "302"
        for hit in counterpart:
            assert hit["act"] == "BNS"
            assert str(hit["metadata"]["section_number"]) == "103"

    def test_compare_absent_section_returns_empty_panel(self, stub_service, auth):
        """A section that does not exist in the act yields an empty panel,
        not same-act neighbours (BNS has sections 1-358 only)."""
        from fastapi.testclient import TestClient

        client = TestClient(app)
        resp = client.post(
            "/compare",
            headers=auth,
            json={"section": "400", "act": "BNS", "page_size": 5},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["requested_results"] == []


class TestExactSectionRetrieval:
    """search_exact_section: the exact act+section lookup compare uses.

    Regression guard for the 2026-10-04 fix: the old filtered path called
    idx.list(filter=...) which raises TypeError on this SDK and silently
    degraded to full hybrid search, so correctness rested entirely on
    post-filtering. The exact path must return only the wanted act's own
    chunks (or nothing) with no model calls on the record-scan leg.
    """

    def test_returns_only_exact_act_section(self, retriever):
        rows = retriever.search_exact_section(
            "Section 302 IPC", "302", "IPC", top_k=3
        )
        assert rows, "IPC 302 exists in SAMPLE_RECORDS"
        for row in rows:
            assert row["act"] == "IPC"
            assert str(row["metadata"]["section_number"]) == "302"
            assert row["document"]
            assert row["reasons"] == ["exact-section-scan"]

    def test_absent_section_returns_empty(self, retriever):
        assert retriever.search_exact_section(
            "Section 999 BNS", "999", "BNS", top_k=3
        ) == []

    def test_section_of_other_act_returns_empty(self, retriever):
        # IPC 302 exists; the same number under BNS must not surface it.
        assert retriever.search_exact_section(
            "Section 302 BNS", "302", "BNS", top_k=3
        ) == []

    def test_respects_top_k(self, retriever):
        rows = retriever.search_exact_section(
            "Section 302 IPC", "302", "IPC", top_k=1
        )
        assert len(rows) <= 1


class TestCitationInjectionAndBlend:
    """Citation/counterpart injection + the rerank blend.

    Regression guard for the 2026-10-04 compare-recall fix. Pure rerank
    dropped the cited section to rank ~32 while sister-act lookalikes held
    0.98-0.997 (the fused score that had it at rank 1 was discarded), and
    the mapping counterpart entered neither the dense nor the bm25 top-30 -
    section_recall@10 on the compare gold was 74/162 = 0.46.
    """

    RECORDS = [
        {
            "id": "ipc-103",
            "document": "Section 103 IPC. The right of private defence of "
                        "property extends to causing death.",
            "metadata": {"source": "IPC.pdf", "page": 1,
                         "section_number": "103"},
        },
        {
            # Shares no query tokens: only injection can bring this in.
            "id": "bns-112",
            "document": "112. Zorawar property defence clause applies to theft.",
            "metadata": {"source": "BNS.pdf", "page": 1,
                         "section_number": "112"},
        },
        {
            "id": "iea-9",
            "document": "Section 9 IEA. Cases in which order of court "
                        "relates to explanation of particulars.",
            "metadata": {"source": "IEA.pdf", "page": 3,
                         "section_number": "9"},
        },
        {
            "id": "bns-302",
            "document": "Section 302 BNS. Deliberate act done to outrage "
                        "religious feelings of any class.",
            "metadata": {"source": "BNS.pdf", "page": 9,
                         "section_number": "302"},
        },
    ]

    COMPARE_Q = (
        "Which section of the Bharatiya Nyaya Sanhita, 2023 corresponds to "
        "Section 103 of the Indian Penal Code?"
    )
    MAPPING = ({"103": ["112"]}, {"112": ["103"]})

    @staticmethod
    def _make_retriever():
        return HectorHybridRetriever.from_records(
            TestCitationInjectionAndBlend.RECORDS
        )

    def test_citation_injection_targets_cited_act(self, monkeypatch):
        import data.hybrid_retriever as hr_mod

        monkeypatch.setattr(hr_mod, "_mapping_cache", self.MAPPING)
        r = self._make_retriever()
        query = "What does Section 302 of the Bharatiya Nyaya Sanhita say?"
        rows = r._citation_injection_rows(query, r._parse_query(query))
        assert [(row["id"], row["reasons"][0]) for row in rows] == [
            ("bns-302", "citation-injection")
        ]

    def test_counterpart_injection_only_for_two_act_queries(self, monkeypatch):
        import data.hybrid_retriever as hr_mod

        monkeypatch.setattr(hr_mod, "_mapping_cache", self.MAPPING)
        r = self._make_retriever()

        rows = r._citation_injection_rows(
            self.COMPARE_Q, r._parse_query(self.COMPARE_Q)
        )
        kinds = {row["id"]: row["reasons"][0] for row in rows}
        assert kinds == {
            "ipc-103": "citation-injection",
            "bns-112": "counterpart-injection",
        }

        single_act = "Which section of the Indian Penal Code covers this?"
        rows = r._citation_injection_rows(
            single_act, r._parse_query(single_act)
        )
        assert all(
            row["reasons"][0] == "citation-injection" for row in rows
        ), "a query naming one act must not pull in cross-act counterparts"

    def test_injected_counterpart_reaches_results(self, monkeypatch):
        import data.hybrid_retriever as hr_mod

        monkeypatch.setattr(hr_mod, "_mapping_cache", self.MAPPING)
        r = self._make_retriever()
        results = r.search(self.COMPARE_Q, top_k=3, candidate_pool=2)
        by_id = {row["id"]: row for row in results}
        assert "bns-112" in by_id, "counterpart must enter the pool"
        assert by_id["bns-112"]["reasons"][0] == "counterpart-injection"
        detail = r.last_stage_info.get("detail") or {}
        assert any(
            entry["id"] == "bns-112" for entry in detail.get("injected", [])
        )

    def test_blend_keeps_cited_section_above_saturated_noise(self, monkeypatch):
        import data.hybrid_retriever as hr_mod

        monkeypatch.setattr(hr_mod, "_mapping_cache", self.MAPPING)

        class SaturatedProvider:
            """Sister-act lookalikes at 0.997, cited sections demoted to 0.85
            - the exact failure shape measured in the real run."""

            def rerank(self, query, candidates):
                for doc in candidates:
                    score = 0.997
                    if doc["id"] in ("ipc-103", "bns-112"):
                        score = 0.85
                    doc["reranker_score"] = score
                    doc["score"] = score
                    doc["similarity_score"] = score
                candidates.sort(key=lambda d: d["reranker_score"], reverse=True)
                return candidates

        r = self._make_retriever()
        r.reranker_disabled = False
        r._reranker_cached = SaturatedProvider()
        results = r.search(self.COMPARE_Q, top_k=3, candidate_pool=2)
        assert results, "expected results"
        top_ids = [row["id"] for row in results]
        assert top_ids[0] in ("ipc-103", "bns-112"), (
            "blend must rank retrieval evidence over saturated rerank "
            f"noise, got {top_ids}"
        )
        assert "iea-9" not in top_ids[:1]

    def test_blend_env_opt_out_restores_pure_rerank(self, monkeypatch):
        import data.hybrid_retriever as hr_mod

        monkeypatch.setattr(hr_mod, "_mapping_cache", self.MAPPING)
        monkeypatch.setenv("HECTOR_RERANK_BLEND", "1.0")

        class SaturatedProvider:
            def rerank(self, query, candidates):
                for doc in candidates:
                    doc["reranker_score"] = (
                        0.85 if doc["id"] in ("ipc-103", "bns-112") else 0.997
                    )
                    doc["score"] = doc["reranker_score"]
                    doc["similarity_score"] = doc["reranker_score"]
                candidates.sort(
                    key=lambda d: d["reranker_score"], reverse=True
                )
                return candidates

        r = self._make_retriever()
        r.reranker_disabled = False
        r._reranker_cached = SaturatedProvider()
        results = r.search(self.COMPARE_Q, top_k=3, candidate_pool=2)
        top_ids = [row["id"] for row in results]
        assert top_ids[0] not in ("ipc-103", "bns-112"), (
            "HECTOR_RERANK_BLEND=1.0 must restore legacy pure-rerank order "
            f"(citations demoted), got {top_ids}"
        )

    def test_fallback_scorer_values_injected_rows(self, monkeypatch):
        import data.hybrid_retriever as hr_mod

        monkeypatch.setattr(hr_mod, "_mapping_cache", self.MAPPING)
        r = self._make_retriever()  # from_records: reranker disabled
        results = r.search(self.COMPARE_Q, top_k=3, candidate_pool=2)
        top_ids = [row["id"] for row in results]
        assert "bns-112" in top_ids, (
            "fallback scorer must value an injected row's retrieval evidence"
        )
        assert results[0]["id"] == "bns-112"

    def test_expansion_tail_not_treated_as_citations(self, monkeypatch):
        """Query expansion appends 'section N ...' concept hints to
        non-citing queries; injection must honor raw_query so those hints
        are never treated as user citations (regression: whole expansion
        flooded BNS top-10, recall 0.9948 -> 0.6477)."""
        import data.hybrid_retriever as hr_mod

        monkeypatch.setattr(hr_mod, "_mapping_cache", self.MAPPING)
        r = self._make_retriever()
        raw = (
            "Under the Bharatiya Nyaya Sanhita, what applies to abettor "
            "when liable for an offence?"
        )
        expanded = raw + " section 302"  # bns-302 exists in RECORDS

        r.search(expanded, top_k=3, candidate_pool=4, raw_query=raw)
        detail = r.last_stage_info.get("detail") or {}
        assert not detail.get("injected"), (
            f"expansion tail must not inject, got {detail.get('injected')}"
        )

        # contract: without raw_query the passed text IS the citation
        # source (single-string callers pass raw queries themselves)
        r.search(expanded, top_k=3, candidate_pool=4)
        detail = r.last_stage_info.get("detail") or {}
        assert detail.get("injected"), "raw-query fallback must still inject"

    def test_act_attribution_prefers_following_act(self, monkeypatch):
        """'...predecessor of Section 193 of the Bharatiya Nyaya Sanhita'
        must attribute 193 to BNS only - the act named earlier in the
        sentence (IPC) is where the COUNTERPART comes from, not a second
        citation of the same number."""
        import data.hybrid_retriever as hr_mod

        monkeypatch.setattr(
            hr_mod, "_mapping_cache", ({"193": ["207"]}, {"193": ["179"]})
        )
        r = self._make_retriever()
        query = (
            "Which section of the Indian Penal Code is the predecessor of "
            "Section 193 of the Bharatiya Nyaya Sanhita?"
        )
        cited = r._cited_act_sections(query, r._parse_query(query))
        assert cited == [("193", ["BNS"])], cited
        # (IPC, 193) must never be a citation target: the sentence cites
        # 193 under BNS; IPC enters only as the mapped counterpart 179.
        targets = r._citation_injection_rows(query, r._parse_query(query))
        target_pairs = {
            (row["act"], str(row["metadata"]["section_number"]))
            for row in targets
        }
        assert ("IPC", "193") not in target_pairs, target_pairs

    def test_injection_floor_promotes_outside_window(self):
        r = self._make_retriever()
        ranked = [
            {"id": "noise-1", "score": 0.9},
            {"id": "noise-2", "score": 0.8},
            {"id": "ipc-103", "score": 0.5},
            {"id": "bns-112", "score": 0.4},
        ]
        out = r._apply_injection_floor(ranked, 2, {"ipc-103", "bns-112"})
        top_ids = [row["id"] for row in out[:2]]
        # capped at top_k - 1 = 1 injected row in the window
        assert top_ids[0] in ("ipc-103", "bns-112")
        assert len([i for i in top_ids if i in ("ipc-103", "bns-112")]) == 1
        # promote-only: nothing lost, natural order of rest preserved
        assert [row["id"] for row in out[2:]] == [
            i for i in ["noise-1", "noise-2", "ipc-103", "bns-112"]
            if i not in top_ids
        ]

    def test_injection_floor_noop_when_all_in_window(self):
        r = self._make_retriever()
        ranked = [
            {"id": "ipc-103", "score": 0.9},
            {"id": "noise-1", "score": 0.8},
            {"id": "noise-2", "score": 0.7},
        ]
        out = r._apply_injection_floor(ranked, 3, {"ipc-103"})
        assert out == ranked

    def test_injected_row_survives_saturated_rerank_in_window(self, monkeypatch):
        """End-to-end: even when noise out-blends an injected row, the floor
        keeps it inside top_k (the remaining compare-recall gap)."""
        import data.hybrid_retriever as hr_mod

        monkeypatch.setattr(hr_mod, "_mapping_cache", self.MAPPING)

        class HostileProvider:
            """Noise at 0.997, injected rows at 0.0 - worst case blend."""

            def rerank(self, query, candidates):
                for doc in candidates:
                    score = 0.997
                    if doc["id"] in ("ipc-103", "bns-112"):
                        score = 0.0
                    doc["reranker_score"] = score
                    doc["score"] = score
                    doc["similarity_score"] = score
                candidates.sort(key=lambda d: d["reranker_score"], reverse=True)
                return candidates

        r = self._make_retriever()
        r.reranker_disabled = False
        r._reranker_cached = HostileProvider()
        results = r.search(self.COMPARE_Q, top_k=2, candidate_pool=4)
        top_ids = [row["id"] for row in results]
        assert any(i in ("ipc-103", "bns-112") for i in top_ids), (
            f"injected row must survive into top-2, got {top_ids}"
        )


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
