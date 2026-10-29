"""Coverage-reporting invariants for partially observed trust decisions.

The tested policies are research-only. These tests do not assert field validity.
"""
from __future__ import annotations

import itertools
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from evaluate_missing_telemetry import SIGNAL_TO_FACTOR, STRATEGY_IDS, decide_partial
from trust_model import DEFAULT_WEIGHTS


class PartialTelemetryCoverageTests(unittest.TestCase):
    def setUp(self):
        self.healthy = {
            "compliance": .98,
            "endpoint_health": .95,
            "identity_assurance": .92,
            "patch_posture": .93,
            "security_coverage": .97,
            "freshness": .94,
            "threat_risk": .02,
            "anomaly_risk": .04,
        }

    def assert_all_strategies_report(self, signals, expected_decision, expected_coverage):
        for strategy in STRATEGY_IDS:
            with self.subTest(strategy=strategy, observed=sorted(signals)):
                score, decision, coverage = decide_partial(signals, strategy)
                self.assertEqual(decision, expected_decision)
                self.assertEqual(score, 0.0)
                self.assertAlmostEqual(coverage, expected_coverage, places=12)

    def test_threat_hard_gate_with_one_observed_signal(self):
        self.assert_all_strategies_report({"threat_risk": .95}, "DENY", .08)

    def test_security_hard_gate_with_one_observed_signal(self):
        self.assert_all_strategies_report({"security_coverage": .10}, "DENY", .16)

    def test_both_hard_gates_with_partial_observation(self):
        self.assert_all_strategies_report(
            {"threat_risk": .95, "security_coverage": .10}, "DENY", .24
        )

    def test_complete_observation_with_hard_gate_reports_full_coverage(self):
        signals = dict(self.healthy, threat_risk=.95)
        self.assert_all_strategies_report(signals, "DENY", 1.0)

    def test_every_mask_reports_exact_observed_weight(self):
        # Exhaustive 2^8 masks, with each of the two hard-gate conditions
        # independently active, across all five policies.
        for gated_signal, gated_value in (("threat_risk", .95), ("security_coverage", .10)):
            full = dict(self.healthy, **{gated_signal: gated_value})
            names = tuple(full)
            for bits in itertools.product((False, True), repeat=len(names)):
                masked = {name: full[name] for name, present in zip(names, bits) if present}
                expected = math.fsum(DEFAULT_WEIGHTS[SIGNAL_TO_FACTOR[name]] for name in masked)
                for strategy in STRATEGY_IDS:
                    with self.subTest(gate=gated_signal, strategy=strategy, mask=bits):
                        score, decision, coverage = decide_partial(masked, strategy)
                        self.assertAlmostEqual(coverage, expected, places=12)
                        self.assertGreaterEqual(coverage, 0)
                        self.assertLessEqual(coverage, 1.0 + 1e-12)
                        if gated_signal in masked:
                            self.assertEqual((score, decision), (0.0, "DENY"))

    def test_missing_all_signals_remains_step_up_with_zero_coverage(self):
        for strategy in STRATEGY_IDS:
            self.assertEqual(decide_partial({}, strategy), (0.0, "STEP_UP", 0.0))


if __name__ == "__main__":
    unittest.main()
