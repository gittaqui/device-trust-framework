"""Offline verification of frozen paired-process statistical reporting."""
import csv
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from analyze_lanl2015_replication import (
    analyze_csv, exact_two_sided_sign_pvalue, summarize_feature, wilson_95,
    PRIMARY_FEATURES,
)


class FrozenStatisticsTests(unittest.TestCase):
    def test_sign_test_predeclared_exact_p_values(self):
        self.assertEqual(exact_two_sided_sign_pvalue(3, 0), 0.25)
        self.assertEqual(exact_two_sided_sign_pvalue(3, 1), 0.625)
        self.assertEqual(exact_two_sided_sign_pvalue(0, 0), None)
        self.assertEqual(exact_two_sided_sign_pvalue(1, 1), 1.0)

    def test_wilson_boundaries(self):
        a = wilson_95(0, 10)
        b = wilson_95(10, 10)
        self.assertGreaterEqual(a[0], 0.0)
        self.assertLess(a[1], 0.5)
        self.assertGreater(b[0], 0.5)
        self.assertLessEqual(b[1], 1.0)
        self.assertIsNone(wilson_95(0, 0))

    def test_ties_excluded_without_discarding_matched_pairs(self):
        result = summarize_feature([3, 5, 6, 7], [3, 4, 3, 8])
        self.assertEqual(result["matched_pairs"], 4)
        self.assertEqual(result["target_higher_pairs"], 2)
        self.assertEqual(result["control_higher_pairs"], 1)
        self.assertEqual(result["tied_pairs"], 1)
        self.assertEqual(result["non_tied_pairs"], 3)
        self.assertEqual(result["exact_two_sided_sign_p"], 1.0)

    def write_pairs(self, path: Path, *, unexpected_index=False):
        fields = ["target_index", "matched"]
        for feature in PRIMARY_FEATURES:
            fields.extend([f"target_{feature}", f"control_{feature}"])
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for i in range(25):
                row = {"target_index": 26 if unexpected_index and i == 0 else i, "matched": "False" if i == 24 else "True"}
                for feature in PRIMARY_FEATURES:
                    row[f"target_{feature}"] = 4 if i != 24 else 0
                    row[f"control_{feature}"] = 2 if i != 24 else ""
                writer.writerow(row)

    def test_frozen_csv_all_three_primary_metrics(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "pairs.csv"
            self.write_pairs(path)
            result = analyze_csv(path)
            self.assertEqual(result["total_frozen_targets"], 25)
            self.assertEqual(result["unmatched_targets"], 1)
            self.assertEqual(result["matched_pairs"], 24)
            self.assertEqual(set(result["primary_feature_family"]), set(PRIMARY_FEATURES))
            self.assertEqual(result["primary_feature_family"]["proc_event_count"]["target_higher_pairs"], 24)
            self.assertIn("not verified benign", result["claim_boundary"])

    def test_wrong_cohort_index_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "pairs.csv"
            self.write_pairs(path, unexpected_index=True)
            with self.assertRaisesRegex(ValueError, "cohort-local"):
                analyze_csv(path)

    def test_empty_input_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "pairs.csv"
            path.write_text("", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "header"):
                analyze_csv(path)


if __name__ == "__main__":
    unittest.main()
