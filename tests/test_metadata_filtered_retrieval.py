from data.hybrid_retriever import HectorHybridRetriever, SimpleBM25


SAMPLE_RECORDS = [
    {
        "id": "chunk-302",
        "document": "Section 302. Punishment for murder. Whoever commits murder shall be punished with death, or imprisonment for life, and shall also be liable to fine.",
        "metadata": {
            "section_number": "302",
            "real_act_name": "Indian Penal Code, 1860",
            "act_name": "Indian Penal Code, 1860",
            "source": "IPC.pdf",
            "page": 45,
        },
    },
    {
        "id": "chunk-304",
        "document": "Section 304. Punishment for culpable homicide not amounting to murder. Whoever commits culpable homicide not amounting to murder shall be punished with imprisonment for life.",
        "metadata": {
            "section_number": "304",
            "real_act_name": "Indian Penal Code, 1860",
            "act_name": "Indian Penal Code, 1860",
            "source": "IPC.pdf",
            "page": 47,
        },
    },
    {
        "id": "chunk-376",
        "document": "Section 376. Punishment for rape. Whoever commits rape shall be punished with rigorous imprisonment for a term which shall not be less than ten years.",
        "metadata": {
            "section_number": "376",
            "real_act_name": "Indian Penal Code, 1860",
            "act_name": "Indian Penal Code, 1860",
            "source": "IPC.pdf",
            "page": 60,
        },
    },
    {
        "id": "chunk-498a",
        "document": "Section 498A. Husband or relative of husband of a woman subjecting her to cruelty. Whoever commits cruelty shall be punished with imprisonment up to three years.",
        "metadata": {
            "section_number": "498a",
            "real_act_name": "Indian Penal Code, 1860",
            "act_name": "Indian Penal Code, 1860",
            "source": "IPC.pdf",
            "page": 80,
        },
    },
    {
        "id": "chunk-bns-302",
        "document": "Section 103. Punishment for murder. Whoever commits murder shall be punished with death, or imprisonment for life, and shall also be liable to fine.",
        "metadata": {
            "section_number": "103",
            "real_act_name": "Bharatiya Nyaya Sanhita, 2023",
            "act_name": "Bharatiya Nyaya Sanhita, 2023",
            "source": "BNS.pdf",
            "page": 30,
        },
    },
]


def _make_retriever():
    """Create a retriever with sample records, no ChromaDB needed."""
    retriever = HectorHybridRetriever.__new__(HectorHybridRetriever)
    retriever.collection_name = "test"
    retriever.db_path = None
    retriever.embed_fn = None
    retriever.cross_encoder = None
    retriever.reranker_disabled = True
    retriever.semantic_disabled = True
    retriever.collection = None
    retriever.records = []
    retriever.corpus = []
    retriever.tokenized_corpus = []
    retriever.bm25 = None
    retriever._load_records(SAMPLE_RECORDS)
    return retriever


class TestBuildWhereFilter:
    def test_section_number_only(self):
        retriever = _make_retriever()
        where = retriever._build_where_filter(["302"], [])
        assert where == {"section_number": {"$eq": "302"}}

    def test_multiple_section_numbers(self):
        retriever = _make_retriever()
        where = retriever._build_where_filter(["302", "304"], [])
        assert where == {
            "$or": [
                {"section_number": {"$eq": "302"}},
                {"section_number": {"$eq": "304"}},
            ]
        }

    def test_section_and_act(self):
        retriever = _make_retriever()
        where = retriever._build_where_filter(["302"], ["IPC"])
        assert where == {
            "$and": [
                {"section_number": {"$eq": "302"}},
                {"real_act_name": {"$eq": "Indian Penal Code, 1860"}},
            ]
        }

    def test_empty_returns_none(self):
        retriever = _make_retriever()
        assert retriever._build_where_filter([], []) is None

    def test_bns_act_filter(self):
        retriever = _make_retriever()
        where = retriever._build_where_filter([], ["BNS"])
        assert where == {"real_act_name": {"$eq": "Bharatiya Nyaya Sanhita, 2023"}}


class TestSearchWithMetadataFilters:
    def test_falls_back_when_no_entities(self):
        retriever = _make_retriever()
        results = retriever.search_with_metadata_filters("Section 302 IPC", {}, top_k=5)
        assert len(results) > 0

    def test_falls_back_when_no_section_or_act(self):
        retriever = _make_retriever()
        results = retriever.search_with_metadata_filters(
            "murder punishment", {"topics": ["murder"]}, top_k=5
        )
        assert len(results) > 0

    def test_returns_results_with_section_filter(self):
        retriever = _make_retriever()
        entities = {"sections": ["302"], "acts": ["IPC"]}
        results = retriever.search_with_metadata_filters(
            "Section 302 IPC punishment", entities, top_k=5
        )
        assert len(results) > 0

    def test_filtered_results_prioritize_correct_section(self):
        retriever = _make_retriever()
        entities = {"sections": ["302"], "acts": ["IPC"]}
        results = retriever.search_with_metadata_filters(
            "Section 302 punishment for murder", entities, top_k=5
        )
        if results:
            top_result = results[0]
            top_section = top_result.get("metadata", {}).get("section_number", "")
            assert top_section == "302", (
                f"Expected section 302 as top result, got {top_section}"
            )


class TestBM25Filtered:
    def test_returns_ranked_results(self):
        retriever = _make_retriever()
        tokens = retriever._tokenize("section 302 murder punishment")
        filtered = [
            {"id": r["id"], "document": r["document"], "metadata": r["metadata"]}
            for r in SAMPLE_RECORDS[:4]
        ]
        results = retriever._bm25_search_filtered(tokens, filtered)
        assert len(results) > 0
        assert all("score" in r for r in results)

    def test_empty_filtered_returns_empty(self):
        retriever = _make_retriever()
        results = retriever._bm25_search_filtered(["test"], [])
        assert results == []


class TestSimpleBM25:
    def test_basic_scoring(self):
        corpus = [
            ["section", "302", "murder", "punishment"],
            ["section", "304", "culpable", "homicide"],
            ["section", "376", "rape", "punishment"],
        ]
        bm25 = SimpleBM25(corpus)
        scores = bm25.get_scores(["section", "302", "murder"])
        assert len(scores) == 3
        assert scores[0] > scores[1]
        assert scores[0] > scores[2]

    def test_empty_corpus(self):
        bm25 = SimpleBM25([])
        assert bm25.get_scores(["test"]) == []
