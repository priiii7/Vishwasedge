"""Cross-encoder re-ranking of the fused HER candidate set.

Falls back to the RRF fused_score (already computed) if the cross-encoder
model can't be loaded, so reranking degrades gracefully rather than failing.
"""

from functools import lru_cache

from backend.core.config import get_settings
from backend.core.logging import get_logger
from backend.rag.hybrid_retriever import RetrievedChunk

logger = get_logger(__name__)


@lru_cache(maxsize=1)
def _get_cross_encoder():
    try:
        from sentence_transformers import CrossEncoder

        settings = get_settings()
        model = CrossEncoder(settings.reranker_model)
        logger.info("reranker_loaded", model=settings.reranker_model)
        return model
    except Exception as exc:  # noqa: BLE001
        logger.warning("reranker_fallback", reason=str(exc))
        return None


def _sigmoid(x: float) -> float:
    import math

    return 1.0 / (1.0 + math.exp(-x))


def rerank(query: str, candidates: list[RetrievedChunk], top_k: int = 5) -> list[RetrievedChunk]:
    if not candidates:
        return []

    model = _get_cross_encoder()
    if model is None:
        # Fallback: normalize fused RRF scores into a 0-1 range as the rerank score
        max_score = max((c.fused_score for c in candidates), default=1.0) or 1.0
        for c in candidates:
            c.rerank_score = c.fused_score / max_score
        ranked = sorted(candidates, key=lambda c: c.rerank_score, reverse=True)
        return ranked[:top_k]

    pairs = [(query, c.text) for c in candidates]
    raw_scores = model.predict(pairs)
    for c, score in zip(candidates, raw_scores):
        c.rerank_score = _sigmoid(float(score))

    ranked = sorted(candidates, key=lambda c: c.rerank_score, reverse=True)
    return ranked[:top_k]
