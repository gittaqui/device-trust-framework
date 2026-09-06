import csv
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from evaluate_threshold_sensitivity import evaluate_threshold


FIELDNAMES = [
    "id",
    "scenario",
    "safe_for_ordinary_access",
    "compliance",
    "endpoint_health",
    "identity_assurance",
    "patch_posture",
    "security_coverage",
    "freshness",
    "threat_risk",
    "anomaly_risk",
]


class ThresholdSensitivityTests(unittest.TestCase):
    def _write_rows(self, rows):
        handle = tempfile.NamedTemporaryFile(
            mode="w", newline="", suffix=".csv", delete=False, encoding="utf-8"
        )
        with handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
            writer.writeheader()
            writer.writerows(rows)
        return Path(handle.name)

    def test_higher_allow_threshold_does_not_increase_false_allows(self):
        rows = [
            {
                "id": 1,
                "scenario": "unsafe_high_score",
                "safe_for_ordinary_access": 0,
                "compliance": 0.95,
                "endpoint_health": 0.70,
                "identity_assurance": 0.55,
                "patch_posture": 0.95,
                "security_coverage": 0.95,
                "freshness": 0.95,
                "threat_risk": 0.60,
                "anomaly_risk": 0.75,
            },
            {
                "id": 2,
                "scenario": "healthy",
                "safe_for_ordinary_access": 1,
                "compliance": 0.98,
                "endpoint_health": 0.98,
                "identity_assurance": 0.98,
                "patch_posture": 0.98,
                "security_coverage": 0.98,
                "freshness": 0.98,
                "threat_risk": 0.02,
                "anomaly_risk": 0.02,
            },
        ]
        path = self._write_rows(rows)
        try:
            low, _ = evaluate_threshold(path, allow_threshold=0.70)
            high, _ = evaluate_threshold(path, allow_threshold=0.85)
            self.assertLessEqual(
                high["false_allow_rate"], low["false_allow_rate"]
            )
        finally:
            path.unlink(missing_ok=True)

    def test_per_scenario_rates_sum_to_one(self):
        rows = [
            {
                "id": 1,
                "scenario": "healthy",
                "safe_for_ordinary_access": 1,
                "compliance": 0.98,
                "endpoint_health": 0.98,
                "identity_assurance": 0.98,
                "patch_posture": 0.98,
                "security_coverage": 0.98,
                "freshness": 0.98,
                "threat_risk": 0.02,
                "anomaly_risk": 0.02,
            }
        ]
        path = self._write_rows(rows)
        try:
            _, scenarios = evaluate_threshold(path, allow_threshold=0.75)
            metrics = scenarios["healthy"]
            total = (
                metrics["allow_rate"]
                + metrics["step_up_rate"]
                + metrics["deny_rate"]
            )
            self.assertAlmostEqual(total, 1.0)
        finally:
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
