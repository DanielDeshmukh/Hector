import math
import os
import re
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from utils.retry import retry

try:
    import chromadb
    from chromadb.utils import embedding_functions
except ImportError:
    chromadb = None
    embedding_functions = None

try:
    from sentence_transformers import CrossEncoder
except ImportError:
    CrossEncoder = None

try:
    from core.embedding_provider import get_embedding_provider
    from core.rerank_provider import get_rerank_provider
except ImportError:
    get_embedding_provider = None
    get_rerank_provider = None


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(PROJECT_ROOT, "hector_db")
DEFAULT_COLLECTION = "indian_law_bns"
DEFAULT_CROSS_ENCODER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


class SimpleBM25:
    """A compact BM25 implementation so retrieval does not depend on extra packages."""

    def __init__(self, tokenized_corpus, k1=1.5, b=0.75):
        self.tokenized_corpus = tokenized_corpus
        self.k1 = k1
        self.b = b
        self.doc_count = len(tokenized_corpus)
        self.avgdl = (
            sum(len(document) for document in tokenized_corpus) / self.doc_count
            if self.doc_count
            else 0.0
        )
        self.term_frequencies = []
        self.document_frequencies = defaultdict(int)
        self.document_lengths = []

        for document in tokenized_corpus:
            frequencies = Counter(document)
            self.term_frequencies.append(frequencies)
            self.document_lengths.append(len(document))
            for term in frequencies:
                self.document_frequencies[term] += 1

    def get_scores(self, query_tokens):
        if not self.doc_count:
            return []

        scores = []
        for frequencies, doc_length in zip(
            self.term_frequencies, self.document_lengths
        ):
            score = 0.0
            for term in query_tokens:
                tf = frequencies.get(term, 0)
                if tf == 0:
                    continue

                df = self.document_frequencies.get(term, 0)
                idf = math.log(1 + ((self.doc_count - df + 0.5) / (df + 0.5)))
                denominator = tf + self.k1 * (
                    1 - self.b + self.b * (doc_length / max(self.avgdl, 1.0))
                )
                score += idf * ((tf * (self.k1 + 1)) / denominator)
            scores.append(score)
        return scores


class HectorHybridRetriever:
    SECTION_PATTERN = re.compile(
        r"\b(?:section|sec\.?|s\.)\s*(\d{1,4}[a-z]?)\b", re.IGNORECASE
    )
    ACT_PATTERN = re.compile(
        r"\b(ipc|bns|crpc|bnss|bsa|cpc|bharatiya nyaya sanhita|bharatiya nagarik suraksha sanhita|bharatiya sakshya adhiniyam|indian penal code|code of criminal procedure|evidence act|indian evidence act)\b",
        re.IGNORECASE,
    )
    TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
    SECTION_IN_TEXT_PATTERN = re.compile(
        r"\[s\s*(\d{1,4}[a-z]?)(?:\.\d+)?\]|\b(?:section|sec\.?|s\.)\s*(\d{1,4}[a-z]?)\b|^\s*(\d{1,4}[a-z]?)\.\s",
        re.IGNORECASE | re.MULTILINE,
    )

    ACT_ALIASES = {
        "ipc": "IPC",
        "indian penal code": "IPC",
        "bns": "BNS",
        "bharatiya nyaya sanhita": "BNS",
        "crpc": "CRPC",
        "code of criminal procedure": "CRPC",
        "bnss": "BNSS",
        "bharatiya nagarik suraksha sanhita": "BNSS",
        "bsa": "BSA",
        "bharatiya sakshya adhiniyam": "BSA",
        "evidence act": "BSA",
        "indian evidence act": "BSA",
        "cpc": "CPC",
    }
    CONCEPT_STOPWORDS = {
        "and",
        "are",
        "bns",
        "bnss",
        "compare",
        "comparison",
        "crpc",
        "difference",
        "explain",
        "for",
        "ipc",
        "legal",
        "of",
        "punishable",
        "punished",
        "punishment",
        "section",
        "the",
        "under",
        "what",
    }

    def __init__(
        self, collection_name=DEFAULT_COLLECTION, db_path=DB_PATH, collection=None
    ):
        self.collection_name = collection_name
        self.db_path = db_path
        self.embed_fn = None
        self.cross_encoder = None
        self.reranker_disabled = False
        self.semantic_disabled = False

        if collection is not None:
            self.collection = collection
        elif chromadb is None:
            self.chroma_client = None
            self.collection = None
            self.semantic_disabled = True
        else:
            self.chroma_client = chromadb.PersistentClient(path=db_path)

            # Use provider-specific collection if provider is configured
            provider = os.getenv("HECTOR_EMBEDDING_PROVIDER", "local")
            effective_collection = f"{collection_name}_{provider}"

            self.collection = self.chroma_client.get_or_create_collection(
                name=effective_collection,
            )

        self.records = []
        self.corpus = []
        self.tokenized_corpus = []
        self.bm25 = None
        self.refresh_index()

    @classmethod
    def from_records(cls, records):
        instance = cls.__new__(cls)
        instance.collection_name = "memory"
        instance.db_path = None
        instance.embed_fn = None
        instance.cross_encoder = None
        instance.reranker_disabled = True
        instance.semantic_disabled = True
        instance.collection = None
        instance.records = []
        instance.corpus = []
        instance.tokenized_corpus = []
        instance.bm25 = None
        instance._load_records(records)
        return instance

    def _load_records(self, records):
        self.records = []
        for index, record in enumerate(records):
            metadata = dict(record.get("metadata") or {})
            document = record.get("document", "")
            self.records.append(
                {
                    "id": record.get("id", f"record-{index}"),
                    "document": document,
                    "metadata": metadata,
                    "tokens": self._tokenize(document),
                    "citation": self._extract_document_citation(document, metadata),
                    "act": self._infer_act(document, metadata),
                }
            )

        self.corpus = [record["document"] for record in self.records]
        self.tokenized_corpus = [record["tokens"] for record in self.records]
        self.bm25 = SimpleBM25(self.tokenized_corpus) if self.records else None

    def refresh_index(self):
        if self.collection is None:
            return

        BATCH_SIZE = 5000
        all_documents = []
        all_metadatas = []
        all_ids = []
        offset = 0

        while True:
            results = retry(
                self.collection.get,
                include=["documents", "metadatas"],
                limit=BATCH_SIZE,
                offset=offset,
                operation_name="chromadb_get",
            )
            batch_docs = results.get("documents") or []
            batch_metas = results.get("metadatas") or []
            batch_ids = results.get("ids") or []

            all_documents.extend(batch_docs)
            all_metadatas.extend(batch_metas)
            all_ids.extend(batch_ids)

            if len(batch_docs) < BATCH_SIZE:
                break
            offset += BATCH_SIZE

        records = []
        for index, document in enumerate(all_documents):
            records.append(
                {
                    "id": all_ids[index] if index < len(all_ids) else f"record-{index}",
                    "document": document,
                    "metadata": all_metadatas[index]
                    if index < len(all_metadatas)
                    else {},
                }
            )

        self._load_records(records)

    def search(self, query, top_k=5, candidate_pool=20):
        if not self.records:
            return []

        candidate_pool = max(top_k, candidate_pool)
        legal_query = self._parse_query(query)

        # Parallelize BM25 and semantic search
        with ThreadPoolExecutor(max_workers=2) as executor:
            semantic_future = executor.submit(
                self._semantic_search, query, candidate_pool
            )
            bm25_future = executor.submit(
                self._bm25_search, legal_query["tokens"], candidate_pool
            )
            semantic_rank = semantic_future.result()
            bm25_rank = bm25_future.result()

        fused = self._fuse_rankings(semantic_rank, bm25_rank)
        ranked = self._score_candidates(fused, semantic_rank, bm25_rank, legal_query)
        deduped = self._deduplicate_results(ranked)
        reranked = self._rerank_with_cross_encoder(query, deduped)
        return reranked[:top_k]

    def search_with_metadata_filters(self, query, entities, top_k=5, candidate_pool=20):
        """Search with pre-filtering by section_number and real_act_name.

        When entity parser extracts a section number and/or act name, filter
        ChromaDB to ONLY chunks matching those metadata fields BEFORE ranking.
        This prevents "Section 302 query returns Section 304" false matches.
        Falls back to unfiltered search when no metadata filters available.
        """
        if not self.records or not entities:
            return self.search(query, top_k, candidate_pool)

        section_numbers = list(
            dict.fromkeys(
                (entities.get("sections") or [])
                + (entities.get("ipc_sections") or [])
                + (entities.get("bns_sections") or [])
            )
        )
        acts = list(dict.fromkeys(entities.get("acts") or []))

        if not section_numbers and not acts:
            return self.search(query, top_k, candidate_pool)

        where_filter = self._build_where_filter(section_numbers, acts)
        if where_filter is None:
            return self.search(query, top_k, candidate_pool)

        filtered_results = self._chroma_filtered_search(
            where_filter, top_k=min(candidate_pool, 200)
        )

        if not filtered_results and section_numbers:
            # Fallback 1: try section-only filter (without act filter)
            section_only_filter = (
                {"section_number": {"$eq": section_numbers[0]}}
                if len(section_numbers) == 1
                else {"$or": [{"section_number": {"$eq": s}} for s in section_numbers]}
            )
            filtered_results = self._chroma_filtered_search(
                section_only_filter, top_k=min(candidate_pool, 200)
            )

        if not filtered_results:
            # Fallback 2: unfiltered search as last resort
            return self.search(query, top_k, candidate_pool)

        legal_query = self._parse_query(query)

        # Parallelize filtered semantic and BM25 search
        with ThreadPoolExecutor(max_workers=2) as executor:
            semantic_future = executor.submit(
                self._semantic_search_with_filter,
                query,
                min(candidate_pool, 200),
                where_filter,
            )
            bm25_future = executor.submit(
                self._bm25_search_filtered, legal_query["tokens"], filtered_results
            )
            semantic_rank = semantic_future.result()
            bm25_rank = bm25_future.result()
        fused = self._fuse_rankings(semantic_rank, bm25_rank)
        ranked = self._score_candidates(fused, semantic_rank, bm25_rank, legal_query)
        deduped = self._deduplicate_results(ranked)
        reranked = self._rerank_with_cross_encoder(query, deduped)
        return reranked[:top_k]

    def _build_where_filter(self, section_numbers, acts):
        """Build a ChromaDB where clause for metadata filtering.

        Uses only $eq operators since $contains doesn't work with query().
        For act matching, maps abbreviations to exact real_act_name values.
        """
        if not section_numbers and not acts:
            return None

        conditions = []

        if section_numbers:
            if len(section_numbers) == 1:
                conditions.append({"section_number": {"$eq": section_numbers[0]}})
            else:
                conditions.append(
                    {"$or": [{"section_number": {"$eq": s}} for s in section_numbers]}
                )

        if acts:
            exact_act_names = self._resolve_act_to_exact_names(acts)
            if exact_act_names:
                if len(exact_act_names) == 1:
                    conditions.append({"real_act_name": {"$eq": exact_act_names[0]}})
                else:
                    conditions.append(
                        {
                            "$or": [
                                {"real_act_name": {"$eq": name}}
                                for name in exact_act_names
                            ]
                        }
                    )

        if not conditions:
            return None
        if len(conditions) == 1:
            return conditions[0]
        return {"$and": conditions}

    def _resolve_act_to_exact_names(self, acts):
        """Map act abbreviations to exact real_act_name values from the DB."""
        ACT_TO_EXACT = {
            "ipc": ["Indian Penal Code, 1860"],
            "indian penal code": ["Indian Penal Code, 1860"],
            "bns": ["Bharatiya Nyaya Sanhita, 2023"],
            "bharatiya nyaya sanhita": ["Bharatiya Nyaya Sanhita, 2023"],
            "crpc": ["Code of Criminal Procedure, 1973"],
            "code of criminal procedure": ["Code of Criminal Procedure, 1973"],
            "bnss": ["Bharatiya Nagarik Suraksha Sanhita, 2023"],
            "bharatiya nagarik suraksha sanhita": [
                "Bharatiya Nagarik Suraksha Sanhita, 2023"
            ],
            "bsa": [
                "Bharatiya Sakshya Adhiniyam, 2023",
                "erstwhile Indian Evidence Act, 1872",
                "Indian Evidence Act, 1872",
            ],
            "bharatiya sakshya adhiniyam": ["Bharatiya Sakshya Adhiniyam, 2023"],
            "evidence act": [
                "Bharatiya Sakshya Adhiniyam, 2023",
                "erstwhile Indian Evidence Act, 1872",
                "Indian Evidence Act, 1872",
            ],
            "indian evidence act": [
                "erstwhile Indian Evidence Act, 1872",
                "Indian Evidence Act, 1872",
            ],
            "cpc": ["Code of Civil Procedure, 1908"],
            "code of civil procedure": ["Code of Civil Procedure, 1908"],
            "transfer of property": ["Transfer of Property Act, 1882"],
            "transfer of property act": ["Transfer of Property Act, 1882"],
            "indian contract act": ["Indian Contract Act, 1872"],
            "consumer protection": ["Consumer Protection Act, 2019"],
            "consumer protection act": ["Consumer Protection Act, 2019"],
            "ndps": ["Narcotic Drugs and Psychotropic Substances Act, 1985"],
            "ndps act": ["Narcotic Drugs and Psychotropic Substances Act, 1985"],
            "motor vehicles": ["Motor Vehicles Act, 1988"],
            "motor vehicles act": ["Motor Vehicles Act, 1988"],
            "hindu succession": ["Hindu Succession Act, 1956"],
            "hindu succession act": ["Hindu Succession Act, 1956"],
            "hindu marriage": ["Hindu Marriage Act, 1955"],
            "hindu marriage act": ["Hindu Marriage Act, 1955"],
            "constitution": ["Constitution of India"],
            "constitution of india": ["Constitution of India"],
            "limitation": ["Limitation Act, 1963"],
            "limitation act": ["Limitation Act, 1963"],
            "arbitration": ["Arbitration and Conciliation Act, 1996"],
            "arbitration act": ["Arbitration and Conciliation Act, 1996"],
            "negotiable instruments": ["Negotiable Instruments Act, 1881"],
            "ni act": ["Negotiable Instruments Act, 1881"],
        }
        result = []
        for act in acts:
            key = act.lower().strip()
            exact_names = ACT_TO_EXACT.get(key)
            if exact_names:
                result.extend(exact_names)
            else:
                result.append(act)
        return list(dict.fromkeys(result))

    def _chroma_filtered_search(self, where_filter, top_k=200):
        """Get metadata-filtered results from ChromaDB without embeddings."""
        if self.collection is None:
            return []
        try:
            results = retry(
                self.collection.get,
                where=where_filter,
                limit=top_k,
                include=["documents", "metadatas"],
                operation_name="chroma_filtered_get",
            )
            documents = results.get("documents") or []
            metadatas = results.get("metadatas") or []
            ids = results.get("ids") or []
            return [
                {
                    "id": ids[i] if i < len(ids) else f"filtered-{i}",
                    "document": documents[i],
                    "metadata": metadatas[i] if i < len(metadatas) else {},
                }
                for i in range(len(documents))
            ]
        except Exception:
            return []

    def _semantic_search_with_filter(self, query, top_k, where_filter):
        """Semantic search with ChromaDB where clause pre-filter."""
        if self.collection is None or self.semantic_disabled:
            return []
        embed_fn = self._get_embedding_function()
        if embed_fn is None:
            return []
        query_embedding = embed_fn([query])[0]
        try:
            results = retry(
                self.collection.query,
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_filter,
                include=["documents", "metadatas", "distances"],
                operation_name="chroma_filtered_query",
            )
        except Exception:
            return self._semantic_search(query, top_k)

        ranked = []
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        ids = results.get("ids", [[]])[0] if results.get("ids") else []
        for index, document in enumerate(documents):
            ranked.append(
                {
                    "id": ids[index]
                    if index < len(ids)
                    else self._lookup_id(document, metadatas[index]),
                    "document": document,
                    "metadata": metadatas[index] if index < len(metadatas) else {},
                    "distance": distances[index] if index < len(distances) else None,
                    "rank": index + 1,
                }
            )
        return ranked

    def _bm25_search_filtered(self, query_tokens, filtered_results):
        """BM25 search over metadata-filtered subset only."""
        if not query_tokens or not filtered_results:
            return []
        filtered_tokens = [self._tokenize(r["document"]) for r in filtered_results]
        filtered_bm25 = SimpleBM25(filtered_tokens)
        scores = filtered_bm25.get_scores(query_tokens)
        scored_rows = []
        for index, score in enumerate(scores):
            if score <= 0:
                continue
            scored_rows.append((index, score))
        scored_rows.sort(key=lambda item: item[1], reverse=True)
        max_score = max((s for _, s in scored_rows), default=1.0)
        min_score = min((s for _, s in scored_rows), default=0.0)
        ranked = []
        for rank, (index, score) in enumerate(scored_rows[:200], start=1):
            result = filtered_results[index]
            normalized = self._normalize_bm25_score(score, min_score, max_score)
            ranked.append(
                {
                    "id": result["id"],
                    "document": result["document"],
                    "metadata": result["metadata"],
                    "score": score,
                    "normalized_score": normalized,
                    "rank": rank,
                }
            )
        return ranked

    def _tokenize(self, text):
        return self.TOKEN_PATTERN.findall((text or "").lower())

    def _parse_query(self, query):
        sections = [
            match.lower().rstrip(".")
            for match in self.SECTION_PATTERN.findall(query or "")
        ]
        raw_acts = [
            match.group(0).lower() for match in self.ACT_PATTERN.finditer(query or "")
        ]
        acts = [self.ACT_ALIASES.get(act, act.upper()) for act in raw_acts]

        return {
            "raw": query,
            "tokens": self._tokenize(query),
            "section_numbers": list(dict.fromkeys(sections)),
            "acts": list(dict.fromkeys(acts)),
            "concept_terms": self._extract_concept_terms(query),
            "has_legal_citation": bool(sections or acts),
        }

    def _semantic_search(self, query, top_k):
        if self.collection is None or self.semantic_disabled:
            return []

        embed_fn = self._get_embedding_function()
        if embed_fn is None:
            return []

        query_embedding = embed_fn([query])[0]
        results = retry(
            self.collection.query,
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
            operation_name="chromadb_query",
        )

        ranked = []
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        ids = results.get("ids", [[]])[0] if results.get("ids") else []

        for index, document in enumerate(documents):
            ranked.append(
                {
                    "id": ids[index]
                    if index < len(ids)
                    else self._lookup_id(document, metadatas[index]),
                    "document": document,
                    "metadata": metadatas[index] if index < len(metadatas) else {},
                    "distance": distances[index] if index < len(distances) else None,
                    "rank": index + 1,
                }
            )
        return ranked

    def _bm25_search(self, query_tokens, top_k):
        if not self.bm25 or not query_tokens:
            return []

        scores = self.bm25.get_scores(query_tokens)
        positive_scores = [score for score in scores if score > 0]
        min_score = min(positive_scores, default=0.0)
        max_score = max(positive_scores, default=0.0)

        scored_rows = []
        for index, score in enumerate(scores):
            if score <= 0:
                continue
            normalized_score = self._normalize_bm25_score(score, min_score, max_score)
            scored_rows.append((index, score, normalized_score))

        scored_rows.sort(key=lambda item: item[1], reverse=True)
        ranked = []
        for rank, (index, score, normalized_score) in enumerate(
            scored_rows[:top_k], start=1
        ):
            record = self.records[index]
            ranked.append(
                {
                    "id": record["id"],
                    "document": record["document"],
                    "metadata": record["metadata"],
                    "score": score,
                    "normalized_score": normalized_score,
                    "rank": rank,
                }
            )
        return ranked

    def _fuse_rankings(self, semantic_rank, bm25_rank, k=60):
        fused = {}
        for source_name, ranking in (("semantic", semantic_rank), ("bm25", bm25_rank)):
            for item in ranking:
                doc_id = item["id"]
                entry = fused.setdefault(
                    doc_id,
                    {
                        "id": doc_id,
                        "document": item["document"],
                        "metadata": item["metadata"],
                        "rrf_score": 0.0,
                        "sources": {},
                    },
                )
                entry["sources"][source_name] = item
                entry["rrf_score"] += 1.0 / (k + item["rank"])
        return fused

    def _score_candidates(self, fused, semantic_rank, bm25_rank, legal_query):
        semantic_lookup = {item["id"]: item for item in semantic_rank}
        bm25_lookup = {item["id"]: item for item in bm25_rank}

        semantic_max_distance = max(
            (
                item["distance"]
                for item in semantic_rank
                if item.get("distance") is not None
            ),
            default=1.0,
        )
        ranked = []
        for doc_id, candidate in fused.items():
            record = self._get_record(
                doc_id, candidate["document"], candidate["metadata"]
            )

            semantic_item = semantic_lookup.get(doc_id)
            semantic_score = self._normalize_semantic_score(
                semantic_item.get("distance") if semantic_item else None,
                semantic_max_distance,
            )

            bm25_item = bm25_lookup.get(doc_id)
            bm25_score = bm25_item["normalized_score"] if bm25_item else 0.0

            legal_boost, boost_reasons = self._legal_boost(record, legal_query)
            concept_boost, concept_reason = self._concept_term_boost(
                record, legal_query
            )
            current_law_boost, current_law_reason = self._current_law_boost(
                record, legal_query
            )
            jurisdiction_boost, jurisdiction_reason = self._jurisdiction_recency_boost(
                record
            )
            source_type_boost, source_type_reason = self._source_type_boost(record)

            retrieval_score = candidate["rrf_score"]
            boost_score = (
                legal_boost
                + concept_boost
                + current_law_boost
                + jurisdiction_boost
                + source_type_boost
            )
            hybrid_score = retrieval_score + boost_score

            reasons = [
                reason
                for reason in [
                    "semantic-hit" if semantic_item else None,
                    "bm25-hit" if bm25_item else None,
                    concept_reason,
                    current_law_reason,
                    jurisdiction_reason,
                    source_type_reason,
                ]
                if reason
            ]
            reasons.extend(boost_reasons)

            ranked.append(
                {
                    "id": doc_id,
                    "document": record["document"],
                    "metadata": record["metadata"],
                    "score": round(hybrid_score, 6),
                    "hybrid_score": round(hybrid_score, 6),
                    "retrieval_score": round(retrieval_score, 6),
                    "boost_score": round(boost_score, 6),
                    "rrf_score": round(candidate["rrf_score"], 6),
                    "semantic_score": round(semantic_score, 6),
                    "bm25_score": round(bm25_score, 6),
                    "bm25_raw_score": round(bm25_item["score"], 6)
                    if bm25_item
                    else 0.0,
                    "act": record["act"],
                    "citation": record["citation"],
                    "reasons": reasons,
                }
            )

        ranked.sort(
            key=lambda item: item["retrieval_score"] + item["boost_score"], reverse=True
        )
        return ranked

    def _normalize_bm25_score(self, raw_score, min_score, max_score):
        if max_score <= min_score:
            return 1.0 if raw_score > 0 else 0.0
        normalized = (raw_score - min_score) / (max_score - min_score)
        return max(0.0, min(normalized, 1.0))

    def _rerank_with_cross_encoder(self, query, candidates):
        if not candidates:
            return []

        # Try provider abstraction first
        if get_rerank_provider is not None:
            try:
                provider = os.getenv("HECTOR_RERANK_PROVIDER", "local")
                if provider == "nemotron":
                    reranker = get_rerank_provider("nemotron")
                    return reranker.rerank(query, candidates)
            except Exception:
                pass  # Fall through to local reranker

        reranker = self._get_cross_encoder()
        if reranker is not None:
            pairs = [(query, item["document"]) for item in candidates]
            raw_scores = reranker.predict(pairs)
            for item, raw_score in zip(candidates, raw_scores):
                reranker_score = self._sigmoid(float(raw_score))
                item["reranker_score"] = round(reranker_score, 6)
                item["score"] = item["reranker_score"]
                item["similarity_score"] = item["reranker_score"]
                item["reasons"] = [*item.get("reasons", []), "cross-encoder-reranked"]
        else:
            for item in candidates:
                fallback_score = self._fallback_reranker_score(item)
                item["reranker_score"] = round(fallback_score, 6)
                item["score"] = item["reranker_score"]
                item["similarity_score"] = item["reranker_score"]
                item["reasons"] = [
                    *item.get("reasons", []),
                    "cross-encoder-unavailable",
                ]

        candidates.sort(key=lambda item: item["reranker_score"], reverse=True)
        return candidates

    def _get_cross_encoder(self):
        if self.cross_encoder is not None:
            return self.cross_encoder
        if self.reranker_disabled:
            return None
        if CrossEncoder is None:
            self.reranker_disabled = True
            return None

        try:
            os.environ.setdefault("HF_HUB_OFFLINE", "1")
            model_name = os.getenv(
                "HECTOR_CROSS_ENCODER_MODEL", DEFAULT_CROSS_ENCODER_MODEL
            )
            self.cross_encoder = CrossEncoder(model_name)
            return self.cross_encoder
        except Exception:
            self.reranker_disabled = True
            return None

    def _fallback_reranker_score(self, item):
        base = (
            item.get("rrf_score", 0.0) * 12.0
            + item.get("bm25_score", 0.0) * 0.30
            + item.get("semantic_score", 0.0) * 0.25
            + item.get("boost_score", 0.0)
        )
        return max(0.0, min(base, 1.0))

    @staticmethod
    def _sigmoid(value):
        if value >= 0:
            z = math.exp(-value)
            return 1 / (1 + z)
        z = math.exp(value)
        return z / (1 + z)

    def _legal_boost(self, record, legal_query):
        boost = 0.0
        reasons = []

        document = record["document"]
        act = record["act"]
        citation = record["citation"]
        query_sections = legal_query["section_numbers"]
        query_acts = legal_query["acts"]

        if query_acts and act in query_acts:
            boost += 0.10
            reasons.append(f"act-match:{act}")

        if query_sections and citation and citation["section"] in query_sections:
            boost += 0.22
            reasons.append(f"section-match:{citation['section']}")

        if (
            query_acts
            and query_sections
            and act in query_acts
            and citation
            and citation["section"] in query_sections
        ):
            boost += 0.18
            reasons.append(f"citation-match:{act}-{citation['section']}")

        if query_sections and self._contains_section_reference(
            document, query_sections
        ):
            boost += 0.08
            reasons.append("section-text-hit")

        return boost, reasons

    def _extract_concept_terms(self, query):
        terms = []
        for token in self._tokenize(query):
            if len(token) < 4 or token in self.CONCEPT_STOPWORDS:
                continue
            terms.append(token)
        return list(dict.fromkeys(terms))

    def _concept_term_boost(self, record, legal_query):
        concept_terms = legal_query.get("concept_terms") or []
        if not concept_terms:
            return 0.0, None

        raw_query = (legal_query.get("raw") or "").lower()
        haystack = " ".join(
            str(value)
            for value in [
                record.get("document", ""),
                record.get("metadata", {}).get("source", ""),
                record.get("metadata", {}).get("act_name", ""),
                record.get("metadata", {}).get("section_title", ""),
            ]
        ).lower()
        matched = [
            term
            for term in concept_terms
            if re.search(rf"\b{re.escape(term)}\b", haystack)
        ]

        if "punishment" in raw_query:
            for term in matched:
                if (
                    f"punishment for {term}" in haystack
                    or f"{term} shall be punished" in haystack
                ):
                    return 0.34, f"concept-punishment-match:{term}"

        if len(matched) == len(concept_terms):
            return 0.24, f"concept-match:{','.join(matched)}"
        if matched:
            return 0.12, f"concept-partial:{','.join(matched)}"
        return -0.10, "concept-missing"

    def _current_law_boost(self, record, legal_query):
        if not legal_query["has_legal_citation"]:
            return 0.0, None

        act = record["act"]
        if act == "BNS":
            return 0.06, "current-law-preferred"
        if act == "IPC" and "BNS" in legal_query["acts"]:
            return -0.04, "legacy-law-deprioritized"
        return 0.0, None

    def _normalize_semantic_score(self, distance, max_distance):
        if distance is None:
            return 0.0
        max_distance = max(max_distance, 1e-9)
        bounded = min(max(distance / max_distance, 0.0), 1.0)
        return 1.0 - bounded

    def _jurisdiction_recency_boost(self, record):
        metadata = record["metadata"]
        jurisdiction = str(metadata.get("jurisdiction", "")).strip().lower()
        date_value = (
            metadata.get("decision_date")
            or metadata.get("effective_date")
            or metadata.get("amended_at")
        )

        boost = 0.0
        reasons = []

        if "supreme court" in jurisdiction:
            boost += 0.03
            reasons.append("jurisdiction:sc")
        elif "high court" in jurisdiction:
            boost += 0.015
            reasons.append("jurisdiction:hc")

        parsed_date = self._parse_date(date_value)
        if parsed_date is not None:
            age_days = max((datetime.now().date() - parsed_date).days, 0)
            boost += max(0.0, 0.03 - min(age_days / 3650, 0.03))
            reasons.append(f"recency:{parsed_date.isoformat()}")

        return boost, ", ".join(reasons) if reasons else None

    def _source_type_boost(self, record):
        """Boost Bare Act text over commentary. Primary sources are authoritative."""
        metadata = record.get("metadata", {})
        source_type = metadata.get("source_type", "")
        if source_type == "bare_act":
            return 0.05, "source:bare-act"
        if source_type == "commentary":
            return -0.02, "source:commentary"
        return 0.0, None

    def _deduplicate_results(self, ranked_results):
        deduped = []
        seen_keys = set()

        for item in ranked_results:
            metadata = item["metadata"]
            page_hash = metadata.get("page_hash")
            normalized_document = " ".join(item["document"].split()).lower()[:300]
            dedupe_key = page_hash or (
                metadata.get("source"),
                metadata.get("page"),
                normalized_document,
            )
            if dedupe_key in seen_keys:
                continue
            seen_keys.add(dedupe_key)
            deduped.append(item)

        return deduped

    def format_results(self, results):
        if not results:
            return "No grounded legal results found in the indexed corpus."

        lines = []
        for index, result in enumerate(results, start=1):
            metadata = result["metadata"]
            citation = result.get("citation") or {}
            source = metadata.get("source", "Unknown Source")
            page = metadata.get("page", "?")
            label_parts = [source, f"page {page}"]

            if result.get("act"):
                label_parts.append(result["act"])
            if citation.get("section"):
                label_parts.append(f"section {citation['section']}")

            snippet = self._snippet(result["document"])
            lines.append(
                f"{index}. {' | '.join(label_parts)}\n"
                f"   score={result['score']:.3f} reasons={', '.join(result['reasons']) or 'retrieved'}\n"
                f"   {snippet}"
            )
        return "\n\n".join(lines)

    def _lookup_id(self, document, metadata):
        metadata = metadata or {}
        for record in self.records:
            if record["document"] == document and record["metadata"] == metadata:
                return record["id"]
        return f"lookup-{hash((document, tuple(sorted(metadata.items()))))}"

    def _get_record(self, doc_id, document, metadata):
        for record in self.records:
            if record["id"] == doc_id:
                return record
        return {
            "id": doc_id,
            "document": document,
            "metadata": metadata or {},
            "citation": self._extract_document_citation(document, metadata or {}),
            "act": self._infer_act(document, metadata or {}),
        }

    def _extract_document_citation(self, document, metadata):
        section = None
        bracket_match = re.search(
            r"\[s\s*(\d{1,4}[a-z]?)(?:\.\d+)?\]", document or "", re.IGNORECASE
        )
        match = self.SECTION_IN_TEXT_PATTERN.search(document or "")
        if bracket_match:
            section = bracket_match.group(1).lower()
        elif match:
            section = (match.group(1) or match.group(2) or match.group(3) or "").lower()
        return {
            "section": section,
            "page": metadata.get("page"),
            "source": metadata.get("source"),
        }

    def _infer_act(self, document, metadata):
        explicit_act = str(
            metadata.get("act_name") or metadata.get("act") or ""
        ).strip()
        if explicit_act:
            canonical = self.ACT_ALIASES.get(explicit_act.lower(), explicit_act.upper())
            return canonical

        source = (metadata.get("source") or "").lower()
        text = (document or "").lower()
        combined = f"{source} {text[:300]}"

        for alias, canonical in self.ACT_ALIASES.items():
            if alias in combined:
                return canonical

        if "evidence" in combined and "bharatiya" in combined:
            return "BSA"
        return None

    def _contains_section_reference(self, document, query_sections):
        lowered = (document or "").lower()
        for section in query_sections:
            if re.search(
                rf"\b(?:section|sec\.?|s\.)\s*{re.escape(section)}\b", lowered
            ):
                return True
            if re.search(rf"^\s*{re.escape(section)}\.\s", lowered, re.MULTILINE):
                return True
        return False

    def _snippet(self, document, limit=280):
        clean = " ".join((document or "").split())
        if len(clean) <= limit:
            return clean
        return clean[: limit - 3].rstrip() + "..."

    def _parse_date(self, value):
        if not value:
            return None
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%Y"):
            try:
                return datetime.strptime(str(value), fmt).date()
            except ValueError:
                continue
        return None

    def _get_embedding_function(self):
        if self.embed_fn is not None:
            return self.embed_fn
        if self.semantic_disabled:
            return None

        try:
            # Try provider abstraction first
            if get_embedding_provider is not None:
                provider = os.getenv("HECTOR_EMBEDDING_PROVIDER", "local")
                if provider == "nemotron":
                    embedder = get_embedding_provider("nemotron")
                    self.embed_fn = embedder.get_chroma_embedding_function()
                    return self.embed_fn

            # Fall back to default local embedding
            if embedding_functions is None:
                self.semantic_disabled = True
                return None
            os.environ.setdefault("HF_HUB_OFFLINE", "1")
            self.embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
            return self.embed_fn
        except Exception:
            self.semantic_disabled = True
            return None
