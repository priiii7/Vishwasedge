from backend.trust.confidence import calibration_level, compute_confidence, platt_scale


def test_calibration_levels():
    assert calibration_level(0.9) == "high"
    assert calibration_level(0.7) == "medium"
    assert calibration_level(0.3) == "low"


def test_platt_scale_monotonic():
    assert platt_scale(0.9) > platt_scale(0.1)


def test_compute_confidence_high_when_both_signals_strong():
    result = compute_confidence(retrieval_quality=0.95, model_raw_confidence=0.9)
    assert result.level in {"high", "medium"}
    assert 0.0 <= result.calibrated_score <= 1.0


def test_compute_confidence_low_when_both_signals_weak():
    result = compute_confidence(retrieval_quality=0.05, model_raw_confidence=0.1)
    assert result.calibrated_score < 0.5
