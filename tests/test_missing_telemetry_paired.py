"""Deterministic checks for the paired synthetic evaluation protocol."""
from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from evaluate_missing_telemetry_paired import audit
from evaluate_missing_telemetry import decide_partial
from unittest.mock import patch
import evaluate_missing_telemetry_paired as paired


class PairedAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "fixture.csv"
        self.rows = [
            ("healthy", 1, .96, .95, .93, .91, .98, .94, .02, .03),
            ("stale", 0, .94, .85, .88, .83, .92, .1, .10, .4),
            ("malware", 0, .92, .85, .9, .9, .95, .85, .98, .9),
            ("adversarial_compliant", 0, .98, .70, .5, .95, .9, .9, .75, .9),
            ("healthy", 1, .92, .9, .94, .88, .9, .92, .03, .02),
        ]
        with self.path.open("w", newline="", encoding="utf-8") as handle:
            w = csv.writer(handle)
            w.writerow(("scenario", "safe_for_ordinary_access", "compliance", "endpoint_health", "identity_assurance", "patch_posture", "security_coverage", "freshness", "threat_risk", "anomaly_risk"))
            w.writerows(self.rows)

    def test_deterministic_repeated_runs(self):
        a = audit(self.path, missing_rate=.25, structured=False)
        b = audit(self.path, missing_rate=.25, structured=False)
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))

    def test_mask_generated_once_per_row_for_all_policies(self):
        observed_masks = []
        original = paired.mask_signals
        def spy(signals, rng, rate, *, structured):
            masked = original(signals, rng, rate, structured=structured)
            observed_masks.append(tuple(sorted(masked)))
            return masked
        with patch.object(paired, "mask_signals", side_effect=spy):
            audit(self.path, missing_rate=.25, structured=False)
        self.assertEqual(len(observed_masks), len(self.rows))

    def test_equivalent_strategies_have_identical_metrics(self):
        for structured in (False, True):
            for rate in (0, .1, .25, .4, 1):
                result = audit(self.path, missing_rate=rate, structured=structured)
                a = result["strategies"]["pessimistic"]
                b = result["strategies"]["confidence"]
                self.assertEqual(a, b)

    def test_zero_missing_has_zero_masked_fraction(self):
        result = audit(self.path, missing_rate=0, structured=False)
        self.assertEqual(result["observed_missing_fraction"], 0)
        self.assertEqual(result["input_rows"], 5)
        self.assertEqual(result["safe_rows"], 2)
        self.assertEqual(result["unsafe_rows"], 3)

    def test_full_missing_abstains_all(self):
        result = audit(self.path, missing_rate=1, structured=False)
        for strategy in result["strategies"].values():
            self.assertEqual(strategy["decision_counts"]["STEP_UP"], 5)

    def test_counts_are_valid(self):
        result = audit(self.path, missing_rate=.25, structured=True)
        for strategy in result["strategies"].values():
            self.assertEqual(sum(strategy["decision_counts"].values()), 5)
            self.assertLessEqual(strategy["false_allow_count"], 3)
            self.assertLessEqual(strategy["safe_step_up_count"], 2)

    def test_invalid_missing_rate_rejected(self):
        for rate in (-.01, 1.01, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                audit(self.path, missing_rate=rate, structured=False)

    def test_nonfinite_input_rejected_before_masking(self):
        self.rows[0] = ("healthy", 1, float("nan"), .95, .93, .91, .98, .94, .02, .03)
        with self.path.open("w", newline="", encoding="utf-8") as handle:
            w = csv.writer(handle)
            w.writerow(("scenario", "safe_for_ordinary_access", "compliance", "endpoint_health", "identity_assurance", "patch_posture", "security_coverage", "freshness", "threat_risk", "anomaly_risk"))
            w.writerows(self.rows)
        with self.assertRaisesRegex(ValueError, "Invalid synthetic input"):
            audit(self.path, missing_rate=1, structured=False)

    def test_empty_or_single_label_rejected(self):
        self.path.write_text("scenario,safe_for_ordinary_access,compliance,endpoint_health,identity_assurance,patch_posture,security_coverage,freshness,threat_risk,anomaly_risk\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "at least one safe"):
            audit(self.path, missing_rate=.25, structured=False)

    def test_algebraic_equivalence_for_partial_signal(self):
        signal = {"compliance": .9, "endpoint_health": .4, "identity_assurance": .7}
        score_a, decision_a, _ = decide_partial(signal, "confidence")
        score_b, decision_b, _ = decide_partial(signal, "pessimistic")
        self.assertAlmostEqual(score_a, score_b)
        self.assertEqual(decision_a, decision_b)


if __name__ == "__main__":
    unittest.main()
