import json
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect

from .cache import TTLCache
from .rate_limit import InMemoryRateLimiter, RateLimitExceeded
from .schemas import (
    CompareRequest,
    IngestRequest,
    RouteRequest,
    SearchRequest,
    TokenResponse,
)
from .security import auth_manager, require_auth
from .services import HectorApiService, build_cache_key


cache = TTLCache(ttl_seconds=60, max_items=256)
rate_limiter = InMemoryRateLimiter(limit=60, window_seconds=60)
_service: HectorApiService | None = None


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield


app = FastAPI(
    title="HECTOR API",
    version="9.0.0",
    summary="REST and streaming API for grounded Indian legal research.",
    lifespan=lifespan,
)


def get_service() -> HectorApiService:
    global _service
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
def issue_token(x_api_key: str = Query(..., alias="api_key")):
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
            request = SearchRequest.model_validate(json.loads(raw_payload))
            for event in resolve_service().search_stream_events(request):
                await websocket.send_json(event)
    except WebSocketDisconnect:
        return
