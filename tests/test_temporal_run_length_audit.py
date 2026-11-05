import unittest
from src.temporal_run_length_audit import simulate

class Tests(unittest.TestCase):
    def test_repeatable(self):
        self.assertEqual(simulate(n_devices=30),simulate(n_devices=30))
    def test_transition_estimator(self):
        r=simulate()
        self.assertAlmostEqual(r["transition_exit_probability"],.15,delta=.008)
        self.assertAlmostEqual(r["transition_based_mean"],20/3,delta=.4)
    def test_censoring_reported(self):
        self.assertGreater(simulate()["right_censored_runs"],0)
    def test_invalid(self):
        with self.assertRaises(ValueError): simulate(rho=1)

if __name__ == "__main__": unittest.main()
