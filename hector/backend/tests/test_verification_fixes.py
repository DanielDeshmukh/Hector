"""Regression tests for the verification-layer fixes.

Covers: vacuous CoVe scoring (zero-claim 100%), missing offence_definition
verification branch, abstain-aware retrieval scoring/generation, relevance
threshold behaviour, retry jitter, and NIM model fallback chain.
"""

import os
import sys
from types import SimpleNamespace

import pytest

_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
_BACKEND_DIR = os.path.dirname(_TESTS_DIR)
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from core.response_generator import ContextualResponseGenerator
from core.verifier import ChainOfVerification
from data.hybrid_retriever import HectorHybridRetriever
from run_retrieval_eval import score_retrieval


LIMITATION_SOURCES = [
    {
        "document": (
            "Every suit instituted after the right to sue accrues shall be "
            "barred under section 3 of the Limitation Act, 1963 after three years."
        ),
        "metadata": {"source": "Limitation_Act_1963.pdf", "page": 12},
    }
]

FORGERY_SOURCES = [
    {
        "document": (
            "463. Forgery. \u2014Whoever makes any false document or electronic "
            "record with intent to cause damage shall be punished with "
            "imprisonment of seven years, or with fine, or with both."
        ),
        "metadata": {"source": "IPC.pdf", "page": 210},
    }
]


class TestSectionOfActExtraction:
    def test_limitation_act_section_extracted_and_scored(self):
        verifier = ChainOfVerification()
        response = (
            "Section 3 of the Limitation Act bars suits filed after three years."
        )

        result = verifier.verify_response(response, LIMITATION_SOURCES)

        assert result["claims_total"] >= 1
        assert result["status"] in ("VERIFIED", "PARTIAL", "UNVERIFIED")
        assert result["citation_coverage"] is not None
        assert 0.0 <= result["citation_coverage"] <= 1.0


class TestZeroClaimStatus:
    def test_legal_text_without_claims_is_unverified_not_100(self):
        verifier = ChainOfVerification()
        response = (
            "The Limitation Act and the Code of Civil Procedure provide remedies."
        )

        result = verifier.verify_response(response, [])

        assert result["claims_total"] == 0
        assert result["claims_verified"] == 0
        assert result["citation_coverage"] is None
        assert result["status"] == "UNVERIFIED"

    def test_refusal_is_not_applicable(self):
        verifier = ChainOfVerification()
        response = "I cannot find this information in the loaded legal texts."

        result = verifier.verify_response(response, LIMITATION_SOURCES)

        assert result["claims_total"] == 0
        assert result["claims_verified"] == 0
        assert result["citation_coverage"] is None
        assert result["status"] == "NOT_APPLICABLE"

    def test_hallucination_report_handles_unscored_coverage(self):
        from core.verifier import HallucinationDetector

        report = HallucinationDetector.generate_hallucination_report(
            {
                "verified_response": "The Limitation Act provides remedies.",
                "citation_coverage": None,
                "total_claims": 0,
                "claims_verified": 0,
                "status": "UNVERIFIED",
            }
        )

        assert report["status"] == "HIGH_RISK"
        assert report["needs_review"] is True


class TestOffenceDefinitionBranch:
    def test_grounded_offence_definition_supported_and_kept(self):
        verifier = ChainOfVerification()
        response = (
            "Whoever makes any false document with intent to cause damage "
            "shall be punished with imprisonment of seven years."
        )

        result = verifier.verify_response(response, FORGERY_SOURCES)

        assert result["claims_total"] >= 1
        assert result["unverified_claims"] == []
        assert result["claims_unsupported"] == 0
        assert result["status"] == "VERIFIED"
        assert result["needs_correction"] is False
        assert "Whoever makes any false document" in result["verified_response"]

    def test_absent_offence_definition_is_unsupported(self):
        verifier = ChainOfVerification()
        response = (
            "Whoever operates an unlicensed nuclear reactor shall be punished "
            "with imprisonment for twenty years."
        )

        result = verifier.verify_response(response, FORGERY_SOURCES)

        offence_unsupported = [
            claim
            for claim in result["unverified_claims"]
            if claim["type"] == "offence_definition"
        ]
        assert len(offence_unsupported) >= 1
        assert result["status"] == "UNVERIFIED"


class TestAbstainScoring:
    def test_irrelevant_passes_only_when_abstained_with_zero_citations(self):
        assert (
            score_retrieval(
                "capital of France",
                [],
                [],
                "irrelevant",
                abstained=True,
                citations=0,
            )
            == 100
        )
        assert (
            score_retrieval(
                "capital of France",
                [],
                [],
                "irrelevant",
                abstained=True,
                citations=2,
            )
            < 50
        )

    def test_irrelevant_without_abstention_never_passes(self):
        legal_chunks = ["Section 1 IPC applies to contracts."] * 3
        nonlegal_chunks = ["A recipe for pasta carbonara."] * 3
        for chunks in (legal_chunks, nonlegal_chunks):
            score = score_retrieval(
                "What is the capital of France?",
                chunks,
                [],
                "irrelevant",
                abstained=False,
                citations=0,
            )
            assert score < 50

    def test_in_scope_abstention_scores_zero(self):
        score = score_retrieval(
            "What is the punishment for murder under Section 302 IPC",
            [],
            ["302", "murder"],
            "exact",
            abstained=True,
            citations=0,
        )
        assert score < 50


def test_generation_abstains_explicitly_without_sources():
    generator = ContextualResponseGenerator(retriever=None)

    out = generator.generate("What is the capital of France?", [])

    assert out["abstained"] is True
    assert out["citations"] == []
    assert out["answer_confidence"] == 0.0
    assert "[Source" not in out["generated_response"]
    assert (
        "could not find sufficiently relevant sources"
        in out["generated_response"].lower()
    )

    result = ChainOfVerification().verify_response(
        ContextualResponseGenerator.ABSTENTION_MESSAGE, []
    )
    assert result["status"] == "NOT_APPLICABLE"
    assert result["citation_coverage"] is None


def test_dense_leg_429_retries_then_reports_bm25_only(monkeypatch):
    import utils.retry as retry_mod

    records = [
        {
            "id": "s302",
            "document": (
                "Section 302 IPC punishment for murder is death or "
                "imprisonment for life."
            ),
            "metadata": {"source": "IPC.pdf", "page": 45},
        },
        {
            "id": "s376",
            "document": "Section 376 IPC punishment for rape is rigorous imprisonment.",
            "metadata": {"source": "IPC.pdf", "page": 60},
        },
    ]
    retriever = HectorHybridRetriever.from_records(records)

    class FakeIndex:
        calls = 0

        def query(self, **kwargs):
            FakeIndex.calls += 1
            raise RuntimeError("429 egress limit exceeded")

    retriever.pinecone_index = FakeIndex()
    retriever.semantic_disabled = False
    monkeypatch.setenv("HECTOR_MIN_RELEVANCE", "0.05")
    monkeypatch.setattr(retry_mod, "_MAX_ATTEMPTS", 3)
    monkeypatch.setattr(retry_mod, "time", SimpleNamespace(sleep=lambda _s: None))
    monkeypatch.setattr(retriever, "_embed_text", lambda _text: [0.0] * 8)

    results = retriever.search("Section 302 IPC murder punishment", top_k=5)

    assert FakeIndex.calls == 3
    assert retriever.last_search_mode == "bm25_only"
    assert len(results) > 0


def test_retry_backoff_includes_jitter(monkeypatch):
    import utils.retry as retry_mod

    delays = []
    monkeypatch.setattr(retry_mod, "time", SimpleNamespace(sleep=delays.append))
    monkeypatch.setattr(retry_mod, "uniform", lambda _lo, _hi: 1.5)

    def always_fail():
        raise ValueError("boom")

    with pytest.raises(ValueError):
        retry_mod.retry(
            always_fail, max_attempts=3, base_delay=4.0, max_delay=100.0
        )

    assert delays == [6.0, 12.0]


def _fake_openai_client(create):
    return SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=create))
    )


def test_model_falls_back_to_next_on_dead_model(monkeypatch):
    import utils.retry as retry_mod
    from core.nim_llm import NimLLMClient

    monkeypatch.setattr(retry_mod, "_MAX_ATTEMPTS", 1)
    monkeypatch.setattr(retry_mod, "time", SimpleNamespace(sleep=lambda _s: None))
    monkeypatch.delenv("HECTOR_NIM_CHAT_MODEL", raising=False)

    calls = []

    def create(**kwargs):
        calls.append(kwargs["model"])
        if kwargs["model"] == "dead/one":
            err = RuntimeError("model does not exist")
            err.status_code = 404
            raise err
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="ok"))]
        )

    client = NimLLMClient(api_key="test-key", model="dead/one,good/two")
    client._client = _fake_openai_client(create)

    out = client.chat([{"role": "user", "content": "hi"}])

    assert out == "ok"
    assert calls[0] == "dead/one"
    assert "good/two" in calls


def test_model_chain_clear_error_when_all_dead(monkeypatch):
    import utils.retry as retry_mod
    from core.nim_llm import NimLLMClient

    monkeypatch.setattr(retry_mod, "_MAX_ATTEMPTS", 1)
    monkeypatch.setattr(retry_mod, "time", SimpleNamespace(sleep=lambda _s: None))
    monkeypatch.delenv("HECTOR_NIM_CHAT_MODEL", raising=False)

    def create(**kwargs):
        err = RuntimeError("model does not exist")
        err.status_code = 404
        raise err

    client = NimLLMClient(api_key="test-key", model="dead/one,dead/two")
    client._client = _fake_openai_client(create)

    with pytest.raises(RuntimeError, match="dead/one"):
        client.chat([{"role": "user", "content": "hi"}])
