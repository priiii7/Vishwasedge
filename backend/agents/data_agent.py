"""Data Agent: document retrieval orchestration — HER search -> rerank -> CGR grounding."""

import time
from dataclasses import dataclass

from backend.agents.grounding_agent import GroundingResult, ground
from backend.rag.hybrid_retriever import hybrid_search
from backend.rag.reranker import rerank


@dataclass
class RetrievalOutcome:
    grounding: GroundingResult
    num_considered: int
    latency_ms: float
    reranker_used: bool


def retrieve(query: str, max_docs: int = 5, candidate_k: int = 15) -> RetrievalOutcome:
    start = time.perf_counter()

    candidates = hybrid_search(query, k=candidate_k)
    from backend.rag.reranker import _get_cross_encoder

    reranker_used = _get_cross_encoder() is not None
    top = rerank(query, candidates, top_k=max_docs)
    grounding = ground(top)

    latency_ms = (time.perf_counter() - start) * 1000
    return RetrievalOutcome(
        grounding=grounding,
        num_considered=len(candidates),
        latency_ms=round(latency_ms, 3),
        reranker_used=reranker_used,
    )
