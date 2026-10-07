"""CGR: Confidence-Grounded Retrieval — per-document confidence scoring +
relevance reasoning. Chunks below the 0.6 threshold are filtered, with the
reason surfaced back to the caller."""

from dataclasses import dataclass

from backend.rag.hybrid_retriever import RetrievedChunk

CONFIDENCE_THRESHOLD = 0.6


@dataclass
class GroundedChunk:
    chunk: RetrievedChunk
    confidence: float
    reason: str


@dataclass
class GroundingResult:
    grounded: list[GroundedChunk]
    filtered_out: list[GroundedChunk]


def _reason_for(chunk: RetrievedChunk, confidence: float) -> str:
    if confidence >= 0.85:
        return "strong lexical + semantic agreement with query"
    if confidence >= CONFIDENCE_THRESHOLD:
        return "moderate relevance signal from hybrid retrieval"
    if chunk.bm25_rank is None:
        return "matched only by dense retrieval — weak keyword overlap"
    if chunk.vector_rank is None:
        return "matched only by keyword search — weak semantic similarity"
    return "low combined confidence from both retrieval signals"


def ground(chunks: list[RetrievedChunk]) -> GroundingResult:
    grounded: list[GroundedChunk] = []
    filtered_out: list[GroundedChunk] = []

    for chunk in chunks:
        # confidence = calibrated blend of reranker score and retrieval-rank
        # agreement (present in both bm25 and vector top-k => more grounded)
        rerank_component = chunk.rerank_score if chunk.rerank_score is not None else chunk.fused_score
        agreement_bonus = 0.1 if (chunk.bm25_rank is not None and chunk.vector_rank is not None) else 0.0
        confidence = min(round(rerank_component + agreement_bonus, 4), 1.0)
        chunk.confidence = confidence

        item = GroundedChunk(chunk=chunk, confidence=confidence, reason=_reason_for(chunk, confidence))
        if confidence >= CONFIDENCE_THRESHOLD:
            grounded.append(item)
        else:
            filtered_out.append(item)

    return GroundingResult(grounded=grounded, filtered_out=filtered_out)
