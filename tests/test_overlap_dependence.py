import random

import pytest

from evaluate_overlap_dependence import evaluate_overlap_dependence, overlap_signals, pooled_ranges
from generate_synthetic_data import SCENARIOS


def test_pooled_ranges_cover_every_scenario():
    pooled = pooled_ranges()
    for spec in SCENARIOS.values():
        for signal, (low, high) in spec["ranges"].items():
            assert pooled[signal][0] <= low <= high <= pooled[signal][1]


def test_overlap_zero_preserves_scenario_bounds():
    values = overlap_signals(random.Random(7), "healthy", rho=0.6, overlap=0.0)
    for signal, value in values.items():
        low, high = SCENARIOS["healthy"]["ranges"][signal]
        assert low <= value <= high


def test_invalid_overlap_rejected():
    with pytest.raises(ValueError):
        overlap_signals(random.Random(1), "healthy", rho=0.0, overlap=1.01)


def test_evaluation_is_reproducible():
    first = evaluate_overlap_dependence(0.6, 0.5, rows=1000, seed=123)
    second = evaluate_overlap_dependence(0.6, 0.5, rows=1000, seed=123)
    assert first == second
    assert 0.0 <= first["unsafe_allow_risk"] <= 1.0
    assert 0.0 <= first["safe_session_allow_recall"] <= 1.0
