"""Regression checks for correlated synthetic telemetry dropout (no tenant data)."""
import csv
import math
import random
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from evaluate_correlated_missingness import ARMS, ENDPOINT, POLICIES, SIGNALS, evaluate, make_masks, run_seed


class CorrelatedMissingnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.path = Path(cls.temp.name) / "sample.csv"
        cls.signals = {name: .9 if not name.endswith("_risk") else .1 for name in SIGNALS}
        with cls.path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=("safe_for_ordinary_access", "scenario", *SIGNALS))
            writer.writeheader()
            for i in range(300):
                vals = dict(cls.signals)
                if i % 3 == 0:
                    vals["identity_assurance"] = .15
                    vals["anomaly_risk"] = .75
                if i % 5 == 0:
                    vals["threat_risk"] = .95
                writer.writerow({"safe_for_ordinary_access":str(int(i % 3 != 0 and i % 5 != 0)),
                                 "scenario":"synthetic_unsafe" if i % 3 == 0 or i % 5 == 0 else "synthetic_safe",**vals})

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_no_missing_and_all_missing_in_global_arm(self):
        u = {name: .9 for name in SIGNALS}
        arms = make_masks(self.signals, u, .1, .1, .25)
        self.assertEqual(arms["global_rho_one"], {})
        self.assertEqual(arms["independent"], self.signals)
        arms = make_masks(self.signals, u, .9, .1, .25)
        self.assertEqual(arms["global_rho_one"], self.signals)

    def test_non_endpoint_signals_identical_in_endpoint_arms(self):
        rng = random.Random(42)
        for _ in range(100):
            u = {name:rng.random() for name in SIGNALS}
            shared,selector = rng.random(),rng.random()
            arms = make_masks(self.signals,u,shared,selector,.25)
            for arm in ("endpoint_rho_half","endpoint_rho_one"):
                for name in SIGNALS:
                    if name not in ENDPOINT:
                        self.assertEqual(name in arms[arm],name in arms["independent"])

    def test_endpoint_rho_one_is_joint(self):
        rng = random.Random(13)
        for _ in range(100):
            u = {name:rng.random() for name in SIGNALS}
            arms = make_masks(self.signals,u,rng.random(),rng.random(),.25)
            self.assertEqual(len(ENDPOINT.intersection(arms["endpoint_rho_one"])), 0 if not any(n in arms["endpoint_rho_one"] for n in ENDPOINT) else len(ENDPOINT))

    def test_marginals_and_pair_correlation(self):
        rng = random.Random(4)
        counts = {a:[0,0,0] for a in ARMS}
        n=12000
        for _ in range(n):
            u = {name:rng.random() for name in SIGNALS}
            masks = make_masks(self.signals,u,rng.random(),rng.random(),.25)
            for arm, mask in masks.items():
                a=int('endpoint_health' not in mask)
                b=int('security_coverage' not in mask)
                counts[arm][0]+=a
                counts[arm][1]+=b
                counts[arm][2]+=a*b
        for arm,(a,b,ab) in counts.items():
            p,q,j=a/n,b/n,ab/n
            self.assertAlmostEqual(p,.25,delta=.025)
            self.assertAlmostEqual(q,.25,delta=.025)
            phi=(j-p*q)/math.sqrt(p*(1-p)*q*(1-q))
            expected={'independent':0,'endpoint_rho_half':.5,'endpoint_rho_one':1,'global_rho_one':1}[arm]
            self.assertAlmostEqual(phi,expected,delta=.04)

    def test_policy_counts_and_paired_flips(self):
        from evaluate_correlated_missingness import load_rows
        out=run_seed(load_rows(self.path),seed=7,rate=.25)
        for arm in ARMS:
            for policy in POLICIES:
                p=out['arms'][arm]['policies'][policy]
                self.assertEqual(sum(p['decisions'].values()),300)
                self.assertEqual(p['safe_allow_count']+p['safe_deny_count']+p['safe_step_up_count'],out['safe_rows'])
                self.assertEqual(sum(x['allow_count'] for x in p['unsafe_allow_by_scenario'].values()),p['unsafe_allow_count'])
                if arm!='independent':
                    f=p['paired_allow_flips_vs_independent']
                    baseline=out['arms']['independent']['policies'][policy]
                    self.assertEqual(p['unsafe_allow_count']-baseline['unsafe_allow_count'],f['unsafe_not_to_allow']-f['unsafe_allow_to_not'])
        for policy in POLICIES[1:]:
            self.assertEqual(out['arms']['global_rho_one']['policies'][policy]['decisions'],
                             out['arms']['global_rho_one']['policies'][POLICIES[0]]['decisions'])

    def test_reproducibility(self):
        self.assertEqual(evaluate(self.path,seeds=(5,6)),evaluate(self.path,seeds=(5,6)))

    def test_bad_arguments(self):
        with self.assertRaises(ValueError):
            evaluate(self.path,rate=0)
        with self.assertRaises(ValueError):
            evaluate(self.path,seeds=(5,5))
        with self.assertRaises(ValueError):
            make_masks(self.signals,{name:float('nan') for name in SIGNALS},.1,.2,.25)

if __name__=='__main__':
    unittest.main()
