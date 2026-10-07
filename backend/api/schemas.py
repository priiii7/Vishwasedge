"""Pydantic v2 request/response models for the API."""

from typing import Any

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class MeResponse(BaseModel):
    username: str
    role: str
    permissions: list[str]


class QueryOptionsSchema(BaseModel):
    stream: bool = False
    include_explanation: bool = True
    max_docs: int = Field(default=5, ge=1, le=20)


class QueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    context: dict[str, Any] | None = None
    options: QueryOptionsSchema = Field(default_factory=QueryOptionsSchema)


class SourceSchema(BaseModel):
    chunk_id: str
    source: str
    confidence: float
    reason: str
    excerpt: str


class ExplanationSchema(BaseModel):
    confidence_score: float
    calibration: str
    sources: list[SourceSchema]
    token_saliency: list[dict[str, Any]]
    alternate_paths: list[str]
    explanation_latency_ms: float


class RetrievalMetadataSchema(BaseModel):
    num_docs_considered: int
    num_docs_used: int
    reranker_used: bool
    latency_ms: float
    degradation_strategy: str | None = None


class QueryResponse(BaseModel):
    response: str
    confidence: float
    tier_used: str
    latency_ms: float
    warnings: list[str] = Field(default_factory=list)
    explanation: ExplanationSchema | None = None
    retrieval_metadata: RetrievalMetadataSchema


class DocumentUploadResponse(BaseModel):
    job_id: str
    status: str
    estimated_chunks: int


class DocumentStatusResponse(BaseModel):
    job_id: str
    status: str
    chunks_indexed: int
    errors: list[str]
