"""Compare synthesis tests: chunk builder, offline groundedness validation,
canonical reverse determinism, and services wiring with a mocked model."""

import pytest

from core.compare_synthesis import (
    ASPECTS_SUBSTANTIVE,
    PAIR_COUNTERPART,
    build_provisions_chunk,
    synthesize_comparison,
    validate_synthesis,
)


# ---------------------------------------------------------------------------
# Chunk builder
# ---------------------------------------------------------------------------


def _hit(act, section, title, text):
    return {
        "id": f"{act}-{section}",
        "document": text,
        "score": 0.9,
        "act": act,
        "metadata": {
            "act_name": act,
            "section_number": section,
            "section_title": title,
            "source": f"{act}.pdf",
            "page": 1,
        },
        "citation": {"section": section, "page": 1, "source": f"{act}.pdf"},
        "reasons": [],
    }


def test_chunk_contains_both_sides_and_note():
    chunk = build_provisions_chunk(
        "IPC",
        "302",
        [_hit("IPC", "302", "Murder", "Whoever commits murder shall be punished")],
        "BNS",
        "101",
        [_hit("BNS", "101", "Murder", "Whoever commits murder shall be punished")],
        "intentional killing",
    )
    assert "[REQUESTED] act=IPC section=302 title=Murder" in chunk
    assert "[COUNTERPART] act=BNS section=101 title=Murder" in chunk
    assert "[MAPPING NOTE] intentional killing" in chunk
    assert "punished" in chunk


def test_chunk_truncates_overlong_side_text():
    long_text = "x" * 5000
    chunk = build_provisions_chunk(
        "IPC",
        "302",
        [_hit("IPC", "302", "Murder", long_text)],
        "BNS",
        "101",
        [_hit("BNS", "101", "Murder", "short")],
        None,
    )
    assert "...[truncated]" in chunk
    assert len(chunk) < 5000


# ---------------------------------------------------------------------------
# Offline validation
# ---------------------------------------------------------------------------

ALLOWED = {("IPC", "302"), ("BNS", "101")}


def _good_payload():
    return {
        "rows": [
            {
                "aspect": aspect,
                "requested": f"IPC 302 cell for {aspect}",
                "counterpart": f"BNS 101 cell for {aspect}",
            }
            for aspect in ASPECTS_SUBSTANTIVE
        ],
        "message": "Both provisions punish murder under IPC 302 and BNS 101.",
    }


def test_validate_accepts_good_payload():
    ok, reason = validate_synthesis(_good_payload(), ASPECTS_SUBSTANTIVE, ALLOWED)
    assert ok, reason


def test_validate_rejects_non_object():
    ok, reason = validate_synthesis("nope", ASPECTS_SUBSTANTIVE, ALLOWED)
    assert not ok and reason == "not-object"


def test_validate_rejects_wrong_row_count():
    payload = _good_payload()
    payload["rows"] = payload["rows"][:2]
    ok, reason = validate_synthesis(payload, ASPECTS_SUBSTANTIVE, ALLOWED)
    assert not ok and reason == "row-count"


def test_validate_rejects_reordered_aspects():
    payload = _good_payload()
    payload["rows"][0], payload["rows"][1] = payload["rows"][1], payload["rows"][0]
    ok, reason = validate_synthesis(payload, ASPECTS_SUBSTANTIVE, ALLOWED)
    assert not ok and reason == "aspect-order"


def test_validate_rejects_ungrounded_section_reference():
    payload = _good_payload()
    payload["rows"][2]["counterpart"] = "Punished under BNS 999"
    ok, reason = validate_synthesis(payload, ASPECTS_SUBSTANTIVE, ALLOWED)
    assert not ok and reason == "ungrounded-ref:BNS 999"


def test_validate_allows_actless_numbers_in_punishment_cells():
    payload = _good_payload()
    payload["rows"][2]["requested"] = "Death or imprisonment for life, up to 10 years"
    ok, reason = validate_synthesis(payload, ASPECTS_SUBSTANTIVE, ALLOWED)
    assert ok, reason


def test_validate_rejects_overlong_cell():
    payload = _good_payload()
    payload["rows"][0]["requested"] = "x" * 401
    ok, reason = validate_synthesis(payload, ASPECTS_SUBSTANTIVE, ALLOWED)
    assert not ok and reason == "cell-too-long"


def test_validate_rejects_missing_message():
    payload = _good_payload()
    payload["message"] = ""
    ok, reason = validate_synthesis(payload, ASPECTS_SUBSTANTIVE, ALLOWED)
    assert not ok and reason == "message-missing"


def test_validate_rejects_overlong_message():
    payload = _good_payload()
    payload["message"] = "x" * 421
    ok, reason = validate_synthesis(payload, ASPECTS_SUBSTANTIVE, ALLOWED)
    assert not ok and reason == "message-too-long"


# ---------------------------------------------------------------------------
# synthesize_comparison guards (no network)
# ---------------------------------------------------------------------------


def test_pair_registry_covers_current_and_reserved_pairs():
    assert PAIR_COUNTERPART["IPC"] == "BNS"
    assert PAIR_COUNTERPART["BNS"] == "IPC"
    assert PAIR_COUNTERPART["CRPC"] == "BNSS"
    assert PAIR_COUNTERPART["IEA"] == "BSA"
    assert "CPC" not in PAIR_COUNTERPART


def test_synthesize_disabled_by_env_returns_none(monkeypatch):
    monkeypatch.setenv("HECTOR_COMPARE_DISABLED", "1")
    assert (
        synthesize_comparison(
            requested_act="IPC",
            requested_section="302",
            requested_items=[],
            counterpart_act="BNS",
            counterpart_section="101",
            counterpart_items=[],
        )
        is None
    )


def test_synthesize_unknown_pair_returns_none_without_network(monkeypatch):
    monkeypatch.delenv("HECTOR_COMPARE_DISABLED", raising=False)
    assert (
        synthesize_comparison(
            requested_act="CRPC",
            requested_section="154",
            requested_items=[],
            counterpart_act="BNSS",
            counterpart_section="175",
            counterpart_items=[],
        )
        is None
    )


# ---------------------------------------------------------------------------
# Services wiring (mocked model) + canonical reverse
# ---------------------------------------------------------------------------

RECORDS = [
    _hit("IPC", "302", "Murder", "Whoever commits murder shall be punished with death."),
    _hit(
        "IPC",
        "94",
        "Act to which a person is compelled by threats",
        "Nothing is an offence by reason of an act done by a person under threat.",
    ),
    _hit(
        "IPC",
        "304",
        "Punishment for culpable homicide not amounting to murder",
        "Whoever commits culpable homicide not amounting to murder shall be punished.",
    ),
    _hit("BNS", "101", "Murder", "Whoever commits murder shall be punished with death."),
    _hit("BNS", "103", "Punishment for murder", "Whoever commits murder shall be punished."),
]


@pytest.fixture(scope="module")
def service():
    from api.services import HectorApiService
    from core.orchestrator import HectorOrchestrator
    from core.router import HectorRouter
    from data.hybrid_retriever import HectorHybridRetriever

    router = HectorRouter()
    router.client = None  # force rule-based routing (no network)
    retriever = HectorHybridRetriever.from_records(RECORDS)
    orch = HectorOrchestrator.__new__(HectorOrchestrator)
    orch.router = router
    orch.retriever = retriever
    orch.enable_verification = False
    return HectorApiService(orchestrator=orch, retriever=retriever, router=router)


def test_canonical_reverse_resolves_shared_target_by_title_overlap(service):
    # Direct tie-break unit test: among candidates for one BNS target the
    # candidate whose corpus section_title overlaps the BNS title wins,
    # regardless of candidate order (IPC 94 "Act to which a person is
    # compelled by threats" has zero overlap with "Punishment for murder",
    # IPC 302 matches).
    sec, _note = service._pick_reverse_counterpart(
        "103",
        [("94", {"new": "103"}), ("302", {"new": "103"})],
    )
    assert sec == "302"
    first = service._canonical_reverse()
    second = service._canonical_reverse()
    assert first is second  # cached single build
    chosen, _note2 = first["103"]
    assert chosen == "302"  # official counterpart of BNS 103 is IPC 302


def test_canonical_reverse_covers_every_mapping_target(service):
    reverse = service._canonical_reverse()
    targets = {
        str((m or {}).get("new") or "").strip().upper()
        for m in service.router.legal_map.values()
        if (m or {}).get("new")
    }
    assert targets == set(reverse)
    for section, note in reverse.values():
        assert section  # every target resolves to an IPC section


def _wired_synthesis(rows, message):
    return {
        "rows": [
            {"aspect": a, "requested": "r", "counterpart": "c"}
            for a in (rows or ASPECTS_SUBSTANTIVE)
        ],
        "message": message,
    }


def test_compare_synthesis_ok_path(service, monkeypatch):
    from api import services as services_module
    from api.schemas import CompareRequest

    monkeypatch.delenv("HECTOR_COMPARE_DISABLED", raising=False)
    monkeypatch.setattr(
        services_module.compare_synthesis,
        "synthesize_comparison",
        lambda **kwargs: _wired_synthesis(None, "Grounded summary."),
    )
    resp = service.compare(CompareRequest(section="302", act="IPC"))
    assert resp.counterpart_act == "BNS"
    assert resp.counterpart_section == "103"
    assert resp.synthesis == "ok"
    assert len(resp.comparison_table) == len(ASPECTS_SUBSTANTIVE)
    assert resp.grounded_message == "Grounded summary."


def test_compare_synthesis_failure_falls_back_to_panels(service, monkeypatch):
    from api import services as services_module
    from api.schemas import CompareRequest

    monkeypatch.delenv("HECTOR_COMPARE_DISABLED", raising=False)
    monkeypatch.setattr(
        services_module.compare_synthesis,
        "synthesize_comparison",
        lambda **kwargs: None,
    )
    resp = service.compare(CompareRequest(section="302", act="IPC"))
    assert resp.synthesis == "fallback"
    assert resp.comparison_table == []
    assert resp.grounded_message is None
    assert resp.requested_results and resp.counterpart_results


def test_compare_env_disabled_makes_no_model_call(service, monkeypatch):
    from api.schemas import CompareRequest

    monkeypatch.setenv("HECTOR_COMPARE_DISABLED", "1")
    calls = []

    def _bomb(**kwargs):
        calls.append(kwargs)
        raise AssertionError("model must not be called when disabled")

    monkeypatch.setattr(
        "core.compare_synthesis.get_nim_llm", lambda **kwargs: _bomb
    )
    resp = service.compare(CompareRequest(section="302", act="IPC"))
    # services still calls synthesize_comparison, which returns None
    # before touching the client when the kill switch is on.
    assert resp.synthesis in ("fallback", "skipped")
    assert calls == []


def test_compare_without_counterpart_is_skipped(service, monkeypatch):
    from api.schemas import CompareRequest

    resp = service.compare(CompareRequest(section="1", act="BNS"))
    # BNS 1 has no IPC counterpart in mapping.json -> nothing to synthesize
    if resp.counterpart_section is None:
        assert resp.synthesis == "skipped"
        assert resp.comparison_table == []
    else:  # pragma: no cover - mapping unexpectedly provides one
        pytest.skip("mapping.json resolved a counterpart for BNS 1")
