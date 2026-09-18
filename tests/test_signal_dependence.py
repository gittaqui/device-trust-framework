import random

import pytest

from generate_synthetic_data import SCENARIOS
from evaluate_signal_dependence import correlated_signals, evaluate_dependence


def test_correlated_signals_stay_inside_scenario_ranges():
    rng = random.Random(7)
    for scenario in SCENARIOS:
        for _ in range(100):
            signals = correlated_signals(rng, scenario, 0.8)
            for signal, value in signals.items():
                low, high = SCENARIOS[scenario]["ranges"][signal]
                assert low <= value <= high


def test_invalid_rho_is_rejected():
    rng = random.Random(7)
    with pytest.raises(ValueError):
        correlated_signals(rng, "healthy", -0.01)
    with pytest.raises(ValueError):
        correlated_signals(rng, "healthy", 1.0)


def test_evaluation_is_reproducible():
    first = evaluate_dependence(0.6, rows=1_000, seed=99)
    second = evaluate_dependence(0.6, rows=1_000, seed=99)
    assert first == second


def test_evaluation_returns_bounded_rates():
    result = evaluate_dependence(0.3, rows=1_000, seed=11)
    assert set(result) == {"additive_075", "guarded_075", "quorum_070_7of8"}
    for metrics in result.values():
        assert 0.0 <= metrics["false_allow_rate"] <= 1.0
        assert 0.0 <= metrics["safe_step_up_rate"] <= 1.0
