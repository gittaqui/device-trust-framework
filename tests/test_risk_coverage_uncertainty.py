import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from evaluate_risk_coverage_uncertainty import evaluate_uncertainty, wilson_interval


def test_wilson_zero_events_has_nonzero_upper_bound():
    low, high = wilson_interval(0, 1000)
    assert low == 0.0
    assert high > 0.0


def test_wilson_contains_observed_proportion():
    low, high = wilson_interval(72, 25_162)
    observed = 72 / 25_162
    assert low < observed < high


def test_uncertainty_is_deterministic():
    first = evaluate_uncertainty(rows=1000, seed=7, thresholds=(0.75, 0.80))
    second = evaluate_uncertainty(rows=1000, seed=7, thresholds=(0.75, 0.80))
    assert first == second


def test_higher_threshold_reduces_or_preserves_coverage():
    results = evaluate_uncertainty(rows=2000, seed=11, thresholds=(0.70, 0.75, 0.80))
    coverage = [row["ordinary_access_coverage"] for row in results]
    assert coverage == sorted(coverage, reverse=True)
