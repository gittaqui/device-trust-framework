import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from evaluate_identity_noncompensation import (
    apply_identity_guard,
    policy_surface,
    representative_healthy_context,
    summarize_surface,
)
from trust_model import calculate_trust


class IdentityNonCompensationTests(unittest.TestCase):
    def test_additive_compensation_exists(self):
        signals = representative_healthy_context()
        signals["identity_assurance"] = 0.20
        signals["anomaly_risk"] = 0.90

        decision = calculate_trust(signals, allow_threshold=0.75)

        self.assertEqual(decision.decision, "ALLOW")

    def test_guard_abstains_on_weak_identity_and_high_anomaly(self):
        signals = representative_healthy_context()
        signals["identity_assurance"] = 0.20
        signals["anomaly_risk"] = 0.90

        decision, reason = apply_identity_guard(signals)

        self.assertEqual(decision, "STEP_UP")
        self.assertEqual(reason, "identity_behavior_guard")

    def test_existing_hard_deny_is_preserved(self):
        signals = representative_healthy_context()
        signals["threat_risk"] = 0.95

        decision, reason = apply_identity_guard(signals)

        self.assertEqual(decision, "DENY")
        self.assertEqual(reason, "critical_threat_risk")

    def test_policy_surface_counts_are_reproducible(self):
        summary = summarize_surface(policy_surface())

        self.assertEqual(summary["points"], 441)
        self.assertEqual(summary["additive_075_allow"], 417)
        self.assertEqual(summary["additive_080_allow"], 303)
        self.assertEqual(summary["guarded_075_allow"], 208)


if __name__ == "__main__":
    unittest.main()
