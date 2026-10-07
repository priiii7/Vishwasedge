"""Drift detection + anomaly alerts over a rolling window of query confidence."""

from collections import deque
from dataclasses import dataclass
from statistics import mean, pstdev


@dataclass
class DriftReport:
    window_size: int
    mean_confidence: float
    stdev_confidence: float
    anomaly: bool
    message: str


class ConfidenceMonitor:
    def __init__(self, window: int = 50, drift_threshold: float = 0.15):
        self._history: deque[float] = deque(maxlen=window)
        self._baseline_mean: float | None = None
        self._drift_threshold = drift_threshold

    def record(self, confidence: float) -> None:
        self._history.append(confidence)
        if self._baseline_mean is None and len(self._history) == self._history.maxlen:
            self._baseline_mean = mean(self._history)

    def check_drift(self) -> DriftReport:
        if not self._history:
            return DriftReport(0, 0.0, 0.0, False, "no data yet")

        current_mean = mean(self._history)
        current_std = pstdev(self._history) if len(self._history) > 1 else 0.0

        anomaly = False
        message = "stable"
        if self._baseline_mean is not None:
            drift = abs(current_mean - self._baseline_mean)
            if drift > self._drift_threshold:
                anomaly = True
                message = f"confidence drift detected: baseline={self._baseline_mean:.3f} current={current_mean:.3f}"

        return DriftReport(
            window_size=len(self._history),
            mean_confidence=round(current_mean, 4),
            stdev_confidence=round(current_std, 4),
            anomaly=anomaly,
            message=message,
        )


confidence_monitor = ConfidenceMonitor()
