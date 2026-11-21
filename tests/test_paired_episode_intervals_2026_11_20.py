import importlib.util
import pathlib
import random
import unittest
p=pathlib.Path(__file__).resolve().parents[1]/"experiments"/"paired_episode_intervals_2026_11_20.py"
s=importlib.util.spec_from_file_location("paired",p)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class TestPairedIntervals(unittest.TestCase):
    def test_invalid_phi(self):
        with self.assertRaises(ValueError): m.ar1(10,1.0,random.Random(1))
    def test_invalid_lag(self):
        with self.assertRaises(ValueError): m.coverage([0]*10,10)
    def test_zero_vector(self):
        self.assertEqual(m.coverage([0]*10),(1,0,0))
    def test_reproducibility(self):
        self.assertEqual(m.run(20,7),m.run(20,7))
    def test_bounds(self):
        for row in m.run(20,7):
            self.assertTrue(all(0<=v<=1 for v in row[3:]))
    def test_nine_conditions(self):
        self.assertEqual(len(m.run(1)),9)
if __name__=="__main__": unittest.main()
