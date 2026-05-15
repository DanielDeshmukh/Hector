from __future__ import annotations

import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

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

    def search(self, request: SearchRequest) -> SearchResponse:
        intent = self.router.get_route(request.query)
        normalized_query = request.query
        mappings: list[str] = []

        if intent.get("route") == "LEGAL_RESEARCH":
            normalized_query, mappings = self.router.normalize_query(request.query)

        total_needed = max(request.page * request.page_size, request.page_size)
        retrieval_window = max(25, total_needed)
        results = self.retriever.search(
            normalized_query,
            top_k=retrieval_window,
            candidate_pool=max(40, retrieval_window * 2),
        )
        total_results = len(results)
        start = (request.page - 1) * request.page_size
        end = start + request.page_size
        paginated = results[start:end]

        items = [self._to_hit(item) for item in paginated]

        if intent.get("route") == "LEGAL_RESEARCH":
            generated_response = self.orchestrator.execute(request.query) if request.verify else self.retriever.format_results(results[: request.page_size])
        else:
            generated_response = intent.get("hector_response", "")

        if mappings and generated_response:
            generated_response = f"Mapped legacy references: {'; '.join(mappings)}\n\n{generated_response}"

        total_pages = max(1, (total_results + request.page_size - 1) // request.page_size)
        return SearchResponse(
            route=intent.get("route", "GENERAL"),
            query=request.query,
            normalized_query=normalized_query,
            verification_enabled=bool(request.verify and getattr(self.orchestrator, "enable_verification", False)),
            total_results=total_results,
            page=request.page,
            page_size=request.page_size,
            total_pages=total_pages,
            items=items,
            generated_response=generated_response,
            retrieved_at=datetime.now(UTC),
        )

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
        requested_results = self.retriever.search(requested_query, top_k=request.page_size)

        counterpart_results = []
        if counterpart_act and counterpart_section:
            counterpart_query = f"Section {counterpart_section} {counterpart_act}"
            counterpart_results = self.retriever.search(counterpart_query, top_k=request.page_size)

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
            semantic_search_enabled=not bool(getattr(self.retriever, "semantic_disabled", False)),
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
            act=item.get("act"),
            citation=dict(item.get("citation") or {}),
            reasons=list(item.get("reasons") or []),
            metadata=metadata,
            snippet=snippet,
        )


def build_cache_key(prefix: str, payload: dict) -> str:
    return f"{prefix}:{json.dumps(payload, sort_keys=True, default=str)}"
