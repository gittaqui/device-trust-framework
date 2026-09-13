"""Tests for the literature-inspired attribute-quorum baseline."""

from evaluate_attribute_quorum import (
    QuorumPolicy,
    quorum_decision,
    safety_factors,
    sweep,
)


HEALTHY = {
    "compliance": 0.95,
    "endpoint_health": 0.92,
    "identity_assurance": 0.93,
    "patch_posture": 0.90,
    "security_coverage": 0.96,
    "freshness": 0.94,
    "threat_risk": 0.05,
    "anomaly_risk": 0.08,
}

IDENTITY_WEAK = {
    **HEALTHY,
    "identity_assurance": 0.30,
    "anomaly_risk": 0.82,
}


def test_safety_factors_invert_risk_inputs():
    factors = safety_factors(HEALTHY)
    assert factors[-2] == 0.95
    assert factors[-1] == 0.92


def test_healthy_row_can_pass_quorum():
    assert quorum_decision(HEALTHY) == "ALLOW"


def test_quorum_blocks_compensation_by_two_weak_factors():
    policy = QuorumPolicy(signal_threshold=0.70, min_passing_signals=7)
    assert quorum_decision(IDENTITY_WEAK, policy=policy) == "STEP_UP"


def test_invalid_quorum_size_is_rejected():
    policy = QuorumPolicy(min_passing_signals=9)
    try:
        quorum_decision(HEALTHY, policy=policy)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected invalid quorum size to raise ValueError.")


def test_seeded_sweep_contains_nine_configurations():
    results = sweep(rows=500, seed=20260903)
    assert len(results) == 9
    assert {(r["signal_threshold"], r["min_passing_signals"]) for r in results} == {
        (q, k) for q in (0.60, 0.70, 0.75) for k in (5, 6, 7)
    }
