import random
import pytest

from evaluate_within_scenario_shift import SHIFTS, evaluate_shift, shifted_signals


def test_shifted_signals_are_clipped():
    signals = shifted_signals(random.Random(1), "healthy", {"identity_assurance": -2.0, "anomaly_risk": 2.0})
    assert all(0.0 <= value <= 1.0 for value in signals.values())
    assert signals["identity_assurance"] == 0.0
    assert signals["anomaly_risk"] == 1.0


def test_unknown_signal_rejected():
    with pytest.raises(ValueError):
        evaluate_shift({"not_a_signal": 0.1}, rows=10)


def test_evaluation_is_deterministic():
    first = evaluate_shift(SHIFTS["mixed_adverse"], rows=500, seed=42)
    second = evaluate_shift(SHIFTS["mixed_adverse"], rows=500, seed=42)
    assert first == second


def test_metrics_are_rates():
    result = evaluate_shift({}, rows=500, seed=42)
    for metrics in result.values():
        assert 0.0 <= metrics["false_allow_rate"] <= 1.0
        assert 0.0 <= metrics["safe_step_up_rate"] <= 1.0
