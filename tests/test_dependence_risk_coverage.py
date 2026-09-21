import pytest

from evaluate_dependence_risk_coverage import evaluate_dependence_risk_coverage


def test_rejects_invalid_inputs():
    with pytest.raises(ValueError):
        evaluate_dependence_risk_coverage(-0.1, rows=100)
    with pytest.raises(ValueError):
        evaluate_dependence_risk_coverage(0.2, rows=0)


def test_is_reproducible():
    first = evaluate_dependence_risk_coverage(0.6, rows=500, seed=7, thresholds=(0.75, 0.85))
    second = evaluate_dependence_risk_coverage(0.6, rows=500, seed=7, thresholds=(0.75, 0.85))
    assert first == second


def test_intervals_contain_point_estimates():
    for result in evaluate_dependence_risk_coverage(0.3, rows=1000, seed=9, thresholds=(0.75,)):
        assert result["unsafe_allow_risk_ci_low"] <= result["unsafe_allow_risk"] <= result["unsafe_allow_risk_ci_high"]
        assert result["safe_session_allow_recall_ci_low"] <= result["safe_session_allow_recall"] <= result["safe_session_allow_recall_ci_high"]


def test_higher_dependence_exposes_threshold_085_failures_in_frozen_study():
    baseline = evaluate_dependence_risk_coverage(0.0, rows=50_000, seed=20260920, thresholds=(0.85,))[0]
    stressed = evaluate_dependence_risk_coverage(0.8, rows=50_000, seed=20260920, thresholds=(0.85,))[0]
    assert baseline["unsafe_allowed"] == 0
    assert stressed["unsafe_allowed"] > 0
