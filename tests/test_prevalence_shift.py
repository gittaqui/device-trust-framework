import pytest
from evaluate_prevalence_shift import MIXES, evaluate_mix


def test_all_mixes_sum_to_one():
    for mix in MIXES.values():
        assert sum(mix.values()) == pytest.approx(1.0)


def test_evaluation_is_deterministic():
    first = evaluate_mix(MIXES["baseline"], rows=2_000, seed=7)
    second = evaluate_mix(MIXES["baseline"], rows=2_000, seed=7)
    assert first == second


def test_identity_heavy_exposes_additive_compensation():
    result = evaluate_mix(MIXES["identity_heavy"], rows=10_000, seed=20260915)
    assert result["guarded_075"]["false_allow_rate"] < result["additive_075"]["false_allow_rate"]


def test_quorum_does_not_reduce_security_by_allowing_more_unsafe_rows():
    for mix in MIXES.values():
        result = evaluate_mix(mix, rows=5_000, seed=20260915)
        assert result["quorum_070_7of8"]["false_allow_rate"] <= result["guarded_075"]["false_allow_rate"]
