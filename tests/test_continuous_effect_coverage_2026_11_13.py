import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'experiments'))
import continuous_effect_coverage_2026_11_13 as m
import random
import unittest

class CoverageTests(unittest.TestCase):
    def test_quantile(self):
        self.assertEqual(m.quantile([0,10],.25),2.5)
    def test_weighted_mean(self):
        self.assertAlmostEqual(m.weighted_mean([0,1],[1,3]),.75)
    def test_constant_effect(self):
        self.assertEqual(m.intervals([.2]*5,[1]*5,random.Random(1),20)[0],(.2,.2))
    def test_invalid(self):
        with self.assertRaises(ValueError): m.intervals([1],[1],random.Random(1))
    def test_reproducible(self):
        self.assertEqual(m.run(3,2,20),m.run(3,2,20))

if __name__=='__main__': unittest.main()
