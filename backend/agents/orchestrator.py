"""DAS: Dynamic Agent Scheduling — the orchestration engine.

Resource-aware task distribution: a psutil snapshot of CPU/RAM decides
whether a query runs the fast path, or degrades via simplify / offload /
queue, per the spec's §Phase 4 algorithm.
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any

import psutil

from backend.agents.data_agent import RetrievalOutcome, retrieve
from backend.agents.reasoning_agent import ReasoningOutcome, reason
from backend.agents.router_agent import route
from backend.core.config import get_settings
from backend.core.logging import get_logger
from backend.core.metrics import (
    ACTIVE_QUERIES,
    DEGRADATION_COUNT,
    EXPLANATION_LATENCY,
    QUERY_COUNT,
    QUERY_LATENCY,
    RESOURCE_CPU_PERCENT,
    RESOURCE_MEMORY_MB,
    RETRIEVAL_LATENCY,
)
from backend.models.llm_router import downgrade_tier, score_complexity
from backend.trust.confidence import compute_confidence
from backend.trust.explainer import explain
from backend.trust.monitor import confidence_monitor
from backend.trust.validator import validate_query, validate_response

logger = get_logger(__name__)

_task_queue: asyncio.Queue = asyncio.Queue()


@dataclass
class ResourceSnapshot:
    cpu_percent: float
    memory_percent: float
    process_memory_mb: float

    def is_stressed(self, max_cpu: int, max_memory_mb: int) -> bool:
        # Edge memory budget is this process's own footprint, not whole-machine
        # usage — on a shared dev box, total system memory is almost always
        # above a 4GB "edge device" budget even when this app is idle.
        return self.cpu_percent > max_cpu or self.process_memory_mb > max_memory_mb


class ResourceMonitor:
    def __init__(self) -> None:
        self._process = psutil.Process()

    def snapshot(self) -> ResourceSnapshot:
        vm = psutil.virtual_memory()
        return ResourceSnapshot(
            cpu_percent=psutil.cpu_percent(interval=0.0),
            memory_percent=vm.percent,
            process_memory_mb=self._process.memory_info().rss / (1024 * 1024),
        )


resource_monitor = ResourceMonitor()


@dataclass
class QueryOptions:
    include_explanation: bool = True
    max_docs: int = 5


@dataclass
class OrchestrationResult:
    response_text: str
    confidence: float
    calibration: str
    tier_used: str
    degradation_strategy: str | None
    retrieval: RetrievalOutcome
    reasoning: ReasoningOutcome
    explanation: dict[str, Any] | None
    validation_warnings: list[str]
    latency_ms: float


async def handle_query(query: str, context: dict | None, options: QueryOptions) -> OrchestrationResult:
    settings = get_settings()
    start = time.perf_counter()
    ACTIVE_QUERIES.inc()

    try:
        validation = validate_query(query)
        routed = route(query)

        snapshot = resource_monitor.snapshot()
        RESOURCE_CPU_PERCENT.set(snapshot.cpu_percent)
        RESOURCE_MEMORY_MB.set(snapshot.process_memory_mb)

        stressed = snapshot.is_stressed(settings.max_cpu_percent, settings.max_memory_mb)
        max_docs = options.max_docs
        strategy: str | None = None

        context_size = len(str(context or {}))
        complexity = score_complexity(routed.query, context_size=context_size)
        tier = complexity.tier

        if stressed:
            strategy = "simplify"
            max_docs = max(2, max_docs // 2)
            tier = downgrade_tier(tier)
            DEGRADATION_COUNT.labels(strategy=strategy).inc()
            logger.info("das_degradation", strategy=strategy, cpu=snapshot.cpu_percent, mem=snapshot.memory_percent)

        retrieval_start = time.perf_counter()
        retrieval = retrieve(routed.query, max_docs=max_docs)
        RETRIEVAL_LATENCY.observe((time.perf_counter() - retrieval_start) * 1000)

        reasoning = reason(routed.query, retrieval.grounding.grounded, tier)

        response_validation = validate_response(reasoning.response.text, reasoning.source_texts)
        warnings = validation.warnings + response_validation.warnings

        retrieval_quality = (
            sum(g.confidence for g in retrieval.grounding.grounded) / len(retrieval.grounding.grounded)
            if retrieval.grounding.grounded
            else 0.0
        )
        confidence_result = compute_confidence(retrieval_quality, reasoning.response.raw_confidence)
        confidence_monitor.record(confidence_result.calibrated_score)

        explanation: dict[str, Any] | None = None
        if options.include_explanation:
            exp_start = time.perf_counter()
            exp = explain(routed.query)
            EXPLANATION_LATENCY.observe((time.perf_counter() - exp_start) * 1000)
            explanation = {
                "confidence_score": confidence_result.calibrated_score,
                "calibration": confidence_result.level,
                "sources": [
                    {
                        "chunk_id": g.chunk.chunk_id,
                        "source": g.chunk.source,
                        "confidence": g.confidence,
                        "reason": g.reason,
                        "excerpt": g.chunk.text[:240],
                    }
                    for g in retrieval.grounding.grounded
                ],
                "token_saliency": [{"token": t.token, "importance": t.importance} for t in exp.token_saliency],
                "alternate_paths": exp.alternate_paths,
                "explanation_latency_ms": exp.latency_ms,
            }

        latency_ms = (time.perf_counter() - start) * 1000
        QUERY_LATENCY.observe(latency_ms)
        QUERY_COUNT.labels(tier=reasoning.response.tier_used, status="ok").inc()

        return OrchestrationResult(
            response_text=reasoning.response.text,
            confidence=confidence_result.calibrated_score,
            calibration=confidence_result.level,
            tier_used=reasoning.response.tier_used,
            degradation_strategy=strategy,
            retrieval=retrieval,
            reasoning=reasoning,
            explanation=explanation,
            validation_warnings=warnings,
            latency_ms=round(latency_ms, 3),
        )
    except Exception:
        QUERY_COUNT.labels(tier="unknown", status="error").inc()
        raise
    finally:
        ACTIVE_QUERIES.dec()
