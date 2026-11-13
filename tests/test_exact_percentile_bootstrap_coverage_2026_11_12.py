import unittest
from experiments.exact_percentile_bootstrap_coverage_2026_11_12 import binomial_cdf,discrete_quantile,ideal_percentile_interval,exact_coverage

class TestExactPercentile(unittest.TestCase):
    def test_extreme_samples(self):
        self.assertEqual(ideal_percentile_interval(0,2),(0.,0.))
        self.assertEqual(ideal_percentile_interval(2,2),(1.,1.))
    def test_n2_mixed(self):
        self.assertEqual(ideal_percentile_interval(1,2),(0.,1.))
    def test_n2_coverage(self):
        self.assertAlmostEqual(exact_coverage(2,.3),.42)
    def test_cdf_boundaries(self):
        self.assertEqual(binomial_cdf(-1,5,.3),0)
        self.assertEqual(binomial_cdf(5,5,.3),1)
    def test_quantile_monotone(self):
        self.assertLessEqual(discrete_quantile(10,.3,.025),discrete_quantile(10,.3,.975))
    def test_invalid(self):
        for call in (lambda:exact_coverage(0),lambda:ideal_percentile_interval(3,2),lambda:discrete_quantile(2,.5,1)):
            with self.assertRaises(ValueError):call()

if __name__=="__main__":unittest.main()
