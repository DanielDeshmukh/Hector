"""Round 2 fail-first tests: citation grounding, status logic, claim
extraction, data-derived threshold, local dense fallback."""

import json
import os
import re
import sys
from pathlib import Path

import chromadb
import pytest

_PROJECT = Path(__file__).resolve().parents[1]
if str(_PROJECT) not in sys.path:
    sys.path.insert(0, str(_PROJECT))

from core.verifier import ClaimExtractor, ChainOfVerification, HallucinationDetector  # noqa: E402
from data.hybrid_retriever import HectorHybridRetriever  # noqa: E402
from calibrate_relevance_threshold import choose_threshold  # noqa: E402


def test_mixed_refusal_with_substantive_content_is_unverified():
    cove = ChainOfVerification()
    answer = (
        "The sources do not contain the limitation period for suits. "
        "Appeals against appellate decrees must be filed within 90 days "
        "under the Limitation Act."
    )
    out = cove.verify_response(answer, [])
    assert out["claims_total"] == 0
    assert out["status"] == "UNVERIFIED"


def test_pure_refusal_stays_not_applicable():
    cove = ChainOfVerification()
    out = cove.verify_response(
        "I cannot find this information in the loaded legal texts.", []
    )
    assert out["status"] == "NOT_APPLICABLE"


def test_non_legal_response_stays_not_applicable():
    cove = ChainOfVerification()
    out = cove.verify_response("Hello! How can I help you today?", [])
    assert out["status"] == "NOT_APPLICABLE"


def test_act_before_section_extracts_section_of_act_claim():
    claims = ClaimExtractor.extract_claims(
        "Bharatiya Sakshya Adhiniyam, 2023 (BSA), Section 23(1) expressly "
        "bars oral confessions."
    )
    matches = [
        c
        for c in claims
        if c.get("type") == "section_of_act" and c.get("section") == "23"
    ]
    assert matches, claims
    assert any(
        "bharatiya sakshya adhiniyam" in " ".join(c.get("act_terms", []))
        for c in matches
    )


def test_section_symbol_extracts_claim():
    claims = ClaimExtractor.extract_claims(
        "BSA \u00a7 23(1) provides that confessions are inadmissible."
    )
    assert any(c.get("value") == "Section 23" for c in claims), claims


def test_abstention_sentence_is_not_a_claim():
    claims = ClaimExtractor.extract_claims(
        "The sources do not contain Section 38 of the Consumer Protection "
        "Act, 2019."
    )
    assert claims == []


def test_generic_act_section_verified():
    cove = ChainOfVerification()
    sources = [
        {
            "document": (
                "Appeals shall be filed within ninety days. Section 5 of "
                "the Limitation Act, 1963 empowers the court to extend time."
            ),
            "metadata": {"source": "limitation_act.pdf", "page": 1},
        }
    ]
    out = cove.verify_response(
        "The period may be extended under Section 5 of the Act if "
        "sufficient cause is shown.",
        sources,
    )
    assert out["claims_total"] >= 1
    assert out["claims_supported"] >= 1


def test_abbreviated_act_expanded_in_verification():
    cove = ChainOfVerification()
    sources = [
        {
            "document": (
                "Section 103 of the Bharatiya Nyaya Sanhita, 2023. Whoever "
                "commits murder shall be punished with death or "
                "imprisonment for life."
            ),
            "metadata": {"source": "bns.pdf", "page": 9},
        }
    ]
    out = cove.verify_response(
        "Murder is punishable under Section 103 BNS with death or life "
        "imprisonment.",
        sources,
    )
    assert out["claims_total"] >= 1
    assert out["claims_supported"] >= 1


def test_narrow_space_normalized_before_verification():
    cove = ChainOfVerification()
    sources = [
        {
            "document": (
                "Section 302 IPC. Whoever commits murder shall be punished "
                "with death."
            ),
            "metadata": {"source": "ipc.pdf", "page": 10},
        }
    ]
    out = cove.verify_response("Section\u202f302 IPC covers murder.", sources)
    assert out["claims_total"] >= 1
    assert out["claims_supported"] >= 1


def test_negated_huge_section_not_flagged_as_fabricated():
    fabricated = HallucinationDetector.detect_fabricated_citations(
        "The provided sources do not contain any reference to the "
        "Underwater Basket Weaving Act, 2099 or its Section 99999."
    )
    assert fabricated == []


def test_none_mention_negation_not_flagged_as_fabricated():
    fabricated = HallucinationDetector.detect_fabricated_citations(
        "After reviewing Sources 1 through 5, none mention that Act or "
        "its section 99999."
    )
    assert fabricated == []


def test_asserted_huge_section_flagged_with_full_value():
    fabricated = HallucinationDetector.detect_fabricated_citations(
        "Section 99999 IPC states the punishment."
    )
    assert len(fabricated) == 1
    assert fabricated[0]["value"] == "99999"


def test_valid_section_not_flagged_as_fabricated():
    fabricated = HallucinationDetector.detect_fabricated_citations(
        "Section 302 IPC covers murder."
    )
    assert fabricated == []


def test_grounding_report_counts_negated_and_grounded_mentions():
    from core.verifier import grounding_report

    answer = (
        "The sources do not contain Section 420 of the Indian Penal Code. "
        "Murder is punishable under Section 103 of the Bharatiya Nyaya "
        "Sanhita, 2023."
    )
    source = (
        "Section 103 of the Bharatiya Nyaya Sanhita, 2023. Whoever "
        "commits murder shall be punished with death."
    )
    report = grounding_report(answer, source)
    assert report["n_mentions"] == 2
    assert report["n_negated"] == 1
    assert report["n_grounded"] == 1


def _new_retriever():
    return HectorHybridRetriever.__new__(HectorHybridRetriever)


def test_min_relevance_env_overrides_threshold_file(tmp_path, monkeypatch):
    path = tmp_path / "threshold.json"
    path.write_text(json.dumps({"threshold": 0.3}), encoding="utf-8")
    monkeypatch.setenv("HECTOR_RELEVANCE_THRESHOLD_JSON", str(path))
    monkeypatch.setenv("HECTOR_MIN_RELEVANCE", "0.7")
    assert _new_retriever()._min_relevance() == pytest.approx(0.7)


def test_min_relevance_reads_threshold_file(tmp_path, monkeypatch):
    path = tmp_path / "threshold.json"
    path.write_text(json.dumps({"threshold": 0.42}), encoding="utf-8")
    monkeypatch.setenv("HECTOR_RELEVANCE_THRESHOLD_JSON", str(path))
    monkeypatch.delenv("HECTOR_MIN_RELEVANCE", raising=False)
    assert _new_retriever()._min_relevance() == pytest.approx(0.42)


def test_min_relevance_invalid_env_falls_back_to_file(tmp_path, monkeypatch):
    path = tmp_path / "threshold.json"
    path.write_text(json.dumps({"threshold": 0.42}), encoding="utf-8")
    monkeypatch.setenv("HECTOR_RELEVANCE_THRESHOLD_JSON", str(path))
    monkeypatch.setenv("HECTOR_MIN_RELEVANCE", "not-a-number")
    assert _new_retriever()._min_relevance() == pytest.approx(0.42)


def test_min_relevance_defaults_to_legacy_without_file(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "HECTOR_RELEVANCE_THRESHOLD_JSON",
        str(tmp_path / "does_not_exist.json"),
    )
    monkeypatch.delenv("HECTOR_MIN_RELEVANCE", raising=False)
    assert _new_retriever()._min_relevance() == pytest.approx(0.05)


def test_choose_threshold_separates_answerable_from_unanswerable():
    best = choose_threshold([0.9, 0.95], [0.01, 0.02])
    assert best["threshold"] == pytest.approx(0.9)
    assert best["balanced_accuracy"] == pytest.approx(1.0)


def test_choose_threshold_requires_both_groups():
    with pytest.raises(ValueError):
        choose_threshold([], [0.1])


class _ToyEmbeddingFunction(chromadb.EmbeddingFunction):
    def __call__(self, input):
        vectors = []
        for text in input:
            vec = [0.0] * 16
            for token in re.findall(r"[a-z0-9]+", text.lower()):
                vec[sum(ord(c) for c in token) % 16] += 1.0
            norm = sum(v * v for v in vec) ** 0.5 or 1.0
            vectors.append([v / norm for v in vec])
        return vectors


def _make_collection(tmp_path, name, docs):
    client = chromadb.PersistentClient(path=str(tmp_path / f"{name}_db"))
    collection = client.create_collection(
        name, embedding_function=_ToyEmbeddingFunction()
    )
    collection.add(
        ids=[f"{name}-{i}" for i in range(len(docs))],
        documents=docs,
        metadatas=[{"chunk": i} for i in range(len(docs))],
    )
    return collection


_LEGAL_DOCS = [
    "Section 302 IPC. Whoever commits murder shall be punished with "
    "death or with imprisonment for life.",
    "Section 376 IPC punishment for rape shall be rigorous imprisonment.",
]


def test_local_dense_search_returns_ranked_items(tmp_path):
    collection = _make_collection(tmp_path, "dense", _LEGAL_DOCS)
    retriever = _new_retriever()
    retriever.collection = collection
    hits = retriever._local_dense_search("punishment for murder", 3)
    assert hits, "local dense leg returned no results"
    assert {"id", "document", "metadata", "distance", "rank"} <= set(hits[0])
    assert hits[0]["rank"] == 1


def test_search_uses_local_dense_and_reports_hybrid(tmp_path):
    records = [
        {"id": f"r{i}", "document": doc, "metadata": {"chunk": i}}
        for i, doc in enumerate(_LEGAL_DOCS)
    ]
    collection = _make_collection(tmp_path, "hybrid", _LEGAL_DOCS)
    retriever = HectorHybridRetriever.from_records(records)
    retriever.collection = collection
    results = retriever.search("Section 302 IPC punishment for murder", top_k=3)
    assert retriever.last_search_mode == "hybrid"
    assert results


def test_refresh_index_falls_back_to_local_records(tmp_path):
    collection = _make_collection(tmp_path, "refresh", _LEGAL_DOCS)
    retriever = HectorHybridRetriever.from_records(
        [{"id": "old", "document": "stale local record", "metadata": {}}]
    )
    retriever.collection = collection
    retriever.refresh_index()
    documents = [r["document"] for r in retriever.records]
    assert any("Section 302" in doc for doc in documents), documents


def test_refresh_index_marks_pinecone_dead_on_probe_failure():
    class DeadIndex:
        def fetch(self, ids, **kwargs):
            raise RuntimeError("429 Egress budget exceeded")

        def list(self):
            raise AssertionError("pinecone loop must be skipped once dead")

    retriever = HectorHybridRetriever.from_records(
        [{"id": "a", "document": "record a", "metadata": {}}]
    )
    retriever.collection = None
    retriever.pinecone_index = DeadIndex()
    retriever.refresh_index()
    assert getattr(retriever, "_pinecone_dead", False) is True
