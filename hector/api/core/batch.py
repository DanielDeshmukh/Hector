"""
Batch Query — processes multiple legal research queries in sequence.

Accepts a list of queries, runs each through the full search pipeline,
and returns structured results. Useful for legal research firms that
need to process multiple questions at once.
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class BatchQueryItem:
    """A single query in a batch request."""
    query: str
    index: int


@dataclass
class BatchQueryResult:
    """Result for a single query in a batch."""
    index: int
    query: str
    route: str | None = None
    confidence: float | None = None
    generated_response: str | None = None
    result_count: int = 0
    response_ms: float | None = None
    cache_hit: bool = False
    error: str | None = None


@dataclass
class BatchJob:
    """A batch processing job."""
    job_id: str
    queries: list[str]
    results: list[BatchQueryResult] = field(default_factory=list)
    status: str = "pending"  # pending, running, completed, failed
    started_at: float | None = None
    completed_at: float | None = None
    total: int = 0
    completed_count: int = 0
    failed_count: int = 0


class BatchQueryProcessor:
    """Processes batch queries through the HECTOR search pipeline."""

    def __init__(self):
        self._service = None

    def _get_service(self):
        if self._service is None:
            from api.services import HectorApiService
            self._service = HectorApiService()
        return self._service

    def process_batch(
        self,
        queries: list[str],
        job_id: str | None = None,
    ) -> BatchJob:
        """
        Process a list of queries through the search pipeline.

        Args:
            queries: List of query strings to process
            job_id: Optional job identifier

        Returns:
            BatchJob with all results
        """
        import uuid
        from api.schemas import SearchRequest

        if not job_id:
            job_id = str(uuid.uuid4())[:8]

        job = BatchJob(
            job_id=job_id,
            queries=queries,
            total=len(queries),
            status="running",
            started_at=time.time(),
        )

        service = self._get_service()

        for i, query in enumerate(queries):
            try:
                t0 = time.perf_counter()
                request = SearchRequest(
                    query=query,
                    page=1,
                    page_size=5,
                    verify=True,
                    format="summary",
                    include_related=True,
                )
                result = service.search(request)
                elapsed_ms = (time.perf_counter() - t0) * 1000

                job.results.append(BatchQueryResult(
                    index=i,
                    query=query,
                    route=result.route,
                    confidence=result.answer_confidence,
                    generated_response=result.generated_response,
                    result_count=result.total_results,
                    response_ms=round(elapsed_ms, 1),
                    cache_hit=result.cached,
                ))
                job.completed_count += 1
                logger.info("Batch [%d/%d] completed: %s", i + 1, len(queries), query[:40])

            except Exception as e:
                job.results.append(BatchQueryResult(
                    index=i,
                    query=query,
                    error=str(e),
                ))
                job.failed_count += 1
                logger.warning("Batch [%d/%d] failed: %s — %s", i + 1, len(queries), query[:40], e)

        job.status = "completed"
        job.completed_at = time.time()
        return job

    def parse_csv(self, csv_text: str) -> list[str]:
        """Parse a CSV or newline-separated list of queries."""
        queries = []
        for line in csv_text.strip().split("\n"):
            line = line.strip().strip('"').strip("'")
            if line and not line.startswith("#"):
                queries.append(line)
        return queries

    def parse_text(self, text: str) -> list[str]:
        """Parse newline-separated queries from text input."""
        return self.parse_csv(text)

    def to_export_data(self, job: BatchJob) -> dict:
        """Convert batch job to exportable dict format."""
        return {
            "job_id": job.job_id,
            "total": job.total,
            "completed": job.completed_count,
            "failed": job.failed_count,
            "duration_ms": round(
                (job.completed_at or time.time()) - (job.started_at or time.time()), 1
            ),
            "results": [
                {
                    "index": r.index,
                    "query": r.query,
                    "route": r.route,
                    "confidence": r.confidence,
                    "response": r.generated_response,
                    "result_count": r.result_count,
                    "response_ms": r.response_ms,
                    "cache_hit": r.cache_hit,
                    "error": r.error,
                }
                for r in job.results
            ],
        }


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_instance: BatchQueryProcessor | None = None
_instance_lock = __import__("threading").Lock()


def get_batch_processor() -> BatchQueryProcessor:
    global _instance
    if _instance is None:
        with _instance_lock:
            if _instance is None:
                _instance = BatchQueryProcessor()
    return _instance
