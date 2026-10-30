"""Deterministic synthetic coverage-stratification invariants."""
from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import audit_missingness_by_coverage as coverage
from evaluate_missing_telemetry_paired import audit as paired_audit


class CoverageStrataTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "fixture.csv"
        self.rows = [
            ("healthy", 1, .96, .95, .93, .91, .98, .94, .02, .03),
            ("policy_drift", 1, .15, .95, .93, .91, .98, .94, .02, .03),
            ("malware", 0, .92, .85, .9, .9, .95, .85, .98, .9),
            ("protection_missing", 0, .92, .85, .9, .9, .10, .85, .20, .5),
            ("adversarial_compliant", 0, .98, .70, .5, .95, .9, .9, .75, .9),
        ]
        with self.path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(("scenario", "safe_for_ordinary_access", "compliance", "endpoint_health", "identity_assurance", "patch_posture", "security_coverage", "freshness", "threat_risk", "anomaly_risk"))
            writer.writerows(self.rows)

    def test_repeated_runs_are_identical(self):
        a = coverage.audit_strata(self.path, missing_rate=.25)
        b = coverage.audit_strata(self.path, missing_rate=.25)
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))

    def test_one_mask_per_observation(self):
        original = coverage.mask_signals
        calls = []
        def spy(*args, **kwargs):
            calls.append(1)
            return original(*args, **kwargs)
        with patch.object(coverage, "mask_signals", side_effect=spy):
            coverage.audit_strata(self.path)
        self.assertEqual(len(calls), len(self.rows))

    def test_aggregate_counts_exactly_match_frozen_paired_audit(self):
        for structured in (False, True):
            for rate in (0, .25, .75, 1):
                strata = coverage.audit_strata(self.path, structured=structured, missing_rate=rate)
                paired = paired_audit(self.path, structured=structured, missing_rate=rate)
                overall = strata["groups"]["overall"]["all"]
                self.assertEqual(overall["rows"], paired["input_rows"])
                self.assertAlmostEqual(strata["observed_missing_fraction"], paired["observed_missing_fraction"])
                for strategy, counts in overall["strategies"].items():
                    original = paired["strategies"][strategy]
                    self.assertEqual(counts["false_allow"], original["false_allow_count"])
                    self.assertEqual(counts["false_deny"], original["false_deny_count"])
                    self.assertEqual(counts["safe_step_up"], original["safe_step_up_count"])
                    for d in ("ALLOW", "DENY", "STEP_UP"):
                        self.assertEqual(counts[d.lower()], original["decision_counts"][d])

    def test_all_coverage_bins_partition_rows(self):
        for rate in (0, .25, 1):
            result = coverage.audit_strata(self.path, missing_rate=rate)
            by_bin = result["groups"]["by_coverage"]
            self.assertEqual(sum(v["rows"] for v in by_bin.values()), len(self.rows))
            self.assertEqual(set(by_bin).difference(coverage.COVERAGE_BINS), set())
        zero = coverage.audit_strata(self.path, missing_rate=0)
        self.assertEqual(zero["groups"]["by_coverage"]["1.00"]["rows"], len(self.rows))
        full = coverage.audit_strata(self.path, missing_rate=1, structured=False)
        self.assertEqual(full["groups"]["by_coverage"]["[0,0.50)"]["rows"], len(self.rows))

    def test_gate_presence_exposes_observed_and_missing(self):
        result = coverage.audit_strata(self.path, missing_rate=0)
        gate = result["groups"]["by_gate_presence"]
        for scenario in ("malware", "protection_missing"):
            self.assertEqual(gate[f"{scenario}|observed"]["rows"], 1)
            for strategy in coverage.STRATEGIES:
                self.assertEqual(gate[f"{scenario}|observed"]["strategies"][strategy]["deny"], 1)
        full = coverage.audit_strata(self.path, missing_rate=1, structured=False)
        gate = full["groups"]["by_gate_presence"]
        for scenario in ("malware", "protection_missing"):
            self.assertEqual(gate[f"{scenario}|missing"]["rows"], 1)

    def test_absent_class_has_null_rate_not_zero(self):
        result = coverage.audit_strata(self.path, missing_rate=0)
        safe_only = result["groups"]["by_scenario"]["healthy"]
        unsafe_only = result["groups"]["by_scenario"]["malware"]
        self.assertIsNone(safe_only["strategies"]["renormalize"]["false_allow_rate_unsafe"])
        self.assertIsNone(unsafe_only["strategies"]["renormalize"]["false_deny_rate_safe"])

    def test_coverage_boundary(self):
        self.assertEqual(coverage.coverage_bin(0), "[0,0.50)")
        self.assertEqual(coverage.coverage_bin(.5), "[0.50,0.75)")
        self.assertEqual(coverage.coverage_bin(.75), "[0.75,1)")
        self.assertEqual(coverage.coverage_bin(1), "1.00")
        for value in (-.1, 1.1, float("nan")):
            with self.assertRaises(ValueError):
                coverage.coverage_bin(value)

    def test_frozen_50000_row_evidence_reconciles(self):
        from generate_synthetic_data import generate
        repo = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "synthetic.csv"
            generate(50_000, path, seed=20260903)
            for structured, regime in ((False, "mcar"), (True, "critical_signal_biased")):
                strata = coverage.audit_strata(path, structured=structured, missing_rate=.25, seed=20260904)
                frozen = json.loads((repo / "results" / f"paired_missing_telemetry_{regime}.json").read_text())
                overall = strata["groups"]["overall"]["all"]
                self.assertEqual(overall["rows"], frozen["input_rows"])
                self.assertEqual(overall["safe"], frozen["safe_rows"])
                self.assertEqual(overall["unsafe"], frozen["unsafe_rows"])
                self.assertEqual(strata["observed_missing_fraction"], frozen["observed_missing_fraction"])
                for strategy, metrics in frozen["strategies"].items():
                    new = overall["strategies"][strategy]
                    self.assertEqual(new["false_allow"], metrics["false_allow_count"])
                    self.assertEqual(new["false_deny"], metrics["false_deny_count"])
                    self.assertEqual(new["safe_step_up"], metrics["safe_step_up_count"])
                    for decision in ("ALLOW", "DENY", "STEP_UP"):
                        self.assertEqual(new[decision.lower()], metrics["decision_counts"][decision])

    def test_invalid_input_rejected(self):
        for rate in (-.01, 1.01, float("nan")):
            with self.assertRaises(ValueError):
                coverage.audit_strata(self.path, missing_rate=rate)


if __name__ == "__main__":
    unittest.main()
