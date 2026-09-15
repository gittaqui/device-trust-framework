from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from evaluate_signal_ablation import SIGNALS, ablated_weights, evaluate_rows


def _row(safe="0"):
    return {
        "scenario": "test", "safe_for_ordinary_access": safe,
        "compliance": "0.95", "endpoint_health": "0.90",
        "identity_assurance": "0.90", "patch_posture": "0.90",
        "security_coverage": "0.95", "freshness": "0.90",
        "threat_risk": "0.05", "anomaly_risk": "0.05",
    }


def test_each_ablation_removes_exactly_one_factor():
    for factor in SIGNALS:
        weights = ablated_weights(factor)
        assert factor not in weights
        assert len(weights) == len(SIGNALS) - 1


def test_unknown_factor_rejected():
    try:
        ablated_weights("not_a_factor")
    except ValueError:
        pass
    else:
        raise AssertionError("unknown factor should raise ValueError")


def test_metrics_are_bounded():
    result = evaluate_rows([_row("0"), _row("1")])
    assert 0.0 <= result["false_allow_rate"] <= 1.0
    assert 0.0 <= result["safe_step_up_rate"] <= 1.0
    assert 0.0 <= result["safe_deny_rate"] <= 1.0
