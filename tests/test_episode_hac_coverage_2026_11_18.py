import random
import unittest
from experiments.episode_hac_coverage_2026_11_18 import ar1,cover,run
class TestHAC(unittest.TestCase):
    def test_reproducibility(self):
        self.assertEqual(ar1(10,.5,random.Random(3)),ar1(10,.5,random.Random(3)))
    def test_invalid_phi(self):
        with self.assertRaises(ValueError): ar1(10,1,random.Random(3))
    def test_invalid_lag(self):
        with self.assertRaises(ValueError): cover([0]*10,10)
    def test_zero(self):
        self.assertEqual(cover([0]*10,3),(1,0,0))
    def test_grid(self):
        rows=run(trials=5)
        self.assertEqual(len(rows),36)
        self.assertTrue(all(0<=v<=1 for r in rows for v in r[4:]))
if __name__=="__main__": unittest.main()
