"""Pluggable LLM client: Anthropic API tiers + a zero-dependency extractive
fallback so the system answers queries with no API key and no local model
download, per the AQR tier mapping in llm_router.py.

Includes a circuit breaker around the cloud call — repeated failures trip
the breaker and route straight to the extractive fallback until it cools
down, matching the spec's resilience requirement (§15 Fallback Strategy).
"""

import re
import time
from dataclasses import dataclass, field

from backend.core.config import get_settings
from backend.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class LLMResponse:
    text: str
    tier_used: str
    raw_confidence: float


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, reset_seconds: float = 30.0):
        self._failures = 0
        self._threshold = failure_threshold
        self._reset_seconds = reset_seconds
        self._opened_at: float | None = None

    def is_open(self) -> bool:
        if self._opened_at is None:
            return False
        if time.time() - self._opened_at > self._reset_seconds:
            self._opened_at = None
            self._failures = 0
            return False
        return True

    def record_success(self) -> None:
        self._failures = 0
        self._opened_at = None

    def record_failure(self) -> None:
        self._failures += 1
        if self._failures >= self._threshold:
            self._opened_at = time.time()
            logger.warning("circuit_breaker_open", failures=self._failures)


_breaker = CircuitBreaker()

SYSTEM_PROMPT = (
    "You are VishwasEdge, a trustworthy technical assistant for oil & gas operations. "
    "Answer strictly from the provided context. If the context doesn't contain the answer, "
    "say so plainly instead of guessing. Be concise and precise."
)


def _build_prompt(query: str, context_chunks: list[str]) -> str:
    context = "\n\n".join(f"[Source {i + 1}] {c}" for i, c in enumerate(context_chunks))
    return f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer using only the context above."


def _extractive_fallback(query: str, context_chunks: list[str]) -> LLMResponse:
    """No LLM call: rank sentences across retrieved chunks by lexical overlap
    with the query and stitch the top ones into an answer. Deterministic,
    <5ms, fully offline."""
    query_tokens = set(re.findall(r"[a-z0-9]+", query.lower()))
    sentences: list[tuple[str, float]] = []
    for chunk in context_chunks:
        for sentence in re.split(r"(?<=[.!?])\s+", chunk):
            sentence = sentence.strip()
            if not sentence:
                continue
            tokens = set(re.findall(r"[a-z0-9]+", sentence.lower()))
            overlap = len(tokens & query_tokens) / (len(query_tokens) or 1)
            sentences.append((sentence, overlap))

    sentences.sort(key=lambda s: s[1], reverse=True)
    top = [s for s, score in sentences[:3] if score > 0]

    if not top:
        return LLMResponse(
            text="I couldn't find directly relevant information in the retrieved documents to answer this confidently.",
            tier_used="fast",
            raw_confidence=0.2,
        )

    text = " ".join(top)
    avg_overlap = sum(score for _, score in sentences[:3]) / max(len(top), 1)
    return LLMResponse(text=text, tier_used="fast", raw_confidence=min(0.5 + avg_overlap * 0.3, 0.85))


def _call_anthropic(query: str, context_chunks: list[str], model: str, tier: str) -> LLMResponse | None:
    settings = get_settings()
    if not settings.anthropic_api_key or _breaker.is_open():
        return None
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key, timeout=15.0)
        message = client.messages.create(
            model=model,
            max_tokens=512,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": _build_prompt(query, context_chunks)}],
        )
        text = "".join(block.text for block in message.content if hasattr(block, "text"))
        _breaker.record_success()
        return LLMResponse(text=text, tier_used=tier, raw_confidence=0.8)
    except Exception as exc:  # noqa: BLE001
        logger.warning("llm_call_failed", tier=tier, error=str(exc))
        _breaker.record_failure()
        return None


def generate(query: str, context_chunks: list[str], tier: str) -> LLMResponse:
    settings = get_settings()
    model_by_tier = {"haiku": settings.llm_fast_model, "sonnet": settings.llm_heavy_model}

    if tier in model_by_tier:
        result = _call_anthropic(query, context_chunks, model_by_tier[tier], tier)
        if result is not None:
            return result
        logger.info("tier_fallback_to_extractive", requested_tier=tier)

    return _extractive_fallback(query, context_chunks)
