import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'experiments'))
from hac_oracle_audit_2026_11_17 import exact_vif, bartlett_population_vif, audit

class TestHACOracle(unittest.TestCase):
    def test_independent(self):
        for n in (10,30,100):
            self.assertAlmostEqual(exact_vif(n,0),1)
            self.assertAlmostEqual(bartlett_population_vif(n,0,3),1)
    def test_lag_zero(self):
        self.assertEqual(bartlett_population_vif(10,.9,0),1)
    def test_positive_correlation_underestimate(self):
        self.assertLess(bartlett_population_vif(30,.9,8),exact_vif(30,.9))
    def test_vif_matches_prior(self):
        self.assertAlmostEqual(exact_vif(10,.9),7.276211921,places=6)
    def test_invalid(self):
        for args in ((1,.2),(10,1),(10,float('nan'))):
            with self.assertRaises(ValueError): exact_vif(*args)
        for lag in (-1,10,1.5):
            with self.assertRaises(ValueError): bartlett_population_vif(10,.2,lag)
    def test_grid(self):
        self.assertEqual(len(audit()),36)

if __name__ == '__main__': unittest.main()
