"""Regression tests for paired device-level resampling."""
import unittest
from src.longitudinal_cluster_bootstrap import paired_effect


class PairedBootstrapTests(unittest.TestCase):
    def setUp(self):
        self.rows = [
            dict(device_id="a", unsafe=True, intervals=10,
                 arm0_allow_count=2, arm1_allow_count=5),
            dict(device_id="b", unsafe=True, intervals=20,
                 arm0_allow_count=4, arm1_allow_count=10),
            dict(device_id="c", unsafe=False, intervals=10,
                 arm0_allow_count=10, arm1_allow_count=10),
        ]

    def test_point_estimate(self):
        self.assertAlmostEqual(paired_effect(self.rows, 200, 1)["paired_difference"], .3)

    def test_deterministic(self):
        self.assertEqual(paired_effect(self.rows, 200, 1),
                         paired_effect(self.rows, 200, 1))

    def test_constant_effect(self):
        rows = [dict(device_id=str(i), unsafe=True, intervals=10,
                     arm0_allow_count=2, arm1_allow_count=5) for i in range(5)]
        self.assertTrue(all(abs(x - .3) < 1e-12 for x in paired_effect(rows, 100, 1)["ci_95_percentile"]))

    def test_duplicate_rejected(self):
        with self.assertRaises(ValueError):
            paired_effect(self.rows + [self.rows[0]])

    def test_boolean_count_rejected(self):
        self.rows[0]["arm0_allow_count"] = True
        with self.assertRaises(ValueError):
            paired_effect(self.rows)

    def test_insufficient_unsafe_clusters(self):
        self.rows[1]["unsafe"] = False
        with self.assertRaises(ValueError):
            paired_effect(self.rows)


if __name__ == "__main__":
    unittest.main()
