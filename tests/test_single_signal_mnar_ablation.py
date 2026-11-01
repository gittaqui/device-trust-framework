"""Deterministic checks for paired, calibrated single-signal MNAR ablations."""
import math
import random
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from evaluate_single_signal_mnar_ablation import (
    ARMS, calibrate_probe_intercepts, evaluate, masks_for_arms, run_seed,
)
from evaluate_value_dependent_missingness import (
    POLICIES, SIGNALS, PROBE_SIGNALS, calibrate, load_rows, risk_value, run_seed as old_run_seed, sigmoid,
)
from generate_synthetic_data import generate


class SingleSignalAblationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.path = Path(cls.temp.name) / "synthetic.csv"
        generate(450, cls.path, seed=20260903)
        cls.rows = load_rows(cls.path)
        cls.alpha = calibrate_probe_intercepts(cls.rows, rate=.25, beta=4.)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_expected_missing_rate_calibrated_for_each_column(self):
        for name in SIGNALS:
            expected = sum(sigmoid(self.alpha[name] + 4 * (risk_value(name, signals[name]) - .5))
                           for _, _, signals in self.rows) / len(self.rows)
            self.assertAlmostEqual(expected, .25, delta=1e-9)

    def test_only_target_signal_mask_differs_from_mcar(self):
        _, _, signals = self.rows[0]
        for i in range(100):
            rng = random.Random(i)
            u = {name: rng.random() for name in SIGNALS}
            masks = masks_for_arms(signals, u, rate=.25, beta=4., intercepts=self.alpha)
            self.assertEqual(set(masks), set(ARMS))
            for target in PROBE_SIGNALS:
                for name in SIGNALS:
                    if name != target:
                        self.assertEqual(name in masks[target], name in masks["mcar"])

    def test_old_baseline_and_all_eight_match_exactly(self):
        # Locks in pairing and old implementation compatibility, not just aggregate rates.
        old_alpha = calibrate(self.rows, .25, (0., 4.))
        old = old_run_seed(self.rows, seed=17, intercepts=old_alpha)
        new = run_seed(self.rows, seed=17, rate=.25, beta=4., intercepts=self.alpha)
        for arm, beta in (("mcar", 0.), ("all_eight", 4.)):
            self.assertAlmostEqual(new["arms"][arm]["missing_fraction"], old[beta]["observed_missing_fraction"])
            for name in SIGNALS:
                self.assertAlmostEqual(new["arms"][arm]["missing_by_signal"][name], old[beta]["missing_by_signal"][name])
            for policy in POLICIES:
                for key in ("unsafe_allow_count", "safe_deny_count", "safe_step_up_count", "safe_allow_count"):
                    self.assertEqual(new["arms"][arm]["policies"][policy][key], old[beta]["policies"][policy][key])

    def test_counts_and_paired_flips_reconcile(self):
        out = run_seed(self.rows, seed=13, rate=.25, beta=4., intercepts=self.alpha)
        for arm in ARMS:
            for policy in POLICIES:
                p = out["arms"][arm]["policies"][policy]
                self.assertEqual(sum(p["decisions"].values()), len(self.rows))
                self.assertEqual(p["safe_allow_count"] + p["safe_deny_count"] + p["safe_step_up_count"], out["safe_rows"])
                self.assertEqual(sum(x["allow_count"] for x in p["unsafe_allow_by_scenario"].values()), p["unsafe_allow_count"])
                if arm != "mcar":
                    f = p["paired_allow_flips_vs_mcar"]
                    base = out["arms"]["mcar"]["policies"][policy]
                    self.assertEqual(p["unsafe_allow_count"] - base["unsafe_allow_count"], f["unsafe_not_to_allow"] - f["unsafe_allow_to_not"])
                    self.assertEqual(p["safe_allow_count"] - base["safe_allow_count"], f["safe_not_to_allow"] - f["safe_allow_to_not"])

    def test_non_target_expected_missingness_is_mcar(self):
        for target in PROBE_SIGNALS:
            _, _, signals = self.rows[0]
            for name in SIGNALS:
                if name != target:
                    for u in (0., .24, .25, .26, .99):
                        uniforms = {n: u for n in SIGNALS}
                        masks = masks_for_arms(signals, uniforms, rate=.25, beta=4., intercepts=self.alpha)
                        self.assertEqual(name in masks[target], name in masks["mcar"])

    def test_reproducible(self):
        a = evaluate(self.path, seeds=(17, 18))
        b = evaluate(self.path, seeds=(17, 18))
        self.assertEqual(a, b)

    def test_invalid_arguments(self):
        with self.assertRaises(ValueError):
            calibrate_probe_intercepts(self.rows, rate=.25, beta=0)
        with self.assertRaises(ValueError):
            evaluate(self.path, seeds=(17, 17))
        with self.assertRaises(ValueError):
            evaluate(self.path, seeds=())
        _, _, signals = self.rows[0]
        with self.assertRaises(ValueError):
            masks_for_arms(signals, {name: .25 for name in SIGNALS}, rate=0, beta=4, intercepts=self.alpha)
        with self.assertRaises(ValueError):
            masks_for_arms(signals, {name: float('nan') for name in SIGNALS}, rate=.25, beta=4, intercepts=self.alpha)


if __name__ == "__main__":
    unittest.main()
