import json
import logging
import math
import os
import re
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

from utils.retry import retry

logger = logging.getLogger(__name__)

try:
    from pinecone import Pinecone
except ImportError:
    Pinecone = None


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# Single index for v2 records. Keep this in sync with step9_push.INDEX_NAME,
# eval fast_recall.DEFAULT_INDEX and bench_retrieval's HECTOR_EVAL_INDEX
# default - three stale spellings (hector-legal / hector-legal-v2) previously
# pointed at indexes that no longer exist, and because this module AUTO-CREATES
# a missing index, the wrong name would have silently spawned a stray empty
# index on the account.
DEFAULT_INDEX_NAME = os.getenv("HECTOR_EVAL_INDEX", "hector")
DEFAULT_COLLECTION = "indian_law_bns"
EMBEDDING_MODEL = "multilingual-e5-large"
EMBEDDING_DIM = 2048
EMBED_NIM_MODEL = "nvidia/nemotron-3-embed-1b"
# Share of the returned slots a single-act query gets to reserve for its own
# act (see _apply_same_act_floor). 0.5 -> 5 of the default top-10.
SAME_ACT_FLOOR_RATIO = 0.5
# Shared keep-alive client for NIM embeddings (see _embed_text).
_EMBED_CLIENT = None

# IPC<->BNS crosswalk from core/mapping.json["IPC_TO_BNS"] - the same table
# router._load_mapping() exposes as legal_map and compare() uses to pick
# counterpart panels. Loaded once per process; (forward, reverse) with
# section numbers normalized UPPER.
_MAPPING_PATH = Path(__file__).resolve().parents[1] / "core" / "mapping.json"
_mapping_cache = None


def _load_ipc_bns_crosswalk():
    global _mapping_cache
    if _mapping_cache is None:
        forward, reverse = {}, {}
        try:
            with open(_MAPPING_PATH, encoding="utf-8") as fh:
                raw = json.load(fh).get("IPC_TO_BNS") or {}
            for old, info in raw.items():
                new = str((info or {}).get("new") or "").strip().upper()
                old_key = str(old).strip().upper()
                if not new or not old_key:
                    continue
                forward.setdefault(old_key, []).append(new)
                reverse.setdefault(new, []).append(old_key)
        except Exception as exc:
            logger.warning(
                "mapping.json crosswalk unavailable (%s) - "
                "counterpart injection disabled",
                exc,
            )
        _mapping_cache = (forward, reverse)
    return _mapping_cache


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
    LEGAL_INTENT_KEYWORDS = frozenset(
        (
            "section", "ipc", "bns", "crpc", "bnss", "bsa", "cpc", "act",
            "court", "judge", "justice", "law", "legal", "statute", "code",
            "murder", "theft", "assault", "rape", "fraud", "forgery", "cheating",
            "bail", "arrest", "custody", "fir", "charge", "accused", "conviction",
            "acquittal", "sentence", "punishment", "imprisonment", "fine",
            "plaintiff", "defendant", "petition", "writ", "appeal", "judgment",
            "dowry", "cruelty", "divorce", "maintenance", "alimony", "adoption",
            "guardian", "succession", "inheritance", "will", "probate", "contract",
            "agreement", "consideration", "void", "voidable", "negligence",
            "liability", "damages", "compensation", "injunction", "mortgage",
            "lease", "rent", "eviction", "trespass", "partition", "consumer",
            "wages", "employer", "employee", "termination", "industrial", "labour",
            "labor", "drunk", "driving", "narcotic", "ndps", "cyber", "digital",
            "electronic", "evidence", "witness", "confession", "admissible",
            "admissibility", "interrogation", "right to", "fundamental right",
            "article", "constitutional", "high court", "supreme court", "tribunal",
            "crime", "offence", "offense", "criminal", "cognizable", "bailable",
            "remedy", "relief", "claim", "dispute", "case", "suit",
            "stole", "steal", "stealing", "stolen", "robbed", "robbery", "rob",
            "killed", "killing", "kill", "stabbed", "stab", "hit", "struck",
            "damaged", "vandalized", "broke", "broken", "snatched", "snatch",
            "picked", "pocket", "burglary", "break-in", "trespassing",
            "dupe", "scam", "defraud", "blackmail", "extortion", "bribery",
            "bike", "vehicle", "car", "motorcycle", "scooter", "property",
            "silencer", "battery", "wheel", "part", "component",
            "file", "complaint", "police", "station", "ipc section", "bns section",
            "punishable", "imprisonment", "jail", "prison",
        )
    )

    CONCEPT_STOPWORDS = {
        "and", "are", "bns", "bnss", "compare", "comparison", "crpc",
        "difference", "explain", "for", "ipc", "legal", "of", "punishable",
        "punished", "punishment", "section", "the", "under", "what",
    }

    ACT_TO_EXACT = {
        "ipc": ["Indian Penal Code, 1860"],
        "indian penal code": ["Indian Penal Code, 1860"],
        "bns": ["Bharatiya Nyaya Sanhita, 2023"],
        "bharatiya nyaya sanhita": ["Bharatiya Nyaya Sanhita, 2023"],
        "crpc": ["Code of Criminal Procedure, 1973"],
        "code of criminal procedure": ["Code of Criminal Procedure, 1973"],
        "bnss": ["Bharatiya Nagarik Suraksha Sanhita, 2023"],
        "bharatiya nagarik suraksha sanhita": ["Bharatiya Nagarik Suraksha Sanhita, 2023"],
        "bsa": ["Bharatiya Sakshya Adhiniyam, 2023", "erstwhile Indian Evidence Act, 1872", "Indian Evidence Act, 1872"],
        "bharatiya sakshya adhiniyam": ["Bharatiya Sakshya Adhiniyam, 2023"],
        "evidence act": ["Bharatiya Sakshya Adhiniyam, 2023", "erstwhile Indian Evidence Act, 1872", "Indian Evidence Act, 1872"],
        "indian evidence act": ["erstwhile Indian Evidence Act, 1872", "Indian Evidence Act, 1872"],
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

    def __init__(
        self, collection_name=DEFAULT_COLLECTION, index_name=DEFAULT_INDEX_NAME, collection=None
    ):
        self.collection_name = collection_name
        self.index_name = index_name
        self.embed_fn = None
        self.cross_encoder = None
        self.reranker_disabled = False
        self.semantic_disabled = False
        self._pc = None
        self._index = None
        self._records_path = None

        if collection is not None:
            self.collection = collection
            self.pinecone_index = None
        else:
            self.collection = None
            self._init_pinecone()
            records_path = self._resolve_records_path()
            if records_path:
                self._records_path = records_path
            else:
                # No local eval corpus on disk: attach the 13k chroma store
                # as dense leg + record fallback (ingest/dev layout).
                self._attach_local_collection()

        self.records = []
        self.corpus = []
        self.tokenized_corpus = []
        self.bm25 = None
        self.last_search_mode = None
        self.last_stage_info = None
        if (
            self.collection is not None
            or self.pinecone_index is not None
            or self._records_path is not None
        ):
            self.refresh_index()

    def _init_pinecone(self):
        if Pinecone is None:
            self.pinecone_index = None
            self.semantic_disabled = True
            return
        api_key = os.getenv("PINECONE_API_KEY", "")
        if not api_key:
            self.pinecone_index = None
            self.semantic_disabled = True
            return
        try:
            self._pc = Pinecone(api_key=api_key)
            existing = [idx.name for idx in self._pc.list_indexes()]
            if self.index_name not in existing:
                self._pc.create_index(
                    name=self.index_name,
                    dimension=EMBEDDING_DIM,
                    metric="cosine",
                    spec={"serverless": {"cloud": "aws", "region": "us-east-1"}},
                )
                time.sleep(5)
            self.pinecone_index = self._pc.Index(self.index_name)
        except Exception:
            self.pinecone_index = None
            self.semantic_disabled = True

    @property
    def _pinecone(self):
        return getattr(self, "pinecone_index", None)

    def _pinecone_unusable(self) -> bool:
        """True when the Pinecone data plane must be skipped (Round 2)."""
        return bool(getattr(self, "_pinecone_dead", False))

    def _attach_local_collection(self):
        """Attach the local Chroma collection as dense-leg + record source.

        Resolution order: HECTOR_LOCAL_CHROMA_PATH/COLLECTION env overrides,
        then the project's indian_law_bns_local store, then collection_name.
        Best-effort: any failure leaves self.collection None and the retriever
        degrades to BM25-only (previous behaviour).
        """
        if self.collection is not None:
            return
        try:
            import chromadb
        except Exception as exc:
            logger.info("chromadb unavailable for local dense leg: %s", exc)
            return
        try:
            default_path = str(Path(__file__).resolve().parents[3] / "hector_db")
            db_path = os.getenv("HECTOR_LOCAL_CHROMA_PATH", default_path)
            if not os.path.isdir(db_path):
                logger.info("local chroma path not found: %s", db_path)
                return
            client = chromadb.PersistentClient(path=db_path)
            names = []
            env_name = os.getenv("HECTOR_LOCAL_CHROMA_COLLECTION")
            if env_name:
                names.append(env_name)
            names.extend(["indian_law_bns_local", self.collection_name])
            for name in dict.fromkeys(names):
                try:
                    coll = client.get_collection(name)
                except Exception:
                    continue
                self.collection = coll
                logger.info(
                    "attached local chroma collection %s (%d vectors)",
                    name,
                    coll.count(),
                )
                return
        except Exception as exc:
            logger.warning("local chroma attach failed: %s", exc)

    def _load_local_records(self) -> list[dict]:
        """Load full records (for BM25) from the local Chroma store."""
        coll = self.collection
        if coll is None:
            return []
        records: list[dict] = []
        try:
            batch = 1000
            offset = 0
            while True:
                page = coll.get(
                    include=["documents", "metadatas"], limit=batch, offset=offset
                )
                docs = page.get("documents") or []
                if not docs:
                    break
                metas = page.get("metadatas") or []
                ids = page.get("ids") or []
                for rid, doc, meta in zip(ids, docs, metas):
                    records.append(
                        {
                            "id": rid,
                            "document": doc or "",
                            "metadata": meta or {},
                        }
                    )
                offset += len(docs)
                if len(docs) < batch:
                    break
            logger.info("loaded %d records from local chroma", len(records))
        except Exception as exc:
            logger.warning("local record load failed: %s", exc)
            return []
        return records

    def _resolve_records_path(self) -> str | None:
        """Locate the 945-record eval corpus. Empty env value disables it."""
        env = os.getenv("HECTOR_LOCAL_RECORDS_PATH")
        if env is not None:
            return env.strip() or None
        here = Path(__file__).resolve()
        candidates = [
            here.parents[3]
            / "hector"
            / "backend"
            / "ingest_v2"
            / "output"
            / "eval_corpus.jsonl",
            here.parents[2]
            / "backend"
            / "ingest_v2"
            / "output"
            / "eval_corpus.jsonl",
        ]
        for path in candidates:
            if path.is_file():
                return str(path)
        return None

    @staticmethod
    def _load_jsonl_records(path: str) -> list[dict]:
        rows: list[dict] = []
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                rows.append(
                    {
                        "id": row.get("id", ""),
                        "document": row.get("document", ""),
                        "metadata": row.get("metadata") or {},
                    }
                )
        if not rows:
            raise ValueError(f"no records in {path}")
        return rows

    def _dense_matrix(self):
        """Precomputed NIM embeddings for the local corpus (ids, unit matrix)."""
        if hasattr(self, "_dense_matrix_cache"):
            return self._dense_matrix_cache
        store = None
        env = os.getenv("HECTOR_LOCAL_EMB_PATH")
        records_path = getattr(self, "_records_path", None) or self._resolve_records_path()
        candidates: list[Path] = []
        if env:
            candidates.append(Path(env))
        elif records_path:
            candidates.append(Path(records_path).with_name("eval_corpus_embs.npz"))
        for path in candidates:
            if not path.is_file():
                continue
            try:
                import numpy as np

                data = np.load(str(path), allow_pickle=False)
                model = ""
                if "model" in data.files:
                    model = str(data["model"])
                if model and model != EMBED_NIM_MODEL:
                    logger.warning(
                        "dense matrix %s built with %s (want %s) — skipping",
                        path,
                        model,
                        EMBED_NIM_MODEL,
                    )
                    continue
                ids = [str(v) for v in data["ids"].tolist()]
                matrix = np.asarray(data["matrix"], dtype=np.float32)
                if matrix.ndim != 2 or matrix.shape[0] != len(ids) or not ids:
                    raise ValueError(f"shape {tuple(matrix.shape)} vs {len(ids)} ids")
                norms = np.linalg.norm(matrix, axis=1, keepdims=True)
                norms[norms == 0] = 1.0
                store = (ids, matrix / norms)
                logger.info(
                    "loaded local dense matrix %s (%d x %d)", path, *matrix.shape
                )
                break
            except Exception as exc:
                logger.warning("dense matrix load failed (%s): %s", path, exc)
        self._dense_matrix_cache = store
        return store

    @property
    def db_source(self) -> str:
        if (
            getattr(self, "pinecone_index", None) is not None
            and not self._pinecone_unusable()
        ):
            return "production"
        return "local"

    @property
    def dense_source(self) -> str:
        if self.db_source == "production" and not getattr(
            self, "semantic_disabled", False
        ):
            return "production"
        if getattr(self, "_local_records_loaded", False) and self._dense_matrix():
            return "local"
        if getattr(self, "collection", None) is not None:
            return "local"
        return "none"

    @property
    def records_source(self) -> str:
        source = getattr(self, "_records_source", None)
        if source:
            return source
        return "local" if getattr(self, "records", None) else "none"

    @classmethod
    def from_records(cls, records):
        instance = cls.__new__(cls)
        instance.collection_name = "memory"
        instance.index_name = None
        instance.embed_fn = None
        instance.cross_encoder = None
        instance.reranker_disabled = True
        instance.semantic_disabled = True
        instance.collection = None
        instance.pinecone_index = None
        instance._pc = None
        instance.records = []
        instance.corpus = []
        instance.tokenized_corpus = []
        instance.bm25 = None
        instance.last_search_mode = None
        instance.last_stage_info = None
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
        # Citations are resolved from the fresh record set - drop any index
        # built for a previous one (ingest/refresh replace records wholesale).
        self._section_index = None

    def _is_legal_query(self, query: str) -> bool:
        q = query.lower()
        if self.SECTION_PATTERN.search(q) or self.ACT_PATTERN.search(q):
            return True
        tokens = set(self.TOKEN_PATTERN.findall(q))
        if tokens & self.LEGAL_INTENT_KEYWORDS:
            return True
        for phrase in (
            "high court", "supreme court", "consumer protection",
            "industrial dispute", "motor vehicle", "right to",
            "fundamental right", "legal remedy", "legal option",
            "what is the punishment", "is it a crime", "can i file",
        ):
            if phrase in q:
                return True
        return False

    def refresh_index(self):
        idx = self._pinecone
        all_records = []
        self._records_source = "none"
        self._local_records_loaded = False

        if idx is not None and not self._pinecone_unusable():
            # Round 2: one cheap fetch probes the data plane. Under the
            # monthly egress quota every vector read returns HTTP 429 after
            # seconds of retry backoff; probing once with max_attempts=1
            # marks the plane dead so later refreshes/searches skip it.
            try:
                retry(
                    idx.fetch,
                    ids=["__hector_quota_probe__"],
                    max_attempts=1,
                    operation_name="pinecone_quota_probe",
                )
            except Exception as exc:
                self._pinecone_dead = True
                logger.warning(
                    "pinecone data plane unavailable (%s) — using local store",
                    exc,
                )

        records_path = getattr(self, "_records_path", None)
        if records_path:
            try:
                all_records = self._load_jsonl_records(records_path)
                self._records_source = "local"
                self._local_records_loaded = True
                logger.info(
                    "loaded %d records from local corpus %s",
                    len(all_records),
                    records_path,
                )
            except Exception as exc:
                logger.warning("local corpus load failed: %s", exc)
                all_records = []

        if not all_records and idx is not None and not self._pinecone_unusable():
            try:
                for vector_list in idx.list():
                    # Pinecone SDK v7 returns string IDs; older versions return objects with .id
                    ids = [
                        v if isinstance(v, str) else v.id
                        for v in vector_list
                    ]
                    if not ids:
                        continue
                    fetched = retry(
                        idx.fetch,
                        ids=ids,
                        max_attempts=3,
                        operation_name="pinecone_fetch",
                    )
                    for vid, vec in fetched.vectors.items():
                        all_records.append({
                            "id": vid,
                            "document": (vec.metadata or {}).get("document", ""),
                            "metadata": {k: v for k, v in (vec.metadata or {}).items() if k != "document"},
                        })
                if all_records:
                    self._records_source = "production"
            except Exception as exc:
                logger.error("refresh_index failed: %s", exc, exc_info=True)
                self._pinecone_dead = True

        if not all_records:
            all_records = self._load_local_records()
            if all_records:
                self._records_source = "local"

        self._load_records(all_records)

    def search(self, query, top_k=5, candidate_pool=30, *, raw_query=None):
        candidate_pool = max(top_k, candidate_pool)
        legal_query = self._parse_query(query)
        # Citation injection must see only what the USER wrote: query
        # expansion appends "section 44 section 106 ..." concept hints to
        # non-citing queries, and treating those as explicit citations
        # flooded the top-10 with wrong sections (measured 2026-10-04:
        # BNS recall 0.9948 -> 0.6477). Callers that expand pass the
        # original text as raw_query.
        injection_query = query if raw_query is None else raw_query
        stage_info = {"timings_ms": {}, "stages": {}, "detail": {}}
        t_total = time.perf_counter()

        def _snap(name, started):
            stage_info["timings_ms"][name] = round(
                (time.perf_counter() - started) * 1000, 1
            )

        def _ids(items):
            return [item["id"] for item in items]

        if not self.records:
            logger.warning("BM25 records not loaded yet — falling back to pure Pinecone search")
            try:
                semantic_rank = self._timed_stage(
                    stage_info, "dense_ms", self._semantic_search, query, candidate_pool
                )
            except Exception as exc:
                logger.warning(
                    "semantic retrieval failed (%s) — no results available", exc
                )
                semantic_rank = []
            stage_info["stages"]["dense"] = _ids(semantic_rank)
            started = time.perf_counter()
            deduped = self._deduplicate_results(semantic_rank)
            _snap("dedup_ms", started)
            stage_info["stages"]["dedup"] = _ids(deduped)
            started = time.perf_counter()
            reranked = self._rerank_with_cross_encoder(query, deduped)
            _snap("rerank_ms", started)
            stage_info["stages"]["rerank"] = _ids(reranked)
            started = time.perf_counter()
            reranked = self._apply_relevance_threshold(reranked)
            _snap("threshold_ms", started)
            started = time.perf_counter()
            reranked = self._apply_same_act_floor(reranked, top_k, legal_query)
            _snap("floor_ms", started)
            stage_info["stages"]["final"] = _ids(reranked)
            _snap("total_ms", t_total)
            self._record_mode(semantic_rank, [])
            self.last_stage_info = stage_info
            return reranked[:top_k]

        bm25_tokens = self._tokenize(query)

        with ThreadPoolExecutor(max_workers=2) as executor:
            semantic_future = executor.submit(
                self._timed_stage, stage_info, "dense_ms",
                self._semantic_search, query, candidate_pool,
            )
            bm25_future = executor.submit(
                self._timed_stage, stage_info, "bm25_ms",
                self._bm25_search, bm25_tokens, candidate_pool,
            )
            try:
                semantic_rank = semantic_future.result()
            except Exception as exc:
                logger.warning(
                    "semantic retrieval failed (%s) — continuing with bm25 only",
                    exc,
                )
                semantic_rank = []
            bm25_rank = bm25_future.result()
        stage_info["stages"]["dense"] = _ids(semantic_rank)
        stage_info["stages"]["bm25"] = _ids(bm25_rank)

        started = time.perf_counter()
        fused = self._fuse_rankings(semantic_rank, bm25_rank)
        _snap("fuse_ms", started)
        stage_info["stages"]["rrf"] = [
            entry["id"]
            for entry in sorted(
                fused.values(), key=lambda entry: entry["rrf_score"], reverse=True
            )
        ]

        started = time.perf_counter()
        ranked = self._score_candidates(fused, semantic_rank, bm25_rank, legal_query)
        _snap("score_ms", started)
        stage_info["stages"]["scored"] = _ids(ranked)
        stage_info["detail"]["scored_top"] = [
            {
                key: item.get(key)
                for key in (
                    "id", "score", "retrieval_score", "boost_score",
                    "semantic_score", "bm25_score", "rrf_score", "act", "reasons",
                )
            }
            for item in ranked[:10]
        ]

        started = time.perf_counter()
        deduped = self._deduplicate_results(ranked)
        _snap("dedup_ms", started)
        stage_info["stages"]["dedup"] = _ids(deduped)

        started = time.perf_counter()
        injected = self._citation_injection_rows(
            injection_query, self._parse_query(injection_query)
        )
        injected_ids = {row["id"] for row in injected}
        if injected:
            present = {item["id"] for item in deduped}
            fresh = [row for row in injected if row["id"] not in present]
            if fresh:
                deduped = fresh + deduped
            stage_info["detail"]["injected"] = [
                {"id": row["id"], "kind": row["reasons"][0]}
                for row in injected
            ]
        _snap("inject_ms", started)

        started = time.perf_counter()
        reranked = self._rerank_with_cross_encoder(query, deduped, injected_ids)
        _snap("rerank_ms", started)
        stage_info["stages"]["rerank"] = _ids(reranked)

        started = time.perf_counter()
        reranked = self._apply_relevance_threshold(reranked, injected_ids)
        _snap("threshold_ms", started)

        started = time.perf_counter()
        reranked = self._apply_same_act_floor(reranked, top_k, legal_query)
        reranked = self._apply_injection_floor(reranked, top_k, injected_ids)
        _snap("floor_ms", started)
        stage_info["stages"]["final"] = _ids(reranked)

        _snap("total_ms", t_total)
        self._record_mode(semantic_rank, bm25_rank)
        self.last_stage_info = stage_info
        return reranked[:top_k]

    @staticmethod
    def _timed_stage(stage_info, name, fn, *args):
        started = time.perf_counter()
        try:
            return fn(*args)
        finally:
            stage_info["timings_ms"][name] = round(
                (time.perf_counter() - started) * 1000, 1
            )

    def _min_relevance(self) -> float:
        """Relevance floor: env HECTOR_MIN_RELEVANCE > threshold file > 0.05.

        Round 2 (task 4): the default comes from a data-derived calibration
        artifact (hector/api/data/relevance_threshold.json, written by
        hector/backend/calibrate_relevance_threshold.py) instead of a
        hardcoded 0.05. Env remains the highest-priority override so tests
        and operators can pin a value.
        """
        raw = os.getenv("HECTOR_MIN_RELEVANCE")
        if raw not in (None, ""):
            try:
                return float(raw)
            except ValueError:
                logger.warning(
                    "invalid HECTOR_MIN_RELEVANCE=%r — falling back to file", raw
                )
        path = os.getenv("HECTOR_RELEVANCE_THRESHOLD_JSON") or str(
            Path(__file__).with_name("relevance_threshold.json")
        )
        try:
            with open(path, encoding="utf-8") as fh:
                value = float(json.load(fh).get("threshold"))
            return value
        except FileNotFoundError:
            pass
        except Exception as exc:
            logger.warning("relevance threshold file %s unusable: %s", path, exc)
        return 0.05

    def _apply_relevance_threshold(self, results, keep_ids=None):
        threshold = self._min_relevance()
        if threshold <= 0 or not results:
            return results
        kept = [
            item
            for item in results
            if item.get("id") in (keep_ids or set())
            or float(item.get("score", 0.0) or 0.0) >= threshold
        ]
        if len(kept) != len(results):
            logger.info(
                "min relevance %.3f dropped %d/%d results",
                threshold,
                len(results) - len(kept),
                len(results),
            )
        return kept

    def _apply_same_act_floor(self, ranked, top_k, legal_query):
        """Guarantee a share of the returned slots to the act the query names.

        The merged IPC+BNS index holds paired provisions that are semantically
        near-identical - BNS 103 "Punishment for murder" against IPC 300
        "Murder" - so a cross-encoder alone will happily fill all ten slots of
        an IPC question with BNS text. Measured 2026-10-03 on iter2: the query
        "What treatment does the Indian Penal Code provide for murder?" returned
        top-10 = 100% BNS, with IPC 300 at rank 19.

        This reserves ceil(top_k * SAME_ACT_FLOOR_RATIO) slots for the named
        act by moving the best same-act candidates to the front and appending
        every other candidate in its existing reranked order, so cross-act
        chunks stay available for comparison questions.

        It only ever PROMOTES. If the window already holds the floor, the list
        is returned untouched - a query whose results are genuinely dominated
        by its own act behaves exactly as before, and no same-act chunk is
        ever evicted to make room for a cross-act one.

        No-op when the query names no act or names more than one (comparison
        questions have no single act to reserve for).
        """
        acts = (legal_query or {}).get("acts") or []
        if len(acts) != 1 or top_k < 2 or not ranked:
            return ranked

        target = acts[0]
        floor = min(top_k, max(1, math.ceil(top_k * SAME_ACT_FLOOR_RATIO)))
        window = ranked[:top_k]
        same_in_window = sum(1 for item in window if item.get("act") == target)
        if same_in_window >= floor:
            return ranked

        same = [item for item in ranked if item.get("act") == target]
        if not same:
            return ranked

        promoted = same[:floor]
        promoted_ids = {id(item) for item in promoted}
        rest = [item for item in ranked if id(item) not in promoted_ids]
        logger.debug(
            "same-act floor: window had %d %s candidates (< %d) - promoted %d",
            same_in_window, target, floor, len(promoted),
        )
        return promoted + rest

    def _apply_injection_floor(self, ranked, top_k, injected_ids):
        """Guarantee cited/counterpart rows a slot in the top-k window.

        Follows the same promote-only contract as _apply_same_act_floor.
        The blend alone leaves injected rows at blended rank ~31 when the
        cross-encoder saturates on sister-act lookalikes (measured
        2026-10-04: compare recall 118/162 with blend, counterparts still
        missing top-10) - the injection already marked these rows as
        authoritative (explicit citation or crosswalk), so the window is
        reordered to carry them, capped at top_k - 1 to keep at least one
        naturally-ranked result when top_k > 1. Honors the same
        HECTOR_RERANK_BLEND >= 1.0 legacy opt-out as _apply_rerank_blend.
        """
        if not ranked or not injected_ids or top_k < 1:
            return ranked
        try:
            alpha = float(os.getenv("HECTOR_RERANK_BLEND", "0.5"))
        except ValueError:
            alpha = 0.5
        if not 0.0 <= alpha < 1.0:
            return ranked
        window_ids = {item.get("id") for item in ranked[:top_k]}
        outside = [
            item
            for item in ranked
            if item.get("id") in injected_ids and item.get("id") not in window_ids
        ]
        if not outside:
            return ranked
        promote = outside[: max(1, top_k - 1)] if top_k > 1 else outside[:1]
        promote_ids = {id(item) for item in promote}
        rest = [item for item in ranked if id(item) not in promote_ids]
        logger.debug(
            "injection floor: promoted %d/%d injected rows into top-%d",
            len(promote), len(injected_ids), top_k,
        )
        return promote + rest

    def _record_mode(self, semantic_rank, bm25_rank):
        if semantic_rank and bm25_rank:
            mode = "hybrid"
        elif semantic_rank:
            mode = "semantic_only"
        elif bm25_rank:
            mode = "bm25_only"
        else:
            mode = "none"
        self.last_search_mode = mode
        logger.info(
            "retrieval mode=%s semantic_hits=%d bm25_hits=%d",
            mode,
            len(semantic_rank),
            len(bm25_rank),
        )

    def search_with_metadata_filters(
        self, query, entities, top_k=5, candidate_pool=20, *, raw_query=None
    ):
        # Round 4: the filtered pipeline below does not populate stage info;
        # clear any stale snapshot from a previous plain search().
        self.last_stage_info = None
        if not entities:
            return self.search(query, top_k, candidate_pool, raw_query=raw_query)

        section_numbers = list(
            dict.fromkeys(
                (entities.get("sections") or [])
                + (entities.get("ipc_sections") or [])
                + (entities.get("bns_sections") or [])
            )
        )
        acts = list(dict.fromkeys(entities.get("acts") or []))

        if not section_numbers and not acts:
            return self.search(query, top_k, candidate_pool, raw_query=raw_query)

        pinecone_filter = self._build_pinecone_filter(section_numbers, acts)
        if pinecone_filter is None:
            return self.search(query, top_k, candidate_pool, raw_query=raw_query)

        filtered_results = self._pinecone_filtered_search(
            pinecone_filter, top_k=min(candidate_pool, 200)
        )

        if not filtered_results and section_numbers:
            section_only_filter = (
                {"section_number": {"$eq": section_numbers[0]}}
                if len(section_numbers) == 1
                else {"$or": [{"section_number": {"$eq": s}} for s in section_numbers]}
            )
            filtered_results = self._pinecone_filtered_search(
                section_only_filter, top_k=min(candidate_pool, 200)
            )

        if not filtered_results:
            return self.search(query, top_k, candidate_pool, raw_query=raw_query)

        legal_query = self._parse_query(query)

        with ThreadPoolExecutor(max_workers=2) as executor:
            semantic_future = executor.submit(
                self._semantic_search_with_filter,
                query,
                min(candidate_pool, 200),
                pinecone_filter,
            )
            bm25_future = executor.submit(
                self._bm25_search_filtered, legal_query["tokens"], filtered_results
            )
            try:
                semantic_rank = semantic_future.result()
            except Exception as exc:
                logger.warning(
                    "filtered semantic retrieval failed (%s) — continuing with bm25 only",
                    exc,
                )
                semantic_rank = []
            bm25_rank = bm25_future.result()
        fused = self._fuse_rankings(semantic_rank, bm25_rank)
        ranked = self._score_candidates(fused, semantic_rank, bm25_rank, legal_query)
        deduped = self._deduplicate_results(ranked)
        reranked = self._rerank_with_cross_encoder(query, deduped)
        reranked = self._apply_relevance_threshold(reranked)
        reranked = self._apply_same_act_floor(reranked, top_k, legal_query)
        self._record_mode(semantic_rank, bm25_rank)
        return reranked[:top_k]

    def search_exact_section(self, query, section_number, act, top_k=3):
        """Exact act+section chunks for one IPC<->BNS compare panel.

        Why not search_with_metadata_filters: its Pinecone leg goes
        _pinecone_filtered_search -> idx.list(filter=...), which raises
        TypeError (this SDK's Index.list() takes no filter kwarg) and that
        method's bare `except: return []` swallows it - measured
        2026-10-04, all 80 "filtered" compare calls silently degraded to
        full hybrid search (p50 4.8s/side, ~4s of it a cross-encoder
        rerank over 30 docs). idx.query(vector, filter=...) accepts the
        same metadata filter, so the Pinecone leg here is ONE filtered
        vector query and no rerank: the filter already leaves only the
        wanted act's own chunks for the wanted section.

        Empty list means the section does not exist in that act (BNS only
        has sections 1-358); the caller's exact panel selector renders
        that as an empty panel rather than lookalike neighbours.

        Fallback chain: Pinecone absent/unusable, embed/query failure, or
        zero matches -> exact metadata scan over loaded records (tests,
        offline mode; same corpus, no network). Rows share the
        _score_candidates shape so _select_compare_panel and _to_hit work
        unchanged.
        """
        want_sec = str(section_number or "").strip().upper().replace(" ", "")
        want_act = str(act or "").strip().upper()
        top_k = max(1, int(top_k or 1))
        rows = self._exact_section_pinecone_rows(
            query, section_number, want_act, top_k
        )
        if not rows:
            rows = self._exact_section_record_rows(want_sec, want_act, top_k)
        return rows[:top_k]

    def _exact_section_pinecone_rows(self, query, section_number, act, top_k):
        idx = self._pinecone
        if (
            idx is None
            or self._pinecone_unusable()
            or getattr(self, "semantic_disabled", False)
        ):
            return []
        sec_raw = str(section_number or "").strip()
        # lettered sections are stored uppercase (120B, 153AA); match all
        # case variants so an uppercased compare request cannot miss them.
        sec_variants = list(
            dict.fromkeys(v for v in (sec_raw, sec_raw.upper(), sec_raw.lower()) if v)
        )
        acts = [act] if act else []
        pinecone_filter = self._build_pinecone_filter(sec_variants, acts)
        if pinecone_filter is None:
            return []
        embedding = self._embed_text(query or f"Section {sec_raw} {act}")
        if not embedding:
            return []
        try:
            results = retry(
                idx.query,
                vector=embedding,
                top_k=top_k,
                include_metadata=True,
                filter=pinecone_filter,
                operation_name="pinecone_exact_section_query",
            )
        except Exception as exc:
            logger.warning(
                "exact-section pinecone query failed (%s) - falling back to records",
                exc,
            )
            return []
        rows = []
        for match in results.get("matches", []):
            meta = match.get("metadata") or {}
            document = meta.get("document", "")
            clean = {k: v for k, v in meta.items() if k != "document"}
            score = float(match.get("score", 0.0) or 0.0)
            rows.append(
                {
                    "id": match.get("id", ""),
                    "document": document,
                    "metadata": clean,
                    "score": round(score, 6),
                    "hybrid_score": round(score, 6),
                    "retrieval_score": round(score, 6),
                    "similarity_score": round(score, 6),
                    "act": self._infer_act(document, clean),
                    "citation": self._extract_document_citation(document, clean),
                    "reasons": ["exact-section-query"],
                }
            )
        return rows[:top_k]

    def _exact_section_record_rows(self, want_sec, want_act, top_k):
        matches = []
        for record in self.records:
            meta = record.get("metadata") or {}
            rec_sec = (
                str(meta.get("section_number") or "").strip().upper().replace(" ", "")
            )
            if rec_sec != want_sec:
                continue
            rec_act = str(
                record.get("act") or self._infer_act(record.get("document", ""), meta)
            ).strip().upper()
            if want_act and rec_act and rec_act != want_act:
                continue
            matches.append((meta.get("chunk_index"), record))
        matches.sort(key=lambda item: (int(item[0] or 0), str(item[1].get("id"))))
        rows = []
        for _, record in matches[:top_k]:
            meta = record.get("metadata") or {}
            document = record.get("document", "")
            rows.append(
                {
                    "id": record.get("id", ""),
                    "document": document,
                    "metadata": meta,
                    "score": 1.0,
                    "hybrid_score": 1.0,
                    "retrieval_score": 1.0,
                    "similarity_score": 1.0,
                    "act": record.get("act") or None,
                    "citation": record.get("citation")
                    or self._extract_document_citation(document, meta),
                    "reasons": ["exact-section-scan"],
                }
            )
        return rows

    def _get_section_index(self):
        """(ACT, SECTION_NUMBER) -> records, built once per record set.

        Sections may span multiple chunks; entries are sorted by chunk order
        so the section opening is injected first.
        """
        index = getattr(self, "_section_index", None)
        if index is None:
            index = {}
            for record in self.records:
                meta = record.get("metadata") or {}
                sec = str(
                    meta.get("section_number") or ""
                ).strip().upper().replace(" ", "")
                act = str(record.get("act") or "").strip().upper()
                if not sec or not act:
                    continue
                index.setdefault((act, sec), []).append(record)
            for entries in index.values():
                entries.sort(
                    key=lambda rec: (
                        int((rec.get("metadata") or {}).get("chunk_index") or 0),
                        str(rec.get("id")),
                    )
                )
            self._section_index = index
        return index

    def _cited_act_sections(self, query, legal_query):
        """(section_number, [acts]) per 'section N' mention in the query.

        The act comes from the text FOLLOWING the mention first ("Section 103
        of the Indian Penal Code" -> IPC); the preceding text is checked only
        when the follow-up names no act ("...predecessor of Section 193" with
        "Bharatiya Nyaya Sanhita" behind it). Both sides are windowed at 45
        chars - wider windows catch the other act of a comparison sentence
        and attribute the section to both, injecting unrelated lookalikes.
        """
        named = list((legal_query or {}).get("acts") or [])
        if not named:
            return []
        surfaces = {
            act: [
                surface
                for surface, canon in self.ACT_ALIASES.items()
                if canon == act
            ]
            for act in named
        }

        def _acts_in(text):
            lowered = text.lower()
            return [
                act
                for act in named
                if any(
                    re.search(r"\b" + re.escape(surface) + r"\b", lowered)
                    for surface in surfaces[act]
                )
            ]

        out, seen = [], set()
        for match in self.SECTION_PATTERN.finditer(query or ""):
            num = match.group(1).upper()
            after = query[match.end(): match.end() + 45]
            before = query[max(0, match.start() - 45): match.start()]
            acts = _acts_in(after) or _acts_in(before) or list(named)
            key = (num, tuple(acts))
            if key in seen:
                continue
            seen.add(key)
            out.append((num, acts))
        return out

    def _citation_injection_rows(self, query, legal_query):
        """Candidate rows for cited sections and their mapped counterparts.

        Reranker-only ranking drops cited sections: measured 2026-10-04, on
        compare questions the cited IPC section reached scored rank 1 and fell
        to rerank rank 32 (sister-act lookalikes hold rerank scores
        0.98-0.997), and the unnamed counterpart was in neither the dense nor
        the bm25 top-30 at all - section_recall@10 = 74/162 = 0.46. Injecting
        these rows before rerank guarantees they enter the pool; the final
        blend (_apply_rerank_blend) keeps their retrieval evidence decisive.

        - "citation-injection": every section the query explicitly names, in
          the act attributed to that mention (retrieval evidence 1.0).
        - "counterpart-injection": mapping.json-derived other side of a
          two-act query (0.9 - authoritative, but not what the user cited).
        Counterparts only fire when BOTH acts of the pair are named in the
        query, so single-act queries keep their act-scoped behaviour.
        """
        if not self.records:
            return []
        cited = self._cited_act_sections(query, legal_query)
        if not cited:
            return []
        named = set((legal_query or {}).get("acts") or [])
        forward, reverse = _load_ipc_bns_crosswalk()
        index = self._get_section_index()

        targets, seen = [], set()

        def _add(act, sec, kind):
            key = (act, sec, kind)
            if key not in seen:
                seen.add(key)
                targets.append((act, sec, kind))

        for num, acts in cited:
            for act in acts:
                _add(act, num, "citation-injection")
                if act == "IPC" and "BNS" in named:
                    for counterpart in forward.get(num, []):
                        _add("BNS", counterpart, "counterpart-injection")
                elif act == "BNS" and "IPC" in named:
                    for counterpart in reverse.get(num, []):
                        _add("IPC", counterpart, "counterpart-injection")

        rows = []
        for act, sec, kind in targets:
            for record in index.get((act, sec), [])[:1]:
                rows.append(self._build_injection_row(record, kind, legal_query))
        return rows

    def _build_injection_row(self, record, kind, legal_query):
        """Same shape/score fields _score_candidates emits, for injected rows."""
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
        retrieval_score = 1.0 if kind == "citation-injection" else 0.9
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
                kind,
                concept_reason,
                current_law_reason,
                jurisdiction_reason,
                source_type_reason,
            ]
            if reason
        ]
        reasons.extend(boost_reasons)
        return {
            "id": record["id"],
            "document": record["document"],
            "metadata": record["metadata"],
            "score": round(hybrid_score, 6),
            "hybrid_score": round(hybrid_score, 6),
            "retrieval_score": round(retrieval_score, 6),
            "boost_score": round(boost_score, 6),
            "rrf_score": 0.0,
            "semantic_score": 0.0,
            "bm25_score": 0.0,
            "bm25_raw_score": 0.0,
            "act": record.get("act"),
            "citation": record.get("citation"),
            "reasons": reasons,
        }

    def _build_pinecone_filter(self, section_numbers, acts):
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
        result = []
        for act in acts:
            key = act.lower().strip()
            exact_names = self.ACT_TO_EXACT.get(key)
            if exact_names:
                result.extend(exact_names)
            else:
                result.append(act)
        return list(dict.fromkeys(result))

    def _pinecone_filtered_search(self, pinecone_filter, top_k=200):
        idx = self._pinecone
        if idx is None or self._pinecone_unusable():
            return []
        try:
            matching_ids = []
            for vector_list in idx.list(filter=pinecone_filter, limit=top_k):
                matching_ids.extend([v.id for v in vector_list])
            if not matching_ids:
                return []
            fetched = retry(
                idx.fetch,
                ids=matching_ids[:top_k],
                max_attempts=2,
                operation_name="pinecone_filtered_fetch",
            )
            results = []
            for vid, vec in fetched.vectors.items():
                meta = vec.metadata or {}
                results.append({
                    "id": vid,
                    "document": meta.get("document", ""),
                    "metadata": {k: v for k, v in meta.items() if k != "document"},
                })
            return results
        except Exception:
            return []

    def _semantic_search_with_filter(self, query, top_k, pinecone_filter):
        idx = self._pinecone
        if (
            idx is None
            or getattr(self, "semantic_disabled", False)
            or self._pinecone_unusable()
        ):
            # No/failed Pinecone leg: same unfiltered-dense fallback the
            # exception path below uses (local Chroma when attached).
            return self._local_dense_search(query, top_k)
        embedding = self._embed_text(query)
        if embedding is None:
            return []
        try:
            results = retry(
                idx.query,
                vector=embedding,
                top_k=top_k,
                include_metadata=True,
                filter=pinecone_filter,
                operation_name="pinecone_filtered_query",
            )
        except Exception:
            return self._semantic_search(query, top_k)

        ranked = []
        for match in results.get("matches", []):
            meta = match.get("metadata", {})
            ranked.append({
                "id": match.get("id", ""),
                "document": meta.get("document", ""),
                "metadata": {k: v for k, v in meta.items() if k != "document"},
                # Round 4: Pinecone cosine metric returns similarity
                # (higher = better); store as distance (lower = better) so
                # _normalize_semantic_score ranks correctly for production.
                "distance": max(0.0, 1.0 - float(match.get("score", 0.0))),
                "rank": len(ranked) + 1,
            })
        return ranked

    def _bm25_search_filtered(self, query_tokens, filtered_results):
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
            ranked.append({
                "id": result["id"],
                "document": result["document"],
                "metadata": result["metadata"],
                "score": score,
                "normalized_score": normalized,
                "rank": rank,
            })
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
        idx = self._pinecone
        if (
            idx is not None
            and not getattr(self, "semantic_disabled", False)
            and not self._pinecone_unusable()
        ):
            try:
                embedding = self._embed_text(query)
                if embedding is not None:
                    results = retry(
                        idx.query,
                        vector=embedding,
                        top_k=top_k,
                        include_metadata=True,
                        operation_name="pinecone_query",
                    )
                    ranked = []
                    for match in results.get("matches", []):
                        meta = match.get("metadata", {})
                        ranked.append({
                            "id": match.get("id", ""),
                            "document": meta.get("document", ""),
                            "metadata": {k: v for k, v in meta.items() if k != "document"},
                            # Round 4: cosine similarity (higher = better)
                            # stored as distance (lower = better) — see
                            # _semantic_search_with_filter.
                            "distance": max(
                                0.0, 1.0 - float(match.get("score", 0.0))
                            ),
                            "rank": len(ranked) + 1,
                        })
                    return ranked
            except Exception as exc:
                # Round 2: quota/errors on the Pinecone data plane switch the
                # dense leg to the local Chroma store for the process lifetime.
                self._pinecone_dead = True
                logger.warning(
                    "pinecone semantic query failed (%s) — switching to local dense",
                    exc,
                )
        return self._local_dense_search(query, top_k)

    def _local_dense_search(self, query, top_k):
        """Local dense search with the same item shape as the Pinecone leg.

        Preference order: precomputed NIM matrix for the eval corpus (works
        without chromadb — serverless), then the legacy Chroma collection
        (dev/ingest layout). Callers expect id/document/metadata/distance/rank
        with distance lower-is-better, which matches both branches.
        """
        if getattr(self, "_local_records_loaded", False):
            store = self._dense_matrix()
            if store is not None:
                return self._matrix_dense_search(query, top_k, store)
        coll = self.collection
        if coll is None:
            return []
        try:
            res = coll.query(
                query_texts=[query],
                n_results=max(int(top_k), 1),
                include=["documents", "metadatas", "distances"],
            )
        except Exception as exc:
            logger.warning("local dense query failed: %s", exc)
            return []
        ids = (res.get("ids") or [[]])[0]
        docs = (res.get("documents") or [[]])[0]
        metas = (res.get("metadatas") or [[]])[0]
        dists = (res.get("distances") or [[]])[0]
        ranked = []
        for i, rid in enumerate(ids):
            ranked.append({
                "id": rid,
                "document": docs[i] if i < len(docs) else "",
                "metadata": (metas[i] if i < len(metas) else None) or {},
                "distance": dists[i] if i < len(dists) else 0.0,
                "rank": len(ranked) + 1,
            })
        return ranked

    def _matrix_dense_search(self, query, top_k, store):
        embedding = self._embed_text(query)
        if embedding is None:
            logger.warning("local dense: query embed unavailable — BM25 only")
            return []
        try:
            import numpy as np

            ids, matrix = store
            vec = np.asarray(embedding, dtype=np.float32)
            if vec.shape[0] != matrix.shape[1]:
                raise ValueError(f"dim {vec.shape[0]} != {matrix.shape[1]}")
            norm = float(np.linalg.norm(vec))
            if norm == 0.0:
                return []
            sims = matrix @ (vec / norm)
            count = min(max(int(top_k), 1), len(ids))
            if count < len(ids):
                idxs = np.argpartition(-sims, count - 1)[:count]
                idxs = idxs[np.argsort(-sims[idxs])]
            else:
                idxs = np.argsort(-sims)
        except Exception as exc:
            logger.warning("local dense search failed: %s", exc)
            return []
        records_by_id = {r["id"]: r for r in self.records}
        ranked = []
        for i in idxs:
            record = records_by_id.get(ids[int(i)])
            if record is None:
                continue
            ranked.append({
                "id": ids[int(i)],
                "document": record["document"],
                "metadata": record["metadata"],
                "distance": max(0.0, 1.0 - float(sims[int(i)])),
                "rank": len(ranked) + 1,
            })
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
            ranked.append({
                "id": record["id"],
                "document": record["document"],
                "metadata": record["metadata"],
                "score": score,
                "normalized_score": normalized_score,
                "rank": rank,
            })
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

    def _rerank_with_cross_encoder(self, query, candidates, injected_ids=None):
        if not candidates:
            return []

        if self.reranker_disabled:
            term_idf = self._query_term_idf(candidates, query)
            for item in candidates:
                fallback_score = self._fallback_reranker_score(
                    item, query=query, term_idf=term_idf
                )
                item["reranker_score"] = round(fallback_score, 6)
                item["score"] = item["reranker_score"]
                item["similarity_score"] = item["reranker_score"]
                item["reasons"] = [
                    *item.get("reasons", []),
                    "reranker-disabled",
                ]
            candidates.sort(key=lambda item: item["reranker_score"], reverse=True)
            return candidates

        # Try Nemotron reranker first (API-based, works on Vercel)
        try:
            from core.rerank_provider import get_rerank_provider

            provider = os.getenv("HECTOR_RERANK_PROVIDER", "nemotron")
            reranker = getattr(self, "_reranker_cached", None)
            if reranker is None:
                reranker = get_rerank_provider(provider)
                self._reranker_cached = reranker
            # Capture retrieval evidence before the provider overwrites
            # item["score"] with the cross-encoder value.
            for item in candidates:
                item["pre_rerank_score"] = round(
                    min(
                        float(
                            item.get("hybrid_score")
                            or item.get("score")
                            or 0.0
                        ),
                        1.0,
                    ),
                    6,
                )
            return self._apply_rerank_blend(
                reranker.rerank(query, candidates), injected_ids
            )
        except Exception as e:
            self._reranker_cached = None
            import logging
            logging.getLogger("hector.retriever").warning(
                f"Nemotron rerank failed, using fallback: {e}"
            )

        # Last resort: heuristic scoring (already retrieval-derived, so it is
        # blended-equivalent - no _apply_rerank_blend here).
        term_idf = self._query_term_idf(candidates, query)
        for item in candidates:
            fallback_score = self._fallback_reranker_score(
                item, query=query, term_idf=term_idf
            )
            item["reranker_score"] = round(fallback_score, 6)
            item["score"] = item["reranker_score"]
            item["similarity_score"] = item["reranker_score"]
            item["reasons"] = [
                *item.get("reasons", []),
                "cross-encoder-unavailable",
            ]

        candidates.sort(key=lambda item: item["reranker_score"], reverse=True)
        return candidates

    def _apply_rerank_blend(self, items, injected_ids=None):
        """Lift injected rows above rerank noise; natural rows keep pure
        reranker order (legacy behavior).

        Why injection-only: the cross-encoder alone cannot separate merged
        acts on COMPARE queries - sister-act restatements saturate at
        0.98-0.997 while the cited section sinks (measured 2026-10-04:
        cited IPC section of cmpf-103-112 at rerank rank 32, compare
        recall 74/162 = 0.46). Injecting the cited/crosswalk rows with
        retrieval evidence 1.0 and blending them back repairs that.

        Why NOT whole-list blending: mixing fused retrieval evidence at
        half weight into every row reorders single-act queries the
        cross-encoder already handled - measured 2026-10-04, whole-list
        blend tanked BNS recall 192/193 -> 125/193 and IPC 155/198 with
        lexical-pre rows outranking semantically-correct ones. With no
        injected ids this returns items untouched, so single-act recall
        is exactly the legacy pure-rerank path.

        HECTOR_RERANK_BLEND sets alpha for the injected-row blend
        (default 0.5; >= 1.0 disables blend AND the injection floor,
        restoring fully legacy ordering).
        """
        try:
            alpha = float(os.getenv("HECTOR_RERANK_BLEND", "0.5"))
        except ValueError:
            alpha = 0.5
        if not 0.0 <= alpha < 1.0 or not injected_ids:
            return items
        natural_max = 0.0
        for item in items:
            if item.get("id") not in injected_ids:
                natural_max = max(
                    natural_max,
                    float(item.get("reranker_score") or item.get("score") or 0.0),
                )
        # Injected rows rank above every natural row regardless of how
        # saturated the cross-encoder got; their internal order still
        # follows the blend below.
        lifted = min(round(natural_max + 0.001, 6), 1.0)
        for item in items:
            if item.get("id") in injected_ids:
                reranker_score = float(
                    item.get("reranker_score") or item.get("score") or 0.0
                )
                pre_score = float(item.get("pre_rerank_score") or 0.0)
                item["score"] = round(
                    max(alpha * reranker_score + (1.0 - alpha) * pre_score, lifted),
                    6,
                )
        items.sort(key=lambda item: item.get("score", 0.0), reverse=True)
        return items

    def _candidate_haystack(self, item):
        metadata = item.get("metadata") or {}
        return " ".join(
            str(value)
            for value in (
                item.get("document") or "",
                metadata.get("source") or "",
                metadata.get("section_title") or "",
                metadata.get("act_name") or "",
            )
        ).lower()

    def _query_term_idf(self, candidates, query):
        """IDF weights for the query's concept terms over this candidate pool.
        Ubiquitous legal boilerplate ("indian", "punishment") drops out, rare
        defining terms ("good faith", "thug") dominate the overlap bonus."""
        terms = self._extract_concept_terms(query)
        if not terms or not candidates:
            return {}
        haystacks = [self._candidate_haystack(item) for item in candidates]
        n = len(haystacks)
        idf = {}
        for term in terms:
            pattern = rf"\b{re.escape(term)}\b"
            df = sum(1 for h in haystacks if re.search(pattern, h))
            weight = math.log((n + 1) / (df + 1))
            if weight >= 0.1:
                idf[term] = weight
        return idf

    def _query_overlap_bonus(self, item, query, term_idf=None):
        """Definitional misses ("good faith", "life", "thug") lose on fusion
        score to look-alike sections; credit candidates that contain the
        query's RARE distinctive terms and adjacent phrases (IDF-weighted)."""
        if not term_idf:
            return 0.0
        haystack = self._candidate_haystack(item)
        if not haystack:
            return 0.0
        total = sum(term_idf.values())
        if total <= 0:
            return 0.0
        hits = sum(
            weight
            for term, weight in term_idf.items()
            if re.search(rf"\b{re.escape(term)}\b", haystack)
        )
        bonus = 0.25 * (hits / total)
        content_tokens = [
            token for token in self._tokenize(query)
            if len(token) >= 4 and token not in self.CONCEPT_STOPWORDS
        ]
        pair_value = 0.0
        for a, b in zip(content_tokens, content_tokens[1:]):
            weight = term_idf.get(a, 0.0) + term_idf.get(b, 0.0)
            if weight <= 0:
                continue
            if re.search(rf"\b{re.escape(a)}\s+{re.escape(b)}\b", haystack):
                pair_value = max(pair_value, weight)
        bonus += 0.10 * (pair_value / total)
        return min(bonus, 0.35)

    def _quoted_phrases(self, query):
        phrases = []
        for match in re.finditer(
            r'[“"\']([^”"\']{2,60})[”"\']', query or ""
        ):
            phrase = " ".join(match.group(1).split()).lower()
            if phrase and phrase not in phrases:
                phrases.append(phrase)
        return phrases

    def _definition_bonus(self, item, query):
        """Definitional queries quote the concept (“good faith”, “life”);
        sections whose TITLE defines that phrase get a decisive lift."""
        phrases = self._quoted_phrases(query)
        if not phrases:
            return 0.0
        metadata = item.get("metadata") or {}

        def normalize(text):
            return re.sub(r"[-–—/]+", " ", str(text or "").lower())

        title = normalize(metadata.get("section_title"))
        haystack = normalize(self._candidate_haystack(item))
        for phrase in phrases:
            pattern = rf"(?<!\w){re.escape(phrase)}(?!\w)"
            if title and re.search(pattern, title):
                return 0.35
            if haystack and re.search(pattern, haystack):
                return 0.18
        return 0.0

    def _fallback_reranker_score(self, item, query=None, term_idf=None):
        rrf_w = float(os.environ.get("HECTOR_FALLBACK_W_RRF", "12.0"))
        bm25_w = float(os.environ.get("HECTOR_FALLBACK_W_BM25", "0.30"))
        sem_w = float(os.environ.get("HECTOR_FALLBACK_W_SEM", "0.25"))
        base = (
            item.get("rrf_score", 0.0) * rrf_w
            + item.get("bm25_score", 0.0) * bm25_w
            + item.get("semantic_score", 0.0) * sem_w
            + item.get("boost_score", 0.0)
        )
        # Injected rows carry their evidence only in retrieval_score (rrf/
        # bm25/semantic are 0 by construction) - without this the fallback
        # scorer ranks a cited section below unrelated bm25 hits.
        if any(
            reason in ("citation-injection", "counterpart-injection")
            for reason in item.get("reasons") or []
        ):
            base += float(item.get("retrieval_score") or 0.0)
        if query:
            base += self._query_overlap_bonus(item, query, term_idf=term_idf)
            base += self._definition_bonus(item, query)
        return max(0.0, min(base, 1.0))

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
            key = explicit_act.lower()
            canonical = self.ACT_ALIASES.get(key)
            if canonical:
                return canonical
            # Long-form citations are not alias keys. Corpus rows carry
            # "The Indian Penal Code, 1860", and falling through to .upper()
            # made record["act"] = "THE INDIAN PENAL CODE, 1860" while queries
            # resolve to "IPC" - so the act-match boost in _legal_boost never
            # fired (verified 2026-10-03). Longest alias first so "indian
            # penal code" wins over any shorter alias inside the same string.
            for alias in sorted(self.ACT_ALIASES, key=len, reverse=True):
                if alias in key:
                    return self.ACT_ALIASES[alias]
            return explicit_act.upper()

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

    def _embed_text(self, text):
        """Embed text using NVIDIA NIM API."""
        try:
            global _EMBED_CLIENT
            nim_key = os.getenv("NIM_API_KEY", "")
            nim_url = os.getenv("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
            if not nim_key:
                return None
            if _EMBED_CLIENT is None:
                import httpx

                # Reuse TCP/TLS connections. A fresh handshake per query cost
                # ~0.85s of the retrieval budget (measured 1146ms -> 300ms).
                _EMBED_CLIENT = httpx.Client(
                    timeout=15,
                    limits=httpx.Limits(
                        max_keepalive_connections=4, max_connections=8
                    ),
                )
            resp = _EMBED_CLIENT.post(
                f"{nim_url}/embeddings",
                headers={
                    "Authorization": f"Bearer {nim_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "input": [text],
                    "model": EMBED_NIM_MODEL,
                    "encoding_format": "float",
                    "input_type": "query",
                    "truncate": "END",
                },
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            items = data.get("data", [])
            if items:
                return items[0].get("embedding", [])
        except Exception:
            pass
        return None
