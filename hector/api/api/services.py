from __future__ import annotations

import json
import logging
import re
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from utils.retry import retry

from .schemas import (
    CompareRequest,
    CompareResponse,
    IngestRequest,
    IngestResponse,
    RouteResponse,
    SearchHit,
    SearchRequest,
    SearchResponse,
    StatusResponse,
)

if TYPE_CHECKING:
    from core.orchestrator import HectorOrchestrator
    from core.router import HectorRouter
    from data.hybrid_retriever import HectorHybridRetriever

logger = logging.getLogger(__name__)


class HectorApiService:
    def __init__(
        self,
        orchestrator: "HectorOrchestrator" | None = None,
        retriever: "HectorHybridRetriever" | None = None,
        router: "HectorRouter" | None = None,
    ):
        self.started_at = time.time()
        if orchestrator is None:
            from core.orchestrator import HectorOrchestrator

            orchestrator = HectorOrchestrator()

        self.orchestrator = orchestrator
        self.router = router or self.orchestrator.router
        self.retriever = retriever or self.orchestrator.retriever

        # Initialize response generator
        from core.response_generator import ContextualResponseGenerator

        self.response_generator = ContextualResponseGenerator(self.retriever)

        # Persistent query cache
        from core.query_cache import get_query_cache

        self._query_cache = get_query_cache()

        # Search analytics
        from core.analytics import get_analytics

        self._analytics = get_analytics()

    def search(self, request: SearchRequest) -> SearchResponse:
        timings: dict[str, float] = {}

        # Check persistent query cache first
        cached = self._query_cache.get(request.query)
        if cached is not None:
            logger.info("Cache hit for query: %s", request.query[:60])
            try:
                cached_data = json.loads(cached["response"])
                cached_data["cached"] = True
                cached_data["stage_timings"] = {
                    **(cached_data.get("stage_timings") or {}),
                    "cache_hit": True,
                }
                # Record analytics for cache hit
                try:
                    self._analytics.record_search(
                        query=request.query,
                        route=cached_data.get("route"),
                        confidence=cached_data.get("answer_confidence"),
                        result_count=len(cached_data.get("items", [])),
                        response_ms=0,
                        cache_hit=True,
                    )
                except Exception:
                    pass
                return SearchResponse(**cached_data)
            except (json.JSONDecodeError, KeyError, TypeError):
                pass  # Fall through to full search

        t0 = time.perf_counter()
        intent = self.router.get_route(request.query)
        normalized_query = request.query
        mappings: list[str] = []

        if intent.get("route") == "LEGAL_RESEARCH":
            normalized_query, mappings = self.router.normalize_query(request.query)
        t_route = time.perf_counter()
        timings["route_ms"] = round((t_route - t0) * 1000, 1)

        total_needed = max(request.page * request.page_size, request.page_size)
        retrieval_window = max(25, total_needed)
        results = retry(
            self.retriever.search,
            normalized_query,
            top_k=retrieval_window,
            candidate_pool=max(40, retrieval_window * 2),
            max_attempts=3,
            retryable_exceptions=(Exception,),
            operation_name="pinecone_search",
        )
        t_retrieve = time.perf_counter()
        timings["retrieve_ms"] = round((t_retrieve - t_route) * 1000, 1)

        total_results = len(results)
        start = (request.page - 1) * request.page_size
        end = start + request.page_size
        selected_results = self._select_response_results(
            results=results,
            normalized_query=normalized_query,
            limit=request.page_size,
        )
        paginated = (
            selected_results[start:end] if request.page == 1 else results[start:end]
        )

        items = [self._to_hit(item) for item in paginated]

        # Generate response with contextual formatting
        response_data = {
            "generated_response": "",
            "answer_sections": [],
            "source_sections": [],
            "answer_confidence": 0.0,
            "citations": [],
            "related_provisions": [],
        }

        # Build the effective query — append file context if provided
        effective_query = request.query
        if request.file_context:
            effective_query = (
                f"{request.query}\n\n"
                f"--- Uploaded Document Context ---\n"
                f"{request.file_context[:8000]}\n"
                f"--- End Document Context ---"
            )

        if intent.get("route") == "LEGAL_RESEARCH" or request.file_context:
            response_data = self.response_generator.generate(
                query=effective_query,
                results=paginated,
                format=request.format,
                include_related=request.include_related,
                file_context=request.file_context,
            )
            generated_response = response_data["generated_response"]
        else:
            generated_response = intent.get("hector_response", "")
        t_generate = time.perf_counter()
        timings["generate_ms"] = round((t_generate - t_retrieve) * 1000, 1)
        timings["total_ms"] = round((t_generate - t0) * 1000, 1)
        timings["route_confidence"] = round(float(intent.get("confidence", 0.0)), 3)

        total_pages = max(
            1, (total_results + request.page_size - 1) // request.page_size
        )

        # Compute confidence level and warning
        raw_confidence = float(response_data.get("answer_confidence", 0.0) or 0.0)
        confidence_level, confidence_warning = self._assess_confidence(
            raw_confidence, intent.get("route", "GENERAL"), len(paginated)
        )

        # Run hallucination check on generated response
        hallucination_check = None
        if generated_response and (intent.get("route") == "LEGAL_RESEARCH" or request.file_context):
            from core.verifier import ClaimExtractor, HallucinationDetector

            actual_claims = ClaimExtractor.extract_claims(generated_response)
            total_claims = len(actual_claims) if actual_claims else 0
            claims_verified = int(total_claims * raw_confidence / 100.0) if total_claims else 0

            verification_result = {
                "verified_response": generated_response,
                "citation_coverage": raw_confidence / 100.0,
                "total_claims": total_claims,
                "claims_verified": claims_verified,
            }
            hallucination_check = HallucinationDetector.generate_hallucination_report(
                verification_result
            )

        response = SearchResponse(
            route=intent.get("route", "GENERAL"),
            query=request.query,
            normalized_query=normalized_query,
            verification_enabled=bool(
                request.verify
                and getattr(self.orchestrator, "enable_verification", False)
            ),
            total_results=total_results,
            page=request.page,
            page_size=request.page_size,
            total_pages=total_pages,
            items=items,
            generated_response=generated_response,
            answer_sections=response_data.get("answer_sections", []),
            source_sections=response_data.get("source_sections", []),
            answer_confidence=raw_confidence,
            confidence_level=confidence_level,
            confidence_warning=confidence_warning,
            hallucination_check=hallucination_check,
            citations=response_data.get("citations", []),
            related_provisions=response_data.get("related_provisions", []),
            response_format=request.format,
            retrieved_at=datetime.now(UTC),
            stage_timings=timings,
        )

        # Store in persistent cache (only for successful legal research queries)
        if intent.get("route") == "LEGAL_RESEARCH" and generated_response:
            try:
                self._query_cache.set(
                    request.query,
                    response.model_dump_json(),
                    timing=timings,
                    route=intent.get("route"),
                )
            except Exception as exc:
                logger.warning("Failed to cache query response: %s", exc)

        # Record analytics
        try:
            self._analytics.record_search(
                query=request.query,
                route=intent.get("route"),
                confidence=raw_confidence,
                result_count=total_results,
                response_ms=timings.get("total_ms"),
                cache_hit=False,
            )
        except Exception as exc:
            logger.warning("Failed to record analytics: %s", exc)

        return response

    def _assess_confidence(
        self, raw_score: float, route: str, num_results: int
    ) -> tuple[str, str | None]:
        """Map raw confidence score to level and generate warning if needed."""
        if route != "LEGAL_RESEARCH":
            return "unknown", None

        if num_results == 0:
            return "low", "No matching documents found in the corpus."

        if raw_score >= 75:
            return "high", None
        elif raw_score >= 50:
            return (
                "medium",
                "Confidence is moderate. Verify critical details against source documents.",
            )
        else:
            return (
                "low",
                "Low confidence — response may be incomplete or unreliable. Always cross-reference with official legal texts.",
            )

    def _select_response_results(
        self, results: list[dict], normalized_query: str, limit: int
    ) -> list[dict]:
        if not results or limit <= 0:
            return []

        requested_acts = {
            act
            for act in ("IPC", "BNS", "CRPC", "BNSS", "BSA", "CPC")
            if act.lower() in normalized_query.lower()
        }
        if len(requested_acts) < 2:
            return results[:limit]

        selected = []
        selected_ids = set()
        for act in sorted(requested_acts):
            match = next((item for item in results if item.get("act") == act), None)
            if match:
                selected.append(match)
                selected_ids.add(match.get("id"))

        for item in results:
            if len(selected) >= limit:
                break
            if item.get("id") in selected_ids:
                continue
            selected.append(item)
            selected_ids.add(item.get("id"))

        return selected

    def compare(self, request: CompareRequest) -> CompareResponse:
        mapping = self.router.legal_map
        counterpart_act = None
        counterpart_section = None
        note = None

        if request.act == "IPC":
            matched = mapping.get(request.section)
            if matched:
                counterpart_act = "BNS"
                counterpart_section = str(matched.get("new"))
                note = matched.get("note")
        else:
            candidates = [
                (ipc_section, mapped)
                for ipc_section, mapped in mapping.items()
                if str(mapped.get("new")).upper() == request.section
            ]
            if candidates:
                counterpart_act = "IPC"
                counterpart_section, note = self._pick_reverse_counterpart(
                    request.section, candidates
                )

        # panel_pool widens the candidate pool beyond page_size so the
        # panel selector has the wanted act's cards to choose from even
        # when raw ranking interleaves cross-act neighbours (paired
        # IPC/BNS provisions are near-identical).
        panel_pool = max(request.page_size * 4, 12)
        candidate_pool = max(panel_pool, 30)

        requested_results = self._compare_retrieve(
            f"Section {request.section} {request.act}",
            request.act,
            request.section,
            panel_pool,
            candidate_pool,
            "pinecone_compare_requested",
        )

        counterpart_results = []
        if counterpart_act and counterpart_section:
            counterpart_results = self._compare_retrieve(
                f"Section {counterpart_section} {counterpart_act}",
                counterpart_act,
                counterpart_section,
                panel_pool,
                candidate_pool,
                "pinecone_compare_counterpart",
            )

        requested_selected = self._select_compare_panel(
            requested_results, request.act, request.section, request.page_size
        )
        counterpart_selected = self._select_compare_panel(
            counterpart_results, counterpart_act, counterpart_section, request.page_size
        )

        return CompareResponse(
            requested_act=request.act,
            requested_section=request.section,
            counterpart_act=counterpart_act,
            counterpart_section=counterpart_section,
            note=note,
            requested_results=[self._to_hit(item) for item in requested_selected],
            counterpart_results=[self._to_hit(item) for item in counterpart_selected],
            compared_at=datetime.now(UTC),
        )

    def _compare_retrieve(
        self, query, act, section, top_k, candidate_pool, operation_name
    ):
        """Retrieve candidates for one compare panel.

        Prefers the retriever's exact-section lookup (one Pinecone
        metadata-filtered vector query, no cross-encoder rerank - see
        HectorHybridRetriever.search_exact_section). Measured 2026-10-04,
        the previous search_with_metadata_filters path silently degraded
        to full hybrid search: its Pinecone leg calls idx.list(filter=...),
        which raises TypeError on this SDK and its bare except returns []
        - so every compare cost p50 9.7s (two ~4.8s full searches, ~4s of
        each a rerank over 30 docs) and correctness rested solely on
        _select_compare_panel filtering afterwards.

        Stubs without the method fall back to search_with_metadata_filters
        (which internally degrades to plain hybrid search), then to plain
        search; _select_compare_panel keeps only exact hits either way.
        """
        exact = getattr(self.retriever, "search_exact_section", None)
        if exact is not None:
            return retry(
                exact,
                query,
                section,
                act,
                top_k=top_k,
                max_attempts=3,
                retryable_exceptions=(Exception,),
                operation_name=operation_name,
            )
        filtered = getattr(self.retriever, "search_with_metadata_filters", None)
        if filtered is not None:
            entities = {"sections": [str(section)], "acts": [str(act)]}
            return retry(
                filtered,
                query,
                entities,
                top_k=top_k,
                candidate_pool=candidate_pool,
                max_attempts=3,
                retryable_exceptions=(Exception,),
                operation_name=operation_name,
            )
        return retry(
            self.retriever.search,
            query,
            top_k=top_k,
            candidate_pool=candidate_pool,
            max_attempts=3,
            retryable_exceptions=(Exception,),
            operation_name=operation_name,
        )

    @staticmethod
    def _title_tokens(title: str) -> set:
        return {t for t in re.findall(r"[a-z0-9]+", str(title or "").lower()) if len(t) >= 3}

    def _titles_index(self) -> dict:
        """{(act, section): section_title} built once from retriever records."""
        index = getattr(self, "_title_index", None)
        if index is None:
            index = {}
            for record in getattr(self.retriever, "records", None) or []:
                meta = record.get("metadata") or {}
                title = meta.get("section_title")
                section = meta.get("section_number")
                if not title or section in (None, ""):
                    continue
                act = self._compare_hit_act(record)
                if act:
                    index[(act, str(section).strip().upper().replace(" ", ""))] = str(title)
            self._title_index = index
        return index

    def _pick_reverse_counterpart(self, bns_section, candidates):
        """Pick the IPC entry for a BNS section among mapping duplicates.

        mapping.json contains 111 duplicate `new` values (several IPC
        sections consolidate into one BNS section), and the old first-match
        in dict order returned IPC 94 "Act to which a person is compelled by
        threats" for BNS 103 "Punishment for murder" - while candidate IPC
        304 "Punishment for culpable homicide not amounting to murder" is
        the sensible comparison. The tie-break scores each candidate's
        corpus section_title by token overlap against the BNS section's own
        corpus title: data-driven, no section numbers hardcoded, and it only
        reorders candidates mapping.json itself provides. Ties and missing
        titles keep the original first-entry behaviour.
        """
        if len(candidates) == 1:
            section, mapped = candidates[0]
            return section, mapped.get("note")
        titles = self._titles_index()
        target_key = ("BNS", str(bns_section).strip().upper().replace(" ", ""))
        target_tokens = self._title_tokens(titles.get(target_key, ""))
        if not target_tokens:
            section, mapped = candidates[0]
            return section, mapped.get("note")
        best_section, best_mapped = candidates[0]
        best_score = -1
        for ipc_section, mapped in candidates:
            cand_key = ("IPC", str(ipc_section).strip().upper().replace(" ", ""))
            score = len(target_tokens & self._title_tokens(titles.get(cand_key, "")))
            if score > best_score:
                best_section, best_mapped, best_score = ipc_section, mapped, score
        return best_section, best_mapped.get("note")

    @staticmethod
    def _compare_hit_act(item: dict) -> str:
        """Canonical act ('IPC'/'BNS') for a raw retrieval hit, '' if unknown."""
        raw = str(item.get("act") or "").strip().upper()
        if raw in ("IPC", "BNS"):
            return raw
        meta = item.get("metadata") or {}
        blob = " ".join(
            str(meta.get(key, ""))
            for key in ("real_act_name", "act_name", "act", "source")
        ).upper()
        if "BHARATIYA NYAYA" in blob:
            return "BNS"
        if "INDIAN PENAL" in blob:
            return "IPC"
        return ""

    @staticmethod
    def _compare_hit_section(item: dict) -> str:
        meta = item.get("metadata") or {}
        for key in ("section_number", "section"):
            val = meta.get(key)
            if val not in (None, ""):
                return str(val).strip().upper().replace(" ", "")
        cit = item.get("citation") or {}
        val = cit.get("section") or cit.get("provision")
        return str(val or "").strip().upper().replace(" ", "")

    def _select_compare_panel(self, items, want_act, want_section, page_size):
        """Keep only exact-section cards of the wanted act for a compare panel.

        A panel headed "BNS Results" must not show IPC cards (their
        bookTitle would contradict the heading) and a request for section
        302 must not lead with a neighbour. Measured 2026-10-03 on 40
        sections per direction: raw ranking gave the correct act at top-1
        only 77.5% of the time and fully act-pure panels 17.5%; after the
        first (act-only) fix every nonempty panel was act-pure but sections
        absent from an act (BNS has 1-358 only) still showed same-act
        neighbours - e.g. BNS 394 returned BNS 39. Exact-only means a panel
        is either the section's own cards or empty, never a lookalike.

        Passthrough (unfiltered pool) when the pool carries no recognisable
        act at all, so metadata-poor stubs are never emptied.
        """
        want_act = str(want_act or "").strip().upper()
        want_sec = str(want_section or "").strip().upper().replace(" ", "")
        if not items:
            return items
        if not want_act:
            return items[:page_size]
        acts = [self._compare_hit_act(item) for item in items]
        if not any(acts):
            return items[:page_size]
        exact = [
            item
            for item, act in zip(items, acts)
            if act == want_act and self._compare_hit_section(item) == want_sec
        ]
        return exact[:page_size]

    def route(self, query: str) -> RouteResponse:
        payload = self.router.get_route(query)
        normalized_query = None
        mappings: list[str] = []

        if payload.get("route") == "LEGAL_RESEARCH":
            normalized_query, mappings = self.router.normalize_query(query)

        return RouteResponse(
            route=payload.get("route", "GENERAL"),
            confidence=float(payload.get("confidence", 0.0)),
            hector_response=payload.get("hector_response", ""),
            normalized_query=normalized_query,
            mappings=mappings,
        )

    def status(self) -> StatusResponse:
        document_count = len(getattr(self.retriever, "records", []))
        # Also check Pinecone directly for accurate count
        pinecone_records = 0
        try:
            idx = getattr(self.retriever, "_pinecone", None)
            if idx is not None:
                stats = idx.describe_index_stats()
                pinecone_records = stats.get("total_vector_count", 0) if isinstance(stats, dict) else getattr(stats, "total_vector_count", 0)
        except Exception:
            pass
        # Use the higher of in-memory or Pinecone count
        effective_count = max(document_count, pinecone_records)
        status = "ok" if effective_count > 0 else "degraded"
        return StatusResponse(
            status=status,
            collection_name=getattr(self.retriever, "collection_name", "unknown"),
            document_count=effective_count,
            verifier_enabled=bool(self.orchestrator.enable_verification),
            semantic_search_enabled=not bool(
                getattr(self.retriever, "semantic_disabled", False)
            ),
            router_model=getattr(self.router, "model", "unknown"),
            uptime_seconds=int(time.time() - self.started_at),
        )

    def ingest(self, request: IngestRequest) -> IngestResponse:
        file_path = Path(request.file_path).expanduser()
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        if file_path.suffix.lower() != ".pdf":
            raise ValueError("Only PDF files are supported for ingestion.")

        from utils.enhanced_ingestor import EnhancedHectorIngestor

        ingestor = EnhancedHectorIngestor(reindex_mode=request.reindex_mode)
        result = ingestor.process_book(file_path.name, str(file_path))
        self.retriever.refresh_index()
        # New chunks may carry new section titles for the compare tie-break.
        self._title_index = None

        return IngestResponse(
            filename=result["filename"],
            pages=result["pages"],
            chunks=result["chunks"],
            reindex_mode=request.reindex_mode,
            collection_count=len(getattr(self.retriever, "records", [])),
            ingested_at=datetime.now(UTC),
        )

    def search_stream_events(self, request: SearchRequest):
        payload = self.route(request.query)
        yield {
            "event": "route",
            "data": payload.model_dump(),
        }

        result = self.search(request)
        yield {
            "event": "summary",
            "data": {
                "total_results": result.total_results,
                "page": result.page,
                "page_size": result.page_size,
                "generated_response": result.generated_response,
                "answer_sections": [
                    section.model_dump() for section in result.answer_sections
                ],
                "source_sections": [
                    section.model_dump() for section in result.source_sections
                ],
                "answer_confidence": result.answer_confidence,
                "citations": result.citations,
                "related_provisions": result.related_provisions,
            },
        }

        for item in result.items:
            yield {
                "event": "result",
                "data": item.model_dump(),
            }

        yield {
            "event": "complete",
            "data": {
                "retrieved_at": result.retrieved_at.isoformat(),
                "total_pages": result.total_pages,
            },
        }

    @staticmethod
    def _normalize_score(score: float) -> float:
        """Normalize a score to 0.0–1.0 range."""
        if score <= 0:
            return 0.0
        if score <= 1:
            return score
        return min(score / 100.0, 1.0)

    def _to_hit(self, item: dict) -> SearchHit:
        document = item.get("document", "")
        metadata = dict(item.get("metadata") or {})
        snippet = " ".join(document.split())
        if len(snippet) > 280:
            snippet = snippet[:277].rstrip() + "..."

        raw_similarity = float(
            item.get("similarity_score", item.get("score", 0.0)) or 0.0
        )
        raw_reranker = float(
            item.get("reranker_score", item.get("similarity_score", 0.0)) or 0.0
        )
        raw_boost = float(item.get("boost_score", 0.0) or 0.0)

        return SearchHit(
            id=str(item.get("id", "")),
            score=float(item.get("score", 0.0)),
            similarity_score=self._normalize_score(raw_similarity),
            reranker_score=self._normalize_score(raw_reranker),
            hybrid_score=self._normalize_score(
                float(item.get("hybrid_score", 0.0) or 0.0)
            ),
            retrieval_score=self._normalize_score(
                float(item.get("retrieval_score", 0.0) or 0.0)
            ),
            boost_score=self._normalize_score(raw_boost),
            semantic_score=self._normalize_score(
                float(item.get("semantic_score", 0.0) or 0.0)
            ),
            bm25_score=self._normalize_score(float(item.get("bm25_score", 0.0) or 0.0)),
            bm25_raw_score=float(item.get("bm25_raw_score", 0.0) or 0.0),
            act=item.get("act"),
            citation=dict(item.get("citation") or {}),
            reasons=list(item.get("reasons") or []),
            metadata=metadata,
            document=document,
            snippet=snippet,
        )


def build_cache_key(prefix: str, payload: dict) -> str:
    return f"{prefix}:{json.dumps(payload, sort_keys=True, default=str)}"
