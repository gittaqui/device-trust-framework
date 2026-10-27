"""Invented fixtures only; these tests do not estimate security performance."""
import copy
import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "audit_lanl_group_influence.py"
spec = importlib.util.spec_from_file_location("audit_lanl_group_influence", MODULE)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def fixtures():
    rows = []
    for i in range(25):
        matched = i < 18
        row = {"target_index": str(i), "target_time": str(i * 1300),
               "target_user": "u" + str(i % 4), "target_source_computer": "h" + str(i % 2),
               "matched": "True" if matched else "False"}
        for f in audit.FEATURES:
            row["target_" + f] = "5" if i % 5 else "0"
            row["control_" + f] = "1" if matched else ""
        rows.append(row)
    return rows


class GroupInfluenceTests(unittest.TestCase):
    def test_known_synthetic_counts_and_groups(self):
        rows = fixtures()
        result = audit.analyze(rows)
        self.assertEqual((result["total_targets"], result["matched"], result["unmatched"]), (25, 18, 7))
        self.assertEqual(result["matched_users"], 4)
        self.assertEqual(result["matched_source_hosts"], 2)
        self.assertEqual(result["episodes_all_targets"], 25)
        self.assertEqual(result["features"][audit.FEATURES[0]]["matched_target_higher"], 14)

    def test_order_invariance(self):
        rows = fixtures()
        self.assertEqual(audit.analyze(rows), audit.analyze(list(reversed(rows))))

    def test_omitted_group_reduces_denominator(self):
        rows = fixtures()
        ep = audit.episodes(rows)
        result = audit.leave_one_group_out(rows, audit.FEATURES[0], "user", ep)
        self.assertEqual(result["groups"], 4)
        self.assertEqual(sum(result["group_sizes"]), 18)
        self.assertLess(result["min_fraction"]["remaining"], 18)
        self.assertLessEqual(result["min_rate"], result["max_rate"])

    def test_episodes_merge_overlapping_windows(self):
        rows = fixtures()
        rows[1]["target_time"] = "700"  # within 2*600 seconds of target zero
        labels = audit.episodes(rows)
        self.assertEqual(labels["0"], labels["1"])
        self.assertNotEqual(labels["1"], labels["2"])

    def test_duplicate_target_index_rejected(self):
        rows = fixtures()
        rows[1]["target_index"] = "0"
        with self.assertRaises(ValueError):
            audit.analyze(rows)

    def test_missing_or_invalid_group_rejected(self):
        rows = fixtures()
        ep = audit.episodes(rows)
        with self.assertRaises(ValueError):
            audit.leave_one_group_out(rows, audit.FEATURES[0], "not_a_group", ep)
        for row in rows:
            row["target_user"] = "only_user"
        with self.assertRaises(ValueError):
            audit.leave_one_group_out(rows, audit.FEATURES[0], "user", ep)

    def test_negative_counts_rejected(self):
        rows = fixtures()
        rows[2]["target_proc_event_count"] = "-1"
        with self.assertRaises(ValueError):
            audit.analyze(rows)

    def test_hash_tampering_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p, m = Path(td) / "pairs.csv", Path(td) / "manifest.json"
            p.write_text("not frozen", encoding="utf-8")
            m.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                audit.read_frozen(p, m)

    def test_no_pseudonymous_ids_in_report(self):
        rows = fixtures()
        import json
        output = json.dumps(audit.analyze(rows))
        self.assertNotIn('"u0"', output)
        self.assertNotIn('"h0"', output)


if __name__ == "__main__":
    unittest.main()
