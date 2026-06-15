import json
import logging
import os
from threading import Lock
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .cache import TTLCache
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

logger = logging.getLogger(__name__)


cache = TTLCache(ttl_seconds=60, max_items=256)
rate_limiter = InMemoryRateLimiter(limit=60, window_seconds=60)
_service: HectorApiService | None = None
_service_lock = Lock()


@asynccontextmanager
async def lifespan(_: FastAPI):
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
    expose_headers=["X-RateLimit-Remaining", "X-RateLimit-Reset"],
    max_age=3600,
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=str(exc.detail),
            status_code=exc.status_code,
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
        ).model_dump(),
    )


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    # Reject oversized requests (10MB limit)
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > 10 * 1024 * 1024:
        return JSONResponse(
            status_code=413,
            content={"error": "Request too large", "detail": "Maximum request size is 10MB.", "status_code": 413},
        )
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
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


def enforce_rate_limit(auth_payload=Depends(require_auth)):
    key = f"{auth_payload['auth_type']}:{auth_payload['subject']}"
    try:
        rate_limiter.check(key)
    except RateLimitExceeded as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    return auth_payload


@app.get("/status")
def status_endpoint(
    _: dict = Depends(enforce_rate_limit),
    svc: HectorApiService = Depends(get_service),
):
    cache_key = build_cache_key("status", {})
    cached = cache.get(cache_key)
    if cached:
        cached["cached"] = True
        return cached

    payload = svc.status().model_dump(mode="json")
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

    payload = svc.search(request).model_dump(mode="json")
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
    api_key = websocket.headers.get("x-api-key") or websocket.query_params.get("api_key")
    bearer = websocket.headers.get("authorization")

    try:
        auth_payload = auth_manager.authenticate_headers(authorization=bearer, x_api_key=api_key)
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
