import importlib.util
import pathlib
import unittest

FILE = pathlib.Path(__file__).resolve().parents[1] / "experiments" / "episode_interval_audit_2026_11_15.py"
spec = importlib.util.spec_from_file_location("episode_audit", FILE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class EpisodeAuditTests(unittest.TestCase):
    def test_constant(self):
        self.assertEqual(m.episode_interval([0.0]*10), (0.0,0.0))
    def test_nonzero(self):
        self.assertEqual(m.episode_interval([1.0]*10), (1.0,1.0))
    def test_invalid(self):
        with self.assertRaises(ValueError):
            m.episode_interval([1.0]*9)
        with self.assertRaises(ValueError):
            m.simulate(episodes=9)
    def test_seed_reproducible(self):
        self.assertEqual(m.simulate(datasets=12,devices=8),m.simulate(datasets=12,devices=8))
    def test_range(self):
        r=m.simulate(datasets=12,devices=8)
        self.assertTrue(0 <= r["episode_t_coverage"] <= 1)

if __name__ == "__main__":
    unittest.main()
