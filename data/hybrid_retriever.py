import math
import os
import re
from collections import Counter, defaultdict
from datetime import datetime

try:
    import chromadb
    from chromadb.utils import embedding_functions
except ImportError:
    chromadb = None
    embedding_functions = None


DB_PATH = "./hector_db"
DEFAULT_COLLECTION = "indian_law_bns"


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
        for frequencies, doc_length in zip(self.term_frequencies, self.document_lengths):
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
    SECTION_PATTERN = re.compile(r"\b(?:section|sec\.?|s\.)\s*(\d{1,4}[a-z]?)\b", re.IGNORECASE)
    ACT_PATTERN = re.compile(
        r"\b(ipc|bns|crpc|bnss|bsa|cpc|bharatiya nyaya sanhita|bharatiya nagarik suraksha sanhita|bharatiya sakshya adhiniyam|indian penal code|code of criminal procedure|evidence act|indian evidence act)\b",
        re.IGNORECASE,
    )
    TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
    SECTION_IN_TEXT_PATTERN = re.compile(
        r"\b(?:section|sec\.?|s\.)\s*(\d{1,4}[a-z]?)\b|^\s*(\d{1,4}[a-z]?)\.\s",
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

    def __init__(self, collection_name=DEFAULT_COLLECTION, db_path=DB_PATH, collection=None):
        self.collection_name = collection_name
        self.db_path = db_path
        self.embed_fn = None
        self.semantic_disabled = False

        if collection is not None:
            self.collection = collection
        elif chromadb is None:
            self.chroma_client = None
            self.collection = None
            self.semantic_disabled = True
        else:
            self.chroma_client = chromadb.PersistentClient(path=db_path)
            self.collection = self.chroma_client.get_or_create_collection(
                name=collection_name,
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

        results = self.collection.get(include=["documents", "metadatas"])
        documents = results.get("documents") or []
        metadatas = results.get("metadatas") or []
        ids = results.get("ids") or []

        records = []
        for index, document in enumerate(documents):
            records.append(
                {
                    "id": ids[index] if index < len(ids) else f"record-{index}",
                    "document": document,
                    "metadata": metadatas[index] if index < len(metadatas) else {},
                }
            )

        self._load_records(records)

    def search(self, query, top_k=5, candidate_pool=20):
        if not self.records:
            return []

        candidate_pool = max(top_k, candidate_pool)
        legal_query = self._parse_query(query)

        semantic_rank = self._semantic_search(query, candidate_pool)
        bm25_rank = self._bm25_search(legal_query["tokens"], candidate_pool)
        fused = self._fuse_rankings(semantic_rank, bm25_rank)
        ranked = self._score_candidates(fused, semantic_rank, bm25_rank, legal_query)
        deduped = self._deduplicate_results(ranked)
        return deduped[:top_k]

    def _tokenize(self, text):
        return self.TOKEN_PATTERN.findall((text or "").lower())

    def _parse_query(self, query):
        sections = [
            match.lower().rstrip(".")
            for match in self.SECTION_PATTERN.findall(query or "")
        ]
        raw_acts = [match.group(0).lower() for match in self.ACT_PATTERN.finditer(query or "")]
        acts = [self.ACT_ALIASES.get(act, act.upper()) for act in raw_acts]

        return {
            "raw": query,
            "tokens": self._tokenize(query),
            "section_numbers": list(dict.fromkeys(sections)),
            "acts": list(dict.fromkeys(acts)),
            "has_legal_citation": bool(sections or acts),
        }

    def _semantic_search(self, query, top_k):
        if self.collection is None or self.semantic_disabled:
            return []

        embed_fn = self._get_embedding_function()
        if embed_fn is None:
            return []

        query_embedding = embed_fn([query])[0]
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        ranked = []
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        ids = results.get("ids", [[]])[0] if results.get("ids") else []

        for index, document in enumerate(documents):
            ranked.append(
                {
                    "id": ids[index] if index < len(ids) else self._lookup_id(document, metadatas[index]),
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
        scored_rows = []
        for index, score in enumerate(scores):
            if score <= 0:
                continue
            scored_rows.append((index, score))

        scored_rows.sort(key=lambda item: item[1], reverse=True)
        ranked = []
        for rank, (index, score) in enumerate(scored_rows[:top_k], start=1):
            record = self.records[index]
            ranked.append(
                {
                    "id": record["id"],
                    "document": record["document"],
                    "metadata": record["metadata"],
                    "score": score,
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
        bm25_max_score = max((item["score"] for item in bm25_rank), default=1.0)

        ranked = []
        for doc_id, candidate in fused.items():
            record = self._get_record(doc_id, candidate["document"], candidate["metadata"])

            semantic_item = semantic_lookup.get(doc_id)
            semantic_score = self._normalize_semantic_score(
                semantic_item.get("distance") if semantic_item else None,
                semantic_max_distance,
            )

            bm25_item = bm25_lookup.get(doc_id)
            bm25_score = (
                bm25_item["score"] / bm25_max_score if bm25_item and bm25_max_score else 0.0
            )

            legal_boost, boost_reasons = self._legal_boost(record, legal_query)
            current_law_boost, current_law_reason = self._current_law_boost(record, legal_query)
            jurisdiction_boost, jurisdiction_reason = self._jurisdiction_recency_boost(record)

            final_score = (
                candidate["rrf_score"] * 0.45
                + semantic_score * 0.20
                + bm25_score * 0.20
                + legal_boost
                + current_law_boost
                + jurisdiction_boost
            )

            reasons = [
                reason
                for reason in [
                    "semantic-hit" if semantic_item else None,
                    "bm25-hit" if bm25_item else None,
                    current_law_reason,
                    jurisdiction_reason,
                ]
                if reason
            ]
            reasons.extend(boost_reasons)

            ranked.append(
                {
                    "id": doc_id,
                    "document": record["document"],
                    "metadata": record["metadata"],
                    "score": round(final_score, 6),
                    "rrf_score": round(candidate["rrf_score"], 6),
                    "semantic_score": round(semantic_score, 6),
                    "bm25_score": round(bm25_score, 6),
                    "act": record["act"],
                    "citation": record["citation"],
                    "reasons": reasons,
                }
            )

        ranked.sort(key=lambda item: item["score"], reverse=True)
        return ranked

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

        if query_acts and query_sections and act in query_acts and citation and citation["section"] in query_sections:
            boost += 0.18
            reasons.append(f"citation-match:{act}-{citation['section']}")

        if query_sections and self._contains_section_reference(document, query_sections):
            boost += 0.08
            reasons.append("section-text-hit")

        return boost, reasons

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

    def _deduplicate_results(self, ranked_results):
        deduped = []
        seen_keys = set()

        for item in ranked_results:
            metadata = item["metadata"]
            page_hash = metadata.get("page_hash")
            normalized_document = " ".join(item["document"].split()).lower()[:300]
            dedupe_key = page_hash or (metadata.get("source"), metadata.get("page"), normalized_document)
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
        match = self.SECTION_IN_TEXT_PATTERN.search(document or "")
        if match:
            section = (match.group(1) or match.group(2) or "").lower()
        return {
            "section": section,
            "page": metadata.get("page"),
            "source": metadata.get("source"),
        }

    def _infer_act(self, document, metadata):
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
            if re.search(rf"\b(?:section|sec\.?|s\.)\s*{re.escape(section)}\b", lowered):
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
