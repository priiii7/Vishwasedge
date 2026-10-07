"""LCE: Lightweight Counterfactual Explanations via token-gradient saliency.

Leave-one-token-out re-embedding + cosine distance from the base embedding.
O(n) in token count, no LLM call — per the spec's §Phase 5 algorithm.
"""

import time
from dataclasses import dataclass

from backend.rag.embeddings import cosine_similarity, encode_cached


@dataclass
class TokenSaliency:
    token: str
    importance: float


@dataclass
class ExplanationResult:
    token_saliency: list[TokenSaliency]
    alternate_paths: list[str]
    latency_ms: float


def _query_without_token(tokens: list[str], index: int) -> str:
    return " ".join(tokens[:index] + tokens[index + 1 :])


def token_gradient_saliency(query: str) -> tuple[list[TokenSaliency], float]:
    start = time.perf_counter()
    tokens = query.split()
    if not tokens:
        return [], 0.0

    base_embedding = encode_cached(query)
    results: list[TokenSaliency] = []

    for i, token in enumerate(tokens):
        perturbed = _query_without_token(tokens, i)
        if not perturbed:
            importance = 1.0
        else:
            perturbed_embedding = encode_cached(perturbed)
            importance = 1.0 - cosine_similarity(base_embedding, perturbed_embedding)
        results.append(TokenSaliency(token=token, importance=round(max(importance, 0.0), 4)))

    latency_ms = (time.perf_counter() - start) * 1000
    return results, latency_ms


WHAT_IF_TEMPLATES = [
    "If '{token}' were removed, the answer's relevance would drop by ~{impact:.0%} based on retrieval sensitivity.",
    "Replacing '{token}' with a broader term would likely retrieve different source documents.",
    "'{token}' is a high-salience anchor — the answer depends heavily on documents matching it.",
]


def generate_what_ifs(saliency: list[TokenSaliency], top_n: int = 3) -> list[str]:
    top = sorted(saliency, key=lambda t: t.importance, reverse=True)[:top_n]
    what_ifs = []
    for i, item in enumerate(top):
        template = WHAT_IF_TEMPLATES[i % len(WHAT_IF_TEMPLATES)]
        what_ifs.append(template.format(token=item.token, impact=item.importance))
    return what_ifs


def explain(query: str) -> ExplanationResult:
    saliency, latency_ms = token_gradient_saliency(query)
    what_ifs = generate_what_ifs(saliency)
    return ExplanationResult(token_saliency=saliency, alternate_paths=what_ifs, latency_ms=round(latency_ms, 3))
