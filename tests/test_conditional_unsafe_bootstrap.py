"""Regression checks for conditional unsafe-device bootstrap."""
import unittest
from src.conditional_unsafe_bootstrap import paired_effect_conditional_unsafe as estimate

class ConditionalUnsafeBootstrapTests(unittest.TestCase):
    def setUp(self):
        self.rows = [
            dict(device_id="a", unsafe=True, intervals=10, arm0_allow_count=2, arm1_allow_count=5),
            dict(device_id="b", unsafe=True, intervals=20, arm0_allow_count=4, arm1_allow_count=10),
            dict(device_id="c", unsafe=False, intervals=10, arm0_allow_count=10, arm1_allow_count=10)]
    def test_point(self):
        self.assertAlmostEqual(estimate(self.rows, 200, 1)["paired_difference"], .3)
    def test_repeatable(self):
        self.assertEqual(estimate(self.rows, 200, 1), estimate(self.rows, 200, 1))
    def test_sparse(self):
        rows = self.rows[:2] + [dict(device_id=str(i), unsafe=False, intervals=10,
                    arm0_allow_count=10, arm1_allow_count=10) for i in range(98)]
        result = estimate(rows, 2000, 3)
        self.assertEqual((result["unsafe_devices"], result["undefined_replicates"]), (2, 0))
        self.assertEqual(result["defined_replicates"], 2000)
    def test_constant(self):
        rows = [dict(device_id=str(i), unsafe=True, intervals=10, arm0_allow_count=2,
                     arm1_allow_count=5) for i in range(5)]
        self.assertTrue(all(abs(x-.3)<1e-12 for x in estimate(rows,100,1)["ci_95_percentile"]))
    def test_duplicate(self):
        with self.assertRaises(ValueError): estimate(self.rows+[self.rows[0]])
    def test_boolean_count(self):
        self.rows[0]["arm0_allow_count"] = True
        with self.assertRaises(ValueError): estimate(self.rows)
    def test_insufficient_unsafe(self):
        self.rows[1]["unsafe"] = False
        with self.assertRaises(ValueError): estimate(self.rows)
    def test_bad_replicates(self):
        with self.assertRaises(ValueError): estimate(self.rows, True)
    def test_bad_intervals(self):
        self.rows[0]["intervals"] = 0
        with self.assertRaises(ValueError): estimate(self.rows)
    def test_safe_records_do_not_change_conditional_effect(self):
        result = estimate(self.rows, 200, 1)
        self.rows[2]["arm0_allow_count"] = 0
        self.assertEqual(result, estimate(self.rows, 200, 1))

if __name__ == "__main__":
    unittest.main()
