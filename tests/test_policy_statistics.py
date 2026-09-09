from __future__ import annotations

from evaluate_policy_statistics import (
    estimate_rate,
    evaluate,
    mcnemar_continuity_corrected,
    wilson_interval,
)


def test_wilson_interval_is_bounded_and_contains_observed_rate() -> None:
    low, high = wilson_interval(50, 100)
    assert 0.0 <= low < 0.5 < high <= 1.0


def test_rate_estimate_preserves_counts() -> None:
    estimate = estimate_rate(25, 100)
    assert estimate.count == 25
    assert estimate.denominator == 100
    assert estimate.rate == 0.25
    assert estimate.ci_low < estimate.rate < estimate.ci_high


def test_mcnemar_counts_paired_disagreements() -> None:
    result = mcnemar_continuity_corrected(
        [True, True, False, False],
        [True, False, True, False],
    )
    assert result.first_only_correct == 1
    assert result.second_only_correct == 1
    assert result.discordant == 2
    assert result.p_value == 1.0


def test_statistical_evaluation_is_reproducible() -> None:
    first = evaluate(rows=2_000, seed=20260903)
    second = evaluate(rows=2_000, seed=20260903)
    assert first == second


def test_guard_reduces_false_allows_vs_additive_075_on_seeded_population() -> None:
    result = evaluate(rows=10_000, seed=20260903)
    metrics = result["metrics"]
    assert metrics["guarded_075"]["false_allow"].rate < metrics["additive_075"]["false_allow"].rate
