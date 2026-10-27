"""Deterministic, invented-fixture tests; not empirical endpoint results."""
from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from render_lanl_replication_results import analyze, load_and_verify, render_tex

FEATURES = ("proc_event_count", "proc_unique_process_count", "proc_start_count")


def fixture_rows():
    rows = []
    controls = []
    for i in range(25):
        matched = i < 18
        row = {
            "target_index": str(i), "target_time": str(i * 2000),
            "target_user": f"TEST_USER_{i // 5}", "target_source_computer": f"TEST_HOST_{i // 10}",
            "target_destination_computer": "TEST_DEST", "matched": str(matched),
            "control_time": str(i * 2000 + 604800) if matched else "",
            "offset_seconds": "604800" if matched else "",
        }
        control = {
            "target_index": i,
            "target": {"time": i * 2000, "user": row["target_user"],
                       "source_computer": row["target_source_computer"], "destination_computer": "TEST_DEST"},
            "matched": matched,
        }
        if matched:
            control.update({"control_time": i * 2000 + 604800, "offset_seconds": 604800})
        for feature in FEATURES:
            row["target_" + feature] = "5"
            row["control_" + feature] = "2" if matched else ""
        rows.append(row)
        controls.append(control)
    manifest = {
        "label_start_zero_based": 25, "target_label_count": 25, "radius_seconds": 600,
        "matched_count": 18, "unmatched_count": 7,
        "candidate_offsets_seconds": [604800], "controls": controls,
    }
    return rows, manifest


class FrozenRendererTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.pairs = Path(self.temp.name) / "pairs.csv"
        self.manifest = Path(self.temp.name) / "manifest.json"
        self.rows, self.manifest_obj = fixture_rows()
        self.write()

    def write(self):
        with self.pairs.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(self.rows[0]))
            writer.writeheader()
            writer.writerows(self.rows)
        self.manifest.write_text(json.dumps(self.manifest_obj), encoding="utf-8")

    def test_frozen_cli_refuses_unrecognized_hashes(self):
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            load_and_verify(self.pairs, self.manifest)

    def test_invented_fixture_bounds(self):
        rows = load_and_verify(self.pairs, self.manifest, require_frozen_hash=False)
        result = analyze(rows)
        self.assertEqual(result["matched"], 18)
        self.assertEqual(result["unmatched"], 7)
        self.assertEqual(result["features"]["proc_event_count"]["higher"], 18)
        self.assertEqual(result["features"]["proc_event_count"]["bound_lower"], 18/25)
        self.assertEqual(result["features"]["proc_event_count"]["bound_upper"], 1.0)
        self.assertEqual(result["overlap_episodes_all"], 25)

    def test_zero_unmatched_target_cannot_be_higher(self):
        self.rows[-1]["target_proc_event_count"] = "0"
        self.write()
        result = analyze(load_and_verify(self.pairs, self.manifest, require_frozen_hash=False))
        self.assertEqual(result["features"]["proc_event_count"]["bound_upper"], 24/25)

    def test_control_offset_tampering_rejected(self):
        self.rows[0]["control_time"] = "604801"
        self.write()
        with self.assertRaisesRegex(ValueError, "control time"):
            load_and_verify(self.pairs, self.manifest, require_frozen_hash=False)

    def test_target_identity_tampering_rejected(self):
        self.rows[0]["target_user"] = "DIFFERENT_TEST_USER"
        self.write()
        with self.assertRaisesRegex(ValueError, "target entity"):
            load_and_verify(self.pairs, self.manifest, require_frozen_hash=False)

    def test_negative_counts_rejected(self):
        self.rows[0]["target_proc_start_count"] = "-1"
        self.write()
        with self.assertRaisesRegex(ValueError, "negative event count"):
            load_and_verify(self.pairs, self.manifest, require_frozen_hash=False)

    def test_render_deterministic_and_cautious(self):
        result = analyze(load_and_verify(self.pairs, self.manifest, require_frozen_hash=False))
        first = render_tex(result)
        self.assertEqual(first, render_tex(result))
        self.assertIn("not verified benign", first)
        self.assertIn("not} confidence intervals", first)
        self.assertIn("18/18", first)
        self.assertNotIn("sensitivity of the model", first)


if __name__ == "__main__":
    unittest.main()
