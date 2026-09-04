import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from trust_model import binary_compliance_decision, calculate_trust


class TrustModelTests(unittest.TestCase):
    def test_healthy_device_is_allowed(self):
        decision = calculate_trust({
            "compliance": 0.95,
            "endpoint_health": 0.95,
            "identity_assurance": 0.95,
            "patch_posture": 0.95,
            "security_coverage": 0.98,
            "freshness": 0.95,
            "threat_risk": 0.05,
            "anomaly_risk": 0.05,
        })
        self.assertEqual(decision.decision, "ALLOW")

    def test_critical_threat_is_hard_denied(self):
        decision = calculate_trust({
            "compliance": 1.0,
            "endpoint_health": 0.95,
            "identity_assurance": 0.95,
            "patch_posture": 1.0,
            "security_coverage": 1.0,
            "freshness": 1.0,
            "threat_risk": 0.95,
            "anomaly_risk": 0.10,
        })
        self.assertEqual(decision.decision, "DENY")
        self.assertEqual(decision.hard_gate, "critical_threat_risk")

    def test_missing_security_coverage_is_hard_denied(self):
        decision = calculate_trust({
            "compliance": 1.0,
            "endpoint_health": 0.95,
            "identity_assurance": 0.95,
            "patch_posture": 1.0,
            "security_coverage": 0.10,
            "freshness": 1.0,
            "threat_risk": 0.05,
            "anomaly_risk": 0.05,
        })
        self.assertEqual(decision.decision, "DENY")
        self.assertEqual(decision.hard_gate, "critical_security_coverage")

    def test_binary_baseline_only_uses_compliance(self):
        self.assertEqual(binary_compliance_decision(1.0), "ALLOW")
        self.assertEqual(binary_compliance_decision(0.0), "DENY")


if __name__ == "__main__":
    unittest.main()
