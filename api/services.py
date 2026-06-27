from __future__ import annotations

import json
import logging
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

    def search(self, request: SearchRequest) -> SearchResponse:
        intent = self.router.get_route(request.query)
        normalized_query = request.query
        mappings: list[str] = []

        if intent.get("route") == "LEGAL_RESEARCH":
            normalized_query, mappings = self.router.normalize_query(request.query)

        total_needed = max(request.page * request.page_size, request.page_size)
        retrieval_window = max(25, total_needed)
        results = retry(
            self.retriever.search,
            normalized_query,
            top_k=retrieval_window,
            candidate_pool=max(40, retrieval_window * 2),
            max_attempts=3,
            retryable_exceptions=(Exception,),
            operation_name="chromadb_search",
        )
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

        if intent.get("route") == "LEGAL_RESEARCH":
            response_data = self.response_generator.generate(
                query=request.query,
                results=paginated,
                format=request.format,
                include_related=request.include_related,
            )
            generated_response = response_data["generated_response"]
        else:
            generated_response = intent.get("hector_response", "")

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
        if generated_response and intent.get("route") == "LEGAL_RESEARCH":
            from core.verifier import HallucinationDetector

            verification_result = {
                "verified_response": generated_response,
                "citation_coverage": raw_confidence / 100.0,
                "total_claims": len(paginated),
                "claims_verified": int(len(paginated) * raw_confidence / 100.0),
            }
            hallucination_check = HallucinationDetector.generate_hallucination_report(
                verification_result
            )

        return SearchResponse(
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
        )

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
            for ipc_section, mapped in mapping.items():
                if str(mapped.get("new")).upper() == request.section:
                    counterpart_act = "IPC"
                    counterpart_section = ipc_section
                    note = mapped.get("note")
                    break

        requested_query = f"Section {request.section} {request.act}"
        requested_results = retry(
            self.retriever.search,
            requested_query,
            top_k=request.page_size,
            max_attempts=3,
            retryable_exceptions=(Exception,),
            operation_name="chromadb_compare_requested",
        )

        counterpart_results = []
        if counterpart_act and counterpart_section:
            counterpart_query = f"Section {counterpart_section} {counterpart_act}"
            counterpart_results = retry(
                self.retriever.search,
                counterpart_query,
                top_k=request.page_size,
                max_attempts=3,
                retryable_exceptions=(Exception,),
                operation_name="chromadb_compare_counterpart",
            )

        return CompareResponse(
            requested_act=request.act,
            requested_section=request.section,
            counterpart_act=counterpart_act,
            counterpart_section=counterpart_section,
            note=note,
            requested_results=[self._to_hit(item) for item in requested_results],
            counterpart_results=[self._to_hit(item) for item in counterpart_results],
            compared_at=datetime.now(UTC),
        )

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
        status = "ok" if document_count > 0 else "degraded"
        return StatusResponse(
            status=status,
            collection_name=getattr(self.retriever, "collection_name", "unknown"),
            document_count=document_count,
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

    def _to_hit(self, item: dict) -> SearchHit:
        document = item.get("document", "")
        metadata = dict(item.get("metadata") or {})
        snippet = " ".join(document.split())
        if len(snippet) > 280:
            snippet = snippet[:277].rstrip() + "..."

        return SearchHit(
            id=str(item.get("id", "")),
            score=float(item.get("score", 0.0)),
            similarity_score=float(
                item.get("similarity_score", item.get("score", 0.0)) or 0.0
            ),
            reranker_score=float(
                item.get("reranker_score", item.get("similarity_score", 0.0)) or 0.0
            ),
            hybrid_score=float(item.get("hybrid_score", 0.0) or 0.0),
            retrieval_score=float(item.get("retrieval_score", 0.0) or 0.0),
            boost_score=float(item.get("boost_score", 0.0) or 0.0),
            semantic_score=float(item.get("semantic_score", 0.0) or 0.0),
            bm25_score=float(item.get("bm25_score", 0.0) or 0.0),
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
