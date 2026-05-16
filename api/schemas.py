from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=2000)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=5, ge=1, le=50)
    verify: bool = True
    format: Literal["summary", "detailed", "citations"] = "summary"
    include_related: bool = True


class CompareRequest(BaseModel):
    section: str = Field(..., min_length=1, max_length=20)
    act: Literal["IPC", "BNS"] = "IPC"
    page_size: int = Field(default=3, ge=1, le=20)

    @field_validator("section")
    @classmethod
    def normalize_section(cls, value: str) -> str:
        return value.strip().upper()


class RouteRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)


class IngestRequest(BaseModel):
    file_path: str = Field(..., min_length=3, max_length=4096)
    reindex_mode: bool = False


class SearchHit(BaseModel):
    id: str
    score: float
    act: str | None = None
    citation: dict[str, Any] = Field(default_factory=dict)
    reasons: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    snippet: str


class SearchResponse(BaseModel):
    route: str
    query: str
    normalized_query: str
    verification_enabled: bool
    total_results: int
    page: int
    page_size: int
    total_pages: int
    items: list[SearchHit]
    generated_response: str
    citations: list[dict] = Field(default_factory=list)
    related_provisions: list[str] = Field(default_factory=list)
    response_format: str = "summary"
    retrieved_at: datetime
    cached: bool = False


class CompareResponse(BaseModel):
    requested_act: str
    requested_section: str
    counterpart_act: str | None = None
    counterpart_section: str | None = None
    note: str | None = None
    requested_results: list[SearchHit] = Field(default_factory=list)
    counterpart_results: list[SearchHit] = Field(default_factory=list)
    compared_at: datetime
    cached: bool = False


class RouteResponse(BaseModel):
    route: str
    confidence: float
    hector_response: str
    normalized_query: str | None = None
    mappings: list[str] = Field(default_factory=list)
    cached: bool = False


class IngestResponse(BaseModel):
    filename: str
    pages: int
    chunks: int
    reindex_mode: bool
    collection_count: int
    ingested_at: datetime


class StatusResponse(BaseModel):
    status: Literal["ok", "degraded"]
    collection_name: str
    document_count: int
    verifier_enabled: bool
    semantic_search_enabled: bool
    router_model: str
    uptime_seconds: int
    cached: bool = False
