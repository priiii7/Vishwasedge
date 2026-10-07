"""REST endpoints: auth, document ingestion, query."""

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents.orchestrator import QueryOptions, handle_query
from backend.api.dependencies import CurrentUser, get_current_user, require_permission, user_permissions
from backend.api.schemas import (
    DocumentStatusResponse,
    DocumentUploadResponse,
    ExplanationSchema,
    LoginRequest,
    MeResponse,
    QueryRequest,
    QueryResponse,
    RetrievalMetadataSchema,
    TokenResponse,
)
from backend.core.config import get_settings
from backend.core.logging import get_logger
from backend.core.security import create_access_token, verify_password
from backend.db.models import Document, QueryLog, User
from backend.infrastructure.db import get_db
from backend.models.model_manager import get_model_status
from backend.rag.document_processor import SUPPORTED_SUFFIXES, process_document

logger = get_logger(__name__)

auth_router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
documents_router = APIRouter(prefix="/api/v1/documents", tags=["documents"])
query_router = APIRouter(prefix="/api/v1", tags=["query"])
system_router = APIRouter(prefix="/api/v1/system", tags=["system"])


@auth_router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    result = await db.execute(select(User).where(User.username == payload.username))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    token = create_access_token(subject=user.username, role=user.role)
    return TokenResponse(access_token=token, role=user.role)


@auth_router.get("/me", response_model=MeResponse)
async def me(user: CurrentUser = Depends(get_current_user)) -> MeResponse:
    return MeResponse(username=user.username, role=user.role, permissions=user_permissions(user))


@documents_router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    source: str = Form(default=""),
    category: str = Form(default="general"),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_permission("write")),
) -> DocumentUploadResponse:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise HTTPException(status_code=422, detail=f"Unsupported file type: {suffix}")

    settings = get_settings()
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    job_id = str(uuid.uuid4())
    dest = raw_dir / f"{job_id}{suffix}"
    content = await file.read()
    dest.write_bytes(content)

    document = Document(
        job_id=job_id,
        filename=file.filename or dest.name,
        source=source or (file.filename or ""),
        category=category,
        status="processing",
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)

    try:
        chunk_ids = process_document(dest, document_id=document.id, source=document.source)
        document.status = "completed"
        document.chunks_indexed = len(chunk_ids)
    except Exception as exc:  # noqa: BLE001
        logger.error("ingestion_failed", job_id=job_id, error=str(exc))
        document.status = "failed"
        document.errors = str(exc)

    await db.commit()

    return DocumentUploadResponse(
        job_id=job_id,
        status=document.status,
        estimated_chunks=document.chunks_indexed,
    )


@documents_router.get("/status/{job_id}", response_model=DocumentStatusResponse)
async def document_status(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> DocumentStatusResponse:
    result = await db.execute(select(Document).where(Document.job_id == job_id))
    document = result.scalar_one_or_none()
    if document is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return DocumentStatusResponse(
        job_id=job_id,
        status=document.status,
        chunks_indexed=document.chunks_indexed,
        errors=[document.errors] if document.errors else [],
    )


@documents_router.get("/list")
async def list_documents(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[dict]:
    result = await db.execute(select(Document).order_by(Document.created_at.desc()).limit(50))
    return [
        {
            "id": d.id,
            "filename": d.filename,
            "status": d.status,
            "chunks_indexed": d.chunks_indexed,
            "category": d.category,
            "created_at": d.created_at.isoformat(),
        }
        for d in result.scalars().all()
    ]


@query_router.post("/query", response_model=QueryResponse)
async def query(
    payload: QueryRequest,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_permission("query")),
) -> QueryResponse:
    options = QueryOptions(
        include_explanation=payload.options.include_explanation,
        max_docs=payload.options.max_docs,
    )
    result = await handle_query(payload.query, payload.context, options)

    db.add(
        QueryLog(
            username=user.username,
            query=payload.query,
            response=result.response_text,
            confidence=result.confidence,
            tier_used=result.tier_used,
            latency_ms=result.latency_ms,
        )
    )
    await db.commit()

    explanation = ExplanationSchema(**result.explanation) if result.explanation else None

    return QueryResponse(
        response=result.response_text,
        confidence=result.confidence,
        tier_used=result.tier_used,
        latency_ms=result.latency_ms,
        warnings=result.validation_warnings,
        explanation=explanation,
        retrieval_metadata=RetrievalMetadataSchema(
            num_docs_considered=result.retrieval.num_considered,
            num_docs_used=len(result.retrieval.grounding.grounded),
            reranker_used=result.retrieval.reranker_used,
            latency_ms=result.retrieval.latency_ms,
            degradation_strategy=result.degradation_strategy,
        ),
    )


@system_router.get("/models")
async def models_status(user: CurrentUser = Depends(get_current_user)) -> list[dict]:
    return [s.__dict__ for s in get_model_status()]
