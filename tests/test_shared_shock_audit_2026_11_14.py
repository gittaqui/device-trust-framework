import unittest
from shared_shock_audit import simulate, analytic_variance

class SharedShockTests(unittest.TestCase):
    def test_zero_shock_variance(self):
        a,b=analytic_variance(rho=0)
        self.assertAlmostEqual(a,b)
    def test_positive_shock_understates_variance(self):
        a,b=analytic_variance(rho=.5)
        self.assertGreater(a,b)
    def test_reproducible(self):
        self.assertEqual(simulate(datasets=20),simulate(datasets=20))
    def test_invalid(self):
        with self.assertRaises(ValueError): simulate(rho=1.2)

if __name__=='__main__': unittest.main()
