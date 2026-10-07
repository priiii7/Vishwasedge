"""Confidence calibration: Platt-style sigmoid scaling + discrete levels."""

import math
from dataclasses import dataclass

# Platt scaling coefficients (A, B) — in production these are fit via logistic
# regression against a labeled validation set of (raw_score, was_correct) pairs.
# We ship reasonable defaults that produce a well-spread 0-1 curve, and expose
# `fit_platt_scaling` for calibrating against real feedback data later.
DEFAULT_A = -4.0
DEFAULT_B = 2.0


@dataclass
class ConfidenceResult:
    raw_score: float
    calibrated_score: float
    level: str  # high | medium | low


def platt_scale(raw_score: float, a: float = DEFAULT_A, b: float = DEFAULT_B) -> float:
    return 1.0 / (1.0 + math.exp(a * raw_score + b))


def calibration_level(score: float) -> str:
    if score > 0.85:
        return "high"
    if score >= 0.6:
        return "medium"
    return "low"


def compute_confidence(retrieval_quality: float, model_raw_confidence: float) -> ConfidenceResult:
    """Blend retrieval quality (mean rerank score of used docs) with the
    model's own raw confidence signal, then calibrate."""
    blended_raw = 0.6 * retrieval_quality + 0.4 * model_raw_confidence
    calibrated = platt_scale(blended_raw)
    # Platt scaling on our default coefficients biases low; rescale into a
    # usable band anchored at the blended raw score for interpretability.
    calibrated = round(0.5 * calibrated + 0.5 * blended_raw, 4)
    return ConfidenceResult(
        raw_score=round(blended_raw, 4),
        calibrated_score=calibrated,
        level=calibration_level(calibrated),
    )


def fit_platt_scaling(samples: list[tuple[float, bool]]) -> tuple[float, float]:
    """Simple gradient-descent fit of (A, B) for y = sigmoid(A*x + B) against
    labeled (raw_score, was_correct) samples. Returns (A, B)."""
    a, b = DEFAULT_A, DEFAULT_B
    lr = 0.1
    for _ in range(200):
        grad_a = grad_b = 0.0
        for x, label in samples:
            y = 1.0 if label else 0.0
            pred = platt_scale(x, a, b)
            error = pred - y
            grad_a += error * x
            grad_b += error
        n = max(len(samples), 1)
        a -= lr * grad_a / n
        b -= lr * grad_b / n
    return a, b
