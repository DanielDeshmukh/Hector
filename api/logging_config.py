"""Structured logging configuration for HECTOR."""
import json
import logging
import os
import sys
import time
from contextvars import ContextVar
from datetime import datetime, timezone

# Context variable for request ID propagation
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


class StructuredFormatter(logging.Formatter):
    """JSON structured log formatter with request ID context."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_var.get("-"),
        }
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "extra_data"):
            log_entry["data"] = record.extra_data
        return json.dumps(log_entry)


class ReadableFormatter(logging.Formatter):
    """Human-readable formatter for local development."""

    def format(self, record: logging.LogRecord) -> str:
        req_id = request_id_var.get("-")
        prefix = f"[{req_id[:8]}] " if req_id != "-" else ""
        return f"{prefix}{record.levelname:8s} {record.name}: {record.getMessage()}"


def setup_logging():
    """Configure structured logging for HECTOR."""
    log_level = os.getenv("HECTOR_LOG_LEVEL", "INFO").upper()
    debug = os.getenv("HECTOR_DEBUG", "false").lower() == "true"

    handler = logging.StreamHandler(sys.stdout)
    if debug or os.getenv("HECTOR_LOG_FORMAT", "") == "text":
        handler.setFormatter(ReadableFormatter())
    else:
        handler.setFormatter(StructuredFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level, logging.INFO))
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    # Suppress noisy third-party loggers
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def log_request(method: str, path: str, status_code: int, duration_ms: float, request_id: str | None = None):
    """Log an HTTP request with timing."""
    logger = logging.getLogger("api.access")
    logger.info(
        "%s %s -> %s (%.1fms)",
        method,
        path,
        status_code,
        duration_ms,
    )


def log_search(query: str, route: str, results_count: int, duration_ms: float, request_id: str | None = None):
    """Log a search query with results."""
    logger = logging.getLogger("api.search")
    logger.info(
        "search route=%s results=%d duration=%.1fms query=%s",
        route,
        results_count,
        duration_ms,
        query[:100],
    )


def log_ingest(book: str, chunks: int, duration_ms: float):
    """Log an ingestion event."""
    logger = logging.getLogger("api.ingest")
    logger.info(
        "ingest book=%s chunks=%d duration=%.1fms",
        book,
        chunks,
        duration_ms,
    )


def log_auth(event: str, subject: str, success: bool):
    """Log an authentication event."""
    logger = logging.getLogger("api.auth")
    level = logging.INFO if success else logging.WARNING
    logger.log(
        level,
        "auth event=%s subject=%s success=%s",
        event,
        subject,
        success,
    )
