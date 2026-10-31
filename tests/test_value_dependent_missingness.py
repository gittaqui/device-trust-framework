"""Contract tests for synthetic value-dependent dropout sensitivity audit."""
import math
import random
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from evaluate_missing_telemetry import SIGNAL_TO_FACTOR, decide_partial
from evaluate_value_dependent_missingness import (
    POLICIES, STRENGTHS, calibrate, calibrated_intercept, evaluate,
    load_rows, risk_value, run_seed, sigmoid,
)
from generate_synthetic_data import generate


class ValueDependentMissingnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.path = Path(cls.temp.name) / "synthetic.csv"
        generate(350, cls.path, seed=20260903)
        cls.rows = load_rows(cls.path)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_risk_orientation(self):
        self.assertAlmostEqual(risk_value("identity_assurance", .1), .9)
        self.assertAlmostEqual(risk_value("threat_risk", .9), .9)
        self.assertAlmostEqual(risk_value("security_coverage", .9), .1)

    def test_invalid_inputs_rejected(self):
        for value in (float("nan"), float("inf"), -0.1, 1.1):
            with self.assertRaises(ValueError):
                risk_value("identity_assurance", value)
        for rate, beta in ((0, 1), (1, 1), (.25, -1), (.25, float("nan"))):
            with self.assertRaises(ValueError):
                calibrated_intercept([.1, .9], rate, beta)
        with self.assertRaises(ValueError):
            calibrated_intercept([], .25, 2)
        with self.assertRaises(ValueError):
            evaluate(self.path, strengths=(0, 0))
        with self.assertRaises(ValueError):
            evaluate(self.path, seeds=(3, 3))

    def test_calibration_matches_per_column_target(self):
        intercepts = calibrate(self.rows, .25, STRENGTHS)
        for beta in STRENGTHS:
            for signal in SIGNAL_TO_FACTOR:
                expected = sum(sigmoid(intercepts[beta][signal] + beta *
                                       (risk_value(signal, values[signal]) - .5))
                               for _, _, values in self.rows) / len(self.rows)
                self.assertAlmostEqual(expected, .25, delta=1e-9)

    def test_mnar_is_strictly_risk_monotone(self):
        alpha = calibrated_intercept([.1, .9], .25, 4)
        self.assertGreater(sigmoid(alpha + 4 * (.9 - .5)),
                           sigmoid(alpha + 4 * (.1 - .5)))
        alpha0 = calibrated_intercept([.1, .9], .25, 0)
        self.assertAlmostEqual(sigmoid(alpha0), .25)

    def test_paired_mcar_matches_manual_rng_masks(self):
        # The beta=0 arm uses the same uniforms for all signals and policies.
        intercepts = calibrate(self.rows, .25, (0.,))
        got = run_seed(self.rows, seed=17, intercepts=intercepts)[0.]
        rng = random.Random(17)
        expected = {policy: 0 for policy in POLICIES}
        for safe, _, signals in self.rows:
            masked = {name: signals[name] for name in SIGNAL_TO_FACTOR if rng.random() >= .25}
            for policy in POLICIES:
                _, decision, _ = decide_partial(masked, policy)
                expected[policy] += int(not safe and decision == "ALLOW")
        for policy in POLICIES:
            self.assertEqual(got["policies"][policy]["unsafe_allow_count"], expected[policy])

    def test_counts_and_denominators_reconcile(self):
        out = evaluate(self.path, seeds=(11, 12))
        for strength in STRENGTHS:
            for run in out["by_strength"][str(strength)]["seed_results"]:
                self.assertEqual(run["rows"], 350)
                self.assertEqual(run["safe_rows"] + run["unsafe_rows"], 350)
                self.assertEqual(len(run["missing_by_signal"]), 8)
                for policy in POLICIES:
                    p = run["policies"][policy]
                    self.assertEqual(sum(p["decisions"].values()), 350)
                    self.assertEqual(p["safe_allow_count"] + p["safe_step_up_count"] + p["safe_deny_count"], run["safe_rows"])
                    self.assertAlmostEqual(p["unsafe_allow_rate"], p["unsafe_allow_count"] / run["unsafe_rows"])
                    self.assertEqual(sum(s["allow_count"] for s in p["unsafe_allow_by_scenario"].values()), p["unsafe_allow_count"])
                for name in ("identity_assurance", "threat_risk", "security_coverage"):
                    for band in ("high", "low"):
                        c = run["risk_conditioned_missingness"][name][band]
                        self.assertLessEqual(c["missing"], c["n"])

    def test_reproducible_across_repeated_runs(self):
        a = evaluate(self.path, strengths=(0., 4.), seeds=(11,))
        b = evaluate(self.path, strengths=(0., 4.), seeds=(11,))
        self.assertEqual(a, b)

    def test_different_strengths_have_same_expected_marginal_rate(self):
        intercepts = calibrate(self.rows, .25, STRENGTHS)
        for signal in SIGNAL_TO_FACTOR:
            means = []
            for beta in STRENGTHS:
                means.append(sum(sigmoid(intercepts[beta][signal] + beta *
                                         (risk_value(signal, signals[signal]) - .5))
                                 for _, _, signals in self.rows) / len(self.rows))
            self.assertLess(max(means) - min(means), 1e-9)


if __name__ == "__main__":
    unittest.main()
