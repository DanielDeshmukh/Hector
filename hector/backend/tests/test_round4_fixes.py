"""Round 4 fail-first tests: semantic-score direction (production Pinecone
cosine similarity vs local Chroma distance), search() sub-phase
instrumentation, and abstention-marker alignment (answer-level flag)."""

import sys
from pathlib import Path

import pytest

_PROJECT = Path(__file__).resolve().parents[1]
if str(_PROJECT) not in sys.path:
    sys.path.insert(0, str(_PROJECT))

from core.verifier import (  # noqa: E402
    ABSTENTION_MARKERS,
    is_abstention_answer,
    is_abstention_sentence,
)
from data.hybrid_retriever import HectorHybridRetriever  # noqa: E402


class _FakePineconeIndex:
    """Minimal data-plane stub: query() returns fixed matches."""

    def __init__(self, matches):
        self._matches = matches

    def query(self, **kwargs):
        return {"matches": [dict(m) for m in self._matches]}


class _FakeChromaCollection:
    """Minimal local dense stub: query() returns fixed ids/distances."""

    def __init__(self, ids, distances):
        self._ids = ids
        self._distances = distances

    def query(self, **kwargs):
        return {
            "ids": [list(self._ids)],
            "documents": [["doc " + rid for rid in self._ids]],
            "metadatas": [[{} for _ in self._ids]],
            "distances": [list(self._distances)],
        }


def _retriever_with_records():
    return HectorHybridRetriever.from_records(
        [
            {
                "id": "uuid-a",
                "document": "Consumer Protection Act section 2 deficiency definition",
                "metadata": {},
            },
            {
                "id": "uuid-b",
                "document": "Copyright Act section 52 fair dealing exceptions",
                "metadata": {},
            },
        ]
    )


def test_pinecone_cosine_similarity_normalizes_best_match_highest():
    """FAIL-FIRST: Pinecone returns cosine similarity (higher = better);
    _normalize_semantic_score treats distance as lower = better, so the raw
    score must be converted to a distance at the source or the ranking is
    inverted for the production backend."""
    retriever = _retriever_with_records()
    retriever.semantic_disabled = False
    retriever.pinecone_index = _FakePineconeIndex(
        [
            {"id": "uuid-a", "score": 0.92, "metadata": {"document": "doc a"}},
            {"id": "uuid-b", "score": 0.31, "metadata": {"document": "doc b"}},
        ]
    )
    retriever._embed_text = lambda text: [0.0] * 4

    ranked = retriever._semantic_search("query", 2)
    by_id = {item["id"]: item for item in ranked}
    assert by_id["uuid-a"]["distance"] < by_id["uuid-b"]["distance"]

    max_distance = max(item["distance"] for item in ranked)
    best = retriever._normalize_semantic_score(
        by_id["uuid-a"]["distance"], max_distance
    )
    worst = retriever._normalize_semantic_score(
        by_id["uuid-b"]["distance"], max_distance
    )
    assert best > worst


def test_chroma_l2_distance_direction_preserved():
    """Regression guard: local Chroma distances (lower = better) keep their
    semantics through _local_dense_search + normalization."""
    retriever = _retriever_with_records()
    retriever.collection = _FakeChromaCollection(
        ["uuid-a", "uuid-b"], [0.30, 0.90]
    )
    ranked = retriever._local_dense_search("query", 2)
    by_id = {item["id"]: item for item in ranked}
    assert by_id["uuid-a"]["distance"] == pytest.approx(0.30)

    max_distance = max(item["distance"] for item in ranked)
    assert retriever._normalize_semantic_score(
        by_id["uuid-a"]["distance"], max_distance
    ) > retriever._normalize_semantic_score(
        by_id["uuid-b"]["distance"], max_distance
    )


def test_search_populates_last_stage_info():
    """FAIL-FIRST: search() must expose per-sub-phase timings and stage id
    lists so the eval harness can profile retrieval and rank expected
    sections at every stage."""
    retriever = _retriever_with_records()
    retriever.search("Consumer Protection Act deficiency definition", top_k=2)

    info = getattr(retriever, "last_stage_info", None)
    assert info is not None, "search() must set last_stage_info"
    expected_stages = {"dense", "bm25", "rrf", "scored", "dedup", "rerank", "final"}
    assert expected_stages <= set(info.get("stages", {}))
    expected_timings = {
        "dense_ms",
        "bm25_ms",
        "fuse_ms",
        "score_ms",
        "dedup_ms",
        "rerank_ms",
        "threshold_ms",
        "total_ms",
    }
    assert expected_timings <= set(info.get("timings_ms", {}))
    assert info["stages"]["bm25"], "bm25 stage should have candidates"
    assert isinstance(info.get("detail", {}).get("scored_top", None), list)


def test_pure_refusal_answer_is_whole_answer_abstention():
    """FAIL-FIRST: a refusal-shaped answer (with a trailing citation-only
    line) must be flagged as an answer-level abstention."""
    answer = (
        "The provided sources do not contain the definition of deficiency "
        "under the Consumer Protection Act, 2019.\n"
        "Consequently, there is no text to compare between the IPC and the "
        "BNS on this point.\n"
        "None of the sources mention that Act.\n"
        "[Source 1] [Source 2] [Source 3]"
    )
    assert is_abstention_answer(answer)


def test_substantive_answer_is_not_abstention():
    answer = (
        "Section 302 of the BNS does not punish murder; murder is punished "
        "under Section 103 with death or imprisonment for life and fine. "
        "Section 103(1) applies to murder committed by a group."
    )
    assert not is_abstention_answer(answer)


def test_empty_or_citation_only_answer_is_not_abstention():
    assert not is_abstention_answer("")
    assert not is_abstention_answer("[Source 1][Source 2]\n\n")


def test_round4_markers_cover_observed_refusal_phrasings():
    observed = [
        "The provided sources do not list or describe these freedoms.",
        "Section 302 does not enumerate the punishment here.",
        "Consequently, there is no text to compare between the IPC and the BNS.",
        "Any practical implications cannot be determined from the given material.",
        "None of the sources mention that Act.",
        "None of Sources 1-5 mention that Act.",
        "The provisions are not stated in the retrieved materials.",
        "These results are not relevant to the query, nor do they address it.",
        "Sources 1-5 contain only references to other statutes, none of which "
        "pertain to the queried Act.",
    ]
    for sentence in observed:
        assert is_abstention_sentence(sentence), sentence
        assert any(
            marker in sentence.lower() for marker in ABSTENTION_MARKERS
        ), sentence
