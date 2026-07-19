import json
import logging
import os
import shutil
import time
import uuid
from threading import Lock
from contextlib import asynccontextmanager

from utils.retry import retry

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Query,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .cache import TTLCache
from .log_redaction import install_redaction_filter
from .logging_config import log_request, log_search, request_id_var, setup_logging
from .metrics import metrics
from .rate_limit import InMemoryRateLimiter, RateLimitExceeded
from .schemas import (
    CompareRequest,
    ErrorResponse,
    IngestRequest,
    RouteRequest,
    SearchRequest,
    TokenResponse,
)
from .security import auth_manager, require_auth
from .services import HectorApiService, build_cache_key

setup_logging()
install_redaction_filter()
logger = logging.getLogger(__name__)


cache = TTLCache(ttl_seconds=60, max_items=256)
rate_limiter = InMemoryRateLimiter(limit=60, window_seconds=60)
_service: HectorApiService | None = None
_service_lock = Lock()


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Pre-warming HECTOR service (loading models, BM25 index)...")
    try:
        get_service()
        logger.info("Service ready.")
    except Exception as e:
        logger.warning("Service pre-warm failed (will retry on first request): %s", e)
    yield


app = FastAPI(
    title="HECTOR API",
    version="2.1.0",
    summary="REST and streaming API for grounded Indian legal research.",
    lifespan=lifespan,
)

# CORS origins from environment or defaults
_cors_origins_str = os.getenv("HECTOR_CORS_ORIGINS", "")
_cors_origins = (
    [o.strip() for o in _cors_origins_str.split(",") if o.strip()]
    if _cors_origins_str
    else [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]
)

# CORS middleware must be added FIRST to handle preflight requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "X-API-Key", "Content-Type"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
    max_age=3600,
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    error_code = (
        "AUTH_REQUIRED"
        if exc.status_code == 401
        else "RATE_LIMITED"
        if exc.status_code == 429
        else "NOT_FOUND"
        if exc.status_code == 404
        else "INVALID_REQUEST"
        if exc.status_code == 400
        else "INTERNAL_ERROR"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=str(exc.detail),
            status_code=exc.status_code,
            error_code=error_code,
            request_id=getattr(request.state, "request_id", None),
        ).model_dump(),
    )


@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    logger.warning("ValueError: %s", exc)
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            error="Invalid request",
            detail="The request contains invalid parameters.",
            status_code=400,
            error_code="INVALID_REQUEST",
            request_id=getattr(request.state, "request_id", None),
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            detail="An unexpected error occurred. Please try again later.",
            status_code=500,
            error_code="INTERNAL_ERROR",
            request_id=getattr(request.state, "request_id", None),
        ).model_dump(),
    )


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    # Generate request ID and set in context var for logging
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    token = request_id_var.set(request_id)

    # Reject oversized requests (10MB limit)
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > 10 * 1024 * 1024:
        return JSONResponse(
            status_code=413,
            content={
                "error": "Request too large",
                "detail": "Maximum request size is 10MB.",
                "status_code": 413,
                "error_code": "REQUEST_TOO_LARGE",
            },
        )

    start_time = time.time()
    try:
        response = await call_next(request)
    finally:
        request_id_var.reset(token)

    duration_ms = round((time.time() - start_time) * 1000, 1)

    # Log access
    log_request(
        request.method, request.url.path, response.status_code, duration_ms, request_id
    )

    # Record metrics
    metrics.inc("http_requests_total")
    path_label = request.url.path
    if path_label.startswith("/ws"):
        path_label = "/ws/*"
    metrics.inc(f"http_requests{{path={path_label}}}")
    if response.status_code >= 400:
        metrics.inc("http_errors_total")
    metrics.observe("http_request_duration", duration_ms / 1000.0)

    response.headers["X-Request-Id"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["X-Response-Time"] = f"{duration_ms}ms"
    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )

    # Add rate limit headers if available
    rate_limit_info = getattr(request.state, "rate_limit", None)
    if rate_limit_info:
        response.headers["X-RateLimit-Limit"] = str(rate_limit_info.limit)
        response.headers["X-RateLimit-Remaining"] = str(rate_limit_info.remaining)
        response.headers["X-RateLimit-Reset"] = str(rate_limit_info.reset_seconds)

    return response


def get_service() -> HectorApiService:
    global _service
    if _service is None:
        with _service_lock:
            if _service is None:
                _service = HectorApiService()
    return _service


def resolve_service() -> HectorApiService:
    override = app.dependency_overrides.get(get_service)
    if override is not None:
        return override()
    return get_service()


def enforce_rate_limit(
    request: Request,
    auth_payload=Depends(require_auth),
):
    key = f"{auth_payload['auth_type']}:{auth_payload['subject']}"
    try:
        info = rate_limiter.check(key)
        request.state.rate_limit = info
    except RateLimitExceeded as exc:
        raise HTTPException(
            status_code=429,
            detail=str(exc),
            headers={"Retry-After": str(exc.retry_after)},
        ) from exc
    return auth_payload


@app.get("/healthz")
def healthz():
    """Liveness probe - returns 200 if the process is running."""
    return {"status": "ok"}


@app.get("/readyz")
def readyz(svc: HectorApiService = Depends(get_service)):
    """Readiness probe - checks ChromaDB and critical dependencies."""
    checks = {}
    healthy = True

    # ChromaDB check
    try:
        count = retry(
            svc.retriever.collection.count,
            max_attempts=2,
            operation_name="chromadb_count_readyz",
        )
        checks["chromadb"] = {"status": "ok", "records": count}
        metrics.set("chromadb_records", count)
    except Exception as exc:
        checks["chromadb"] = {"status": "error", "detail": str(type(exc).__name__)}
        healthy = False

    # Disk space check
    try:
        db_path = os.getenv(
            "HECTOR_DB_PATH",
            os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "hector_db"
            ),
        )
        usage = shutil.disk_usage(db_path)
        free_mb = usage.free // (1024 * 1024)
        checks["disk"] = {"status": "ok", "free_mb": free_mb}
        metrics.set("disk_free_mb", free_mb)
        if free_mb < 100:
            checks["disk"]["status"] = "warning"
    except Exception:
        checks["disk"] = {"status": "unknown"}

    # Groq API check
    try:
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key and hasattr(svc.router, "client") and svc.router.client is not None:
            svc.router.client.models.list()
            checks["groq"] = {"status": "ok"}
        else:
            checks["groq"] = {"status": "unavailable"}
    except Exception as exc:
        checks["groq"] = {"status": "error", "detail": type(exc).__name__}

    # Embedding model check
    try:
        if (
            hasattr(svc.retriever, "embedding_fn")
            and svc.retriever.embedding_fn is not None
        ):
            checks["embedding_model"] = {"status": "ok"}
        else:
            checks["embedding_model"] = {"status": "unavailable"}
            healthy = False
    except Exception as exc:
        checks["embedding_model"] = {"status": "error", "detail": type(exc).__name__}
        healthy = False

    metrics.inc("healthcheck_total")
    return {"status": "ok" if healthy else "degraded", "checks": checks}


@app.get("/metrics")
def metrics_endpoint():
    """Prometheus-compatible metrics endpoint."""
    from fastapi.responses import PlainTextResponse

    # Expose cache metrics as Prometheus gauges
    cache_metrics = cache.get_metrics()
    metrics.set("cache_size", cache_metrics["size"])
    metrics.set("cache_hits", cache_metrics["hits"])
    metrics.set("cache_misses", cache_metrics["misses"])
    metrics.set("cache_evictions", cache_metrics["evictions"])
    metrics.set("cache_hit_rate_percent", cache_metrics["hit_rate_percent"])

    return PlainTextResponse(
        metrics.render(), media_type="text/plain; version=0.0.4; charset=utf-8"
    )


@app.get("/status")
def status_endpoint(
    request: Request,
    _: dict = Depends(enforce_rate_limit),
    svc: HectorApiService = Depends(get_service),
):
    cache_key = build_cache_key("status", {})
    cached = cache.get(cache_key)
    if cached:
        cached["cached"] = True
        cached["request_id"] = getattr(request.state, "request_id", None)
        return cached

    payload = svc.status().model_dump(mode="json")

    # Add health checks
    try:
        retry(
            svc.retriever.collection.count,
            max_attempts=2,
            operation_name="chromadb_count_status",
        )
        payload["chromadb_connected"] = True
    except Exception:
        payload["chromadb_connected"] = False

    try:
        db_path = os.getenv(
            "HECTOR_DB_PATH",
            os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "hector_db"
            ),
        )
        usage = shutil.disk_usage(db_path)
        payload["disk_space_mb"] = usage.free // (1024 * 1024)
    except Exception:
        payload["disk_space_mb"] = 0

    # Groq API connectivity check
    try:
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key and hasattr(svc.router, "client") and svc.router.client is not None:
            svc.router.client.models.list()
            payload["groq_connected"] = True
        else:
            payload["groq_connected"] = False
    except Exception:
        payload["groq_connected"] = False

    # Embedding model availability check
    try:
        if (
            hasattr(svc.retriever, "embedding_fn")
            and svc.retriever.embedding_fn is not None
        ):
            payload["embedding_model_loaded"] = True
        else:
            payload["embedding_model_loaded"] = False
    except Exception:
        payload["embedding_model_loaded"] = False

    # Set status based on health
    if not payload.get("chromadb_connected"):
        payload["status"] = "degraded"

    # Add cache metrics
    payload["cache"] = cache.get_metrics()

    payload["request_id"] = getattr(request.state, "request_id", None)
    cache.set(cache_key, payload)
    return payload


@app.post("/auth/token", response_model=TokenResponse)
def issue_token(
    x_api_key: str = Query(..., alias="api_key"),
    _: dict = Depends(enforce_rate_limit),
):
    if not auth_manager.verify_api_key(x_api_key):
        raise HTTPException(status_code=401, detail="Invalid API key.")
    return TokenResponse(
        access_token=auth_manager.issue_token(),
        expires_in=auth_manager.jwt_expiry_seconds,
    )


@app.post("/route")
def route_endpoint(
    request: RouteRequest,
    _: dict = Depends(enforce_rate_limit),
    svc: HectorApiService = Depends(get_service),
):
    cache_key = build_cache_key("route", request.model_dump())
    cached = cache.get(cache_key)
    if cached:
        cached["cached"] = True
        return cached

    payload = svc.route(request.query).model_dump(mode="json")
    cache.set(cache_key, payload)
    return payload


@app.post("/search")
def search_endpoint(
    request: SearchRequest,
    _: dict = Depends(enforce_rate_limit),
    svc: HectorApiService = Depends(get_service),
):
    cache_key = build_cache_key("search", request.model_dump())
    cached = cache.get(cache_key)
    if cached:
        cached["cached"] = True
        return cached

    start = time.time()
    payload = svc.search(request).model_dump(mode="json")
    duration_ms = round((time.time() - start) * 1000, 1)

    log_search(
        query=request.query,
        route=payload.get("route", "unknown"),
        results_count=len(payload.get("sources", [])),
        duration_ms=duration_ms,
    )

    # Record search metrics
    metrics.inc("search_queries_total")
    metrics.inc(f"search_route{{route={payload.get('route', 'unknown')}}}")
    metrics.observe("search_duration", duration_ms / 1000.0)
    metrics.set("search_results_last", len(payload.get("sources", [])))

    cache.set(cache_key, payload)
    return payload


@app.post("/compare")
def compare_endpoint(
    request: CompareRequest,
    _: dict = Depends(enforce_rate_limit),
    svc: HectorApiService = Depends(get_service),
):
    cache_key = build_cache_key("compare", request.model_dump())
    cached = cache.get(cache_key)
    if cached:
        cached["cached"] = True
        return cached

    payload = svc.compare(request).model_dump(mode="json")
    cache.set(cache_key, payload)
    return payload


@app.post("/ingest")
def ingest_endpoint(
    request: IngestRequest,
    _: dict = Depends(enforce_rate_limit),
    svc: HectorApiService = Depends(get_service),
):
    try:
        payload = svc.ingest(request).model_dump(mode="json")
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    cache.clear()
    return payload


@app.websocket("/ws/search")
async def search_websocket(websocket: WebSocket):
    api_key = websocket.headers.get("x-api-key") or websocket.query_params.get(
        "api_key"
    )
    bearer = websocket.headers.get("authorization")

    try:
        auth_payload = auth_manager.authenticate_headers(
            authorization=bearer, x_api_key=api_key
        )
        rate_limiter.check(f"ws:{auth_payload['auth_type']}:{auth_payload['subject']}")
    except HTTPException:
        await websocket.close(code=4401)
        return
    except RateLimitExceeded:
        await websocket.close(code=4429)
        return

    await websocket.accept()

    try:
        while True:
            raw_payload = await websocket.receive_text()
            try:
                data = json.loads(raw_payload)
                request = SearchRequest.model_validate(data)
            except (json.JSONDecodeError, ValueError):
                await websocket.send_json({"error": "Invalid request format"})
                continue
            for event in resolve_service().search_stream_events(request):
                await websocket.send_json(event)
    except WebSocketDisconnect:
        return
