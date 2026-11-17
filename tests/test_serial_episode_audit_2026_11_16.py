import importlib.util
import pathlib
import unittest

P = pathlib.Path(__file__).resolve().parents[1] / "experiments" / "serial_episode_audit_2026_11_16.py"
spec = importlib.util.spec_from_file_location("serial_episode_audit", P)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class SerialEpisodeAuditTests(unittest.TestCase):
    def test_independent_vif(self):
        self.assertAlmostEqual(mod.variance_inflation(10, 0), 1)
    def test_positive_dependence_increases_variance(self):
        self.assertLess(mod.variance_inflation(10, .3), mod.variance_inflation(10, .6))
    def test_independent_normal_coverage(self):
        self.assertAlmostEqual(mod.normal_reference_coverage(10, 0), .9500042097, places=6)
    def test_positive_dependence_reduces_coverage(self):
        self.assertLess(mod.normal_reference_coverage(10, .6), .95)
    def test_invalid_phi(self):
        for phi in (-1, 1, float("nan")):
            with self.assertRaises(ValueError): mod.variance_inflation(10, phi)
    def test_invalid_episode_count(self):
        with self.assertRaises(ValueError): mod.variance_inflation(1, .2)

if __name__ == "__main__": unittest.main()
