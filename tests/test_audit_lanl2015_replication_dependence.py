"""Deterministic, synthetic-fixture tests for post-hoc LANL dependence auditing."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from audit_lanl2015_replication_dependence import assign_episodes, audit, group_summary, verify_manifest


def synthetic_rows():
    rows = []
    for i in range(25):
        time = [100, 1200, 2400][i] if i < 3 else 10000 + 3000 * i
        matched = i != 24
        rows.append({
            "target_index": str(i), "target_time": str(time),
            "target_user": "A" if i < 12 else "B",
            "target_source_computer": "H1" if i < 20 else "H2",
            "target_destination_computer": "D",
            "matched": str(matched),
            "control_time": str(time + 604800) if matched else "",
            "offset_seconds": "604800" if matched else "",
            "target_proc_event_count": "5", "control_proc_event_count": "3" if matched else "",
            "target_proc_unique_process_count": "4", "control_proc_unique_process_count": "1" if matched else "",
            "target_proc_start_count": "3", "control_proc_start_count": "2" if matched else "",
        })
    return rows


class DependenceAuditTests(unittest.TestCase):
    def test_transitive_target_window_overlap(self):
        episodes = assign_episodes(synthetic_rows())
        self.assertEqual(episodes[0], episodes[1])
        self.assertEqual(episodes[1], episodes[2])
        self.assertNotEqual(episodes[2], episodes[3])

    def test_group_leave_one_out(self):
        result = group_summary(synthetic_rows(), "proc_event_count", lambda r: r["target_user"])
        self.assertEqual(result["group_count"], 2)
        self.assertEqual(result["group_median_higher"], 2)
        self.assertEqual(result["leave_one_group_out"]["A"]["remaining_pairs"], 12)
        self.assertEqual(result["leave_one_group_out"]["B"]["remaining_pairs"], 12)

    def test_unmatched_not_counted_as_matched_observations(self):
        result = audit(synthetic_rows(), "synthetic-test-fixture")
        self.assertEqual(result["matched_pairs"], 24)
        self.assertEqual(result["unmatched_targets"], 1)
        self.assertEqual(result["distinct_target_users_matched"], 2)
        self.assertIn("not verified benign", result["claim_boundary"])

    def test_manifest_provenance_mismatch_fails_closed(self):
        rows = synthetic_rows()
        manifest = {"label_start_zero_based": 25, "target_label_count": 25,
                    "controls": [{
                        "target_index": i,
                        "target": {"time": int(row["target_time"]), "user": row["target_user"],
                                   "source_computer": row["target_source_computer"],
                                   "destination_computer": row["target_destination_computer"]},
                        "matched": row["matched"] == "True",
                        "control_time": int(row["control_time"]) if row["control_time"] else None,
                        "offset_seconds": 604800 if row["control_time"] else None,
                    } for i, row in enumerate(rows)]}
        verify_manifest(rows, manifest)
        corrupted = copy.deepcopy(manifest)
        corrupted["controls"][1]["target"]["time"] += 1
        with self.assertRaisesRegex(ValueError, "timestamp mismatch"):
            verify_manifest(rows, corrupted)


if __name__ == "__main__":
    unittest.main()
