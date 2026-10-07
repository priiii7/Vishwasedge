"""Model lifecycle: reports which backends are actually active (loaded vs.
fallback) so the frontend/ops can see real system state instead of assuming
the spec's local GGUF models are present."""

from dataclasses import dataclass

from backend.core.config import get_settings


@dataclass
class ModelStatus:
    name: str
    role: str
    active: bool
    detail: str


def get_model_status() -> list[ModelStatus]:
    settings = get_settings()
    statuses: list[ModelStatus] = []

    from backend.rag.embeddings import HashingEmbedder, get_embedder

    embedder = get_embedder()
    statuses.append(
        ModelStatus(
            name=settings.embedding_model,
            role="embedding",
            active=not isinstance(embedder, HashingEmbedder),
            detail="sentence-transformers" if not isinstance(embedder, HashingEmbedder) else "offline hashing fallback",
        )
    )

    from backend.rag.reranker import _get_cross_encoder

    reranker_active = _get_cross_encoder() is not None
    statuses.append(
        ModelStatus(
            name=settings.reranker_model,
            role="reranker",
            active=reranker_active,
            detail="cross-encoder" if reranker_active else "RRF-score fallback",
        )
    )

    statuses.append(
        ModelStatus(
            name=settings.llm_fast_model if settings.anthropic_api_key else "extractive-fallback",
            role="llm-haiku-tier",
            active=bool(settings.anthropic_api_key),
            detail="Anthropic API" if settings.anthropic_api_key else "no API key — extractive answers only",
        )
    )
    statuses.append(
        ModelStatus(
            name=settings.llm_heavy_model if settings.anthropic_api_key else "extractive-fallback",
            role="llm-sonnet-tier",
            active=bool(settings.anthropic_api_key),
            detail="Anthropic API" if settings.anthropic_api_key else "no API key — extractive answers only",
        )
    )
    return statuses
