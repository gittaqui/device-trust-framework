import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from evaluate_frozen_transport import TARGET_CONDITIONS, evaluate_transport


def test_transport_uses_one_frozen_threshold_per_model():
    result = evaluate_transport(600, 300, 600)
    assert 0.5 <= result["trust_threshold"] <= 1.0
    assert 0.0 <= result["learned_threshold"] <= 1.0
    assert len(result["results"]) == len(TARGET_CONDITIONS)


def test_transport_metrics_are_probabilities():
    result = evaluate_transport(600, 300, 600)
    for row in result["results"]:
        for model_name in ("trust", "learned"):
            coverage, unsafe_risk, safe_recall = row[model_name]
            assert 0.0 <= coverage <= 1.0
            assert 0.0 <= unsafe_risk <= 1.0
            assert 0.0 <= safe_recall <= 1.0
