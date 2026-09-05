import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from evaluate_missing_telemetry import decide_partial


class MissingTelemetryTests(unittest.TestCase):
    def setUp(self):
        self.healthy = {
            "compliance": 0.95,
            "endpoint_health": 0.95,
            "identity_assurance": 0.95,
            "patch_posture": 0.95,
            "security_coverage": 0.95,
            "freshness": 0.95,
            "threat_risk": 0.05,
            "anomaly_risk": 0.05,
        }

    def test_step_up_when_critical_signal_missing(self):
        partial = dict(self.healthy)
        partial.pop("threat_risk")
        _, decision, _ = decide_partial(partial, "step_up")
        self.assertEqual(decision, "STEP_UP")

    def test_step_up_when_weight_coverage_low(self):
        partial = {
            "compliance": 0.95,
            "endpoint_health": 0.95,
        }
        _, decision, coverage = decide_partial(partial, "step_up")
        self.assertLess(coverage, 0.75)
        self.assertEqual(decision, "STEP_UP")

    def test_observed_critical_threat_still_denies(self):
        partial = dict(self.healthy)
        partial["threat_risk"] = 0.95
        partial.pop("patch_posture")
        _, decision, _ = decide_partial(partial, "renormalize")
        self.assertEqual(decision, "DENY")

    def test_pessimistic_score_not_higher_than_neutral(self):
        partial = dict(self.healthy)
        partial.pop("patch_posture")
        pessimistic, _, _ = decide_partial(partial, "pessimistic")
        neutral, _, _ = decide_partial(partial, "neutral")
        self.assertLessEqual(pessimistic, neutral)


if __name__ == "__main__":
    unittest.main()
