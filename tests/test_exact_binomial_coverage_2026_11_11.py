import unittest
from experiments.exact_binomial_coverage_2026_11_11 import cp_interval,exact_coverage
class Tests(unittest.TestCase):
    def test_bounds(self):
        self.assertEqual(cp_interval(0,2)[0],0.)
        self.assertEqual(cp_interval(2,2)[1],1.)
    def test_symmetry(self):
        a,b=cp_interval(1,5);c,d=cp_interval(4,5)
        self.assertAlmostEqual(a,1-d);self.assertAlmostEqual(b,1-c)
    def test_coverage(self):
        for n in (2,5,20,100):self.assertGreaterEqual(exact_coverage(n),.95-1e-10)
    def test_invalid(self):
        with self.assertRaises(ValueError):cp_interval(-1,5)
if __name__=="__main__":unittest.main()
