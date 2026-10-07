"""AQR: Adaptive Quantization Router — query complexity scoring -> tier selection.

Spec's tiers (Q4/Q5/Q8/Cloud) are remapped onto tiers this environment can
actually serve without multi-GB local GGUF downloads:
  fast   ~ Q4  simple factual   -> extractive, no LLM call
  haiku  ~ Q5  analytical       -> Claude Haiku (if API key configured)
  sonnet ~ Q8  complex reasoning -> Claude Sonnet (if API key configured)
"""

import re
from dataclasses import dataclass

REASONING_INDICATORS = re.compile(
    r"\b(why|how|analyze|analyse|compare|explain|evaluate|justify|trade-?off|implication)\b",
    re.IGNORECASE,
)
DOMAIN_TERMS = re.compile(
    r"\b(pressure|psi|well|casing|wellhead|drilling|reservoir|flowline|choke|"
    r"blowout|corrosion|valve|pipeline|compressor|turbine|manifold)\b",
    re.IGNORECASE,
)


@dataclass
class ComplexityScore:
    score: float
    tier: str
    breakdown: dict[str, float]


def _historical_accuracy_factor(tier_stats: dict[str, float] | None) -> float:
    if not tier_stats:
        return 0.5
    return tier_stats.get("accuracy", 0.5)


def score_complexity(
    query: str, context_size: int = 0, tier_stats: dict[str, float] | None = None
) -> ComplexityScore:
    reasoning_hits = len(REASONING_INDICATORS.findall(query))
    reasoning_component = min(reasoning_hits / 2.0, 1.0)

    domain_hits = len(DOMAIN_TERMS.findall(query))
    domain_component = min(domain_hits / 3.0, 1.0)

    length_component = min(len(query) / 240.0, 1.0)
    context_component = min(context_size / 2000.0, 1.0)
    historical_component = _historical_accuracy_factor(tier_stats)

    score = (
        reasoning_component * 0.35
        + domain_component * 0.25
        + length_component * 0.15
        + context_component * 0.15
        + historical_component * 0.10
    )

    if score < 0.3:
        tier = "fast"
    elif score < 0.6:
        tier = "haiku"
    else:
        tier = "sonnet"

    return ComplexityScore(
        score=round(score, 4),
        tier=tier,
        breakdown={
            "reasoning_indicators": round(reasoning_component, 3),
            "domain_complexity": round(domain_component, 3),
            "query_length": round(length_component, 3),
            "context_density": round(context_component, 3),
            "historical_accuracy": round(historical_component, 3),
        },
    )


def downgrade_tier(tier: str) -> str:
    """DAS 'simplify' degradation path: drop to a cheaper tier under load."""
    order = ["sonnet", "haiku", "fast"]
    idx = order.index(tier) if tier in order else len(order) - 1
    return order[min(idx + 1, len(order) - 1)]
