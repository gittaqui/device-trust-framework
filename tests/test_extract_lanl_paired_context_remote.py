import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from extract_lanl_auth_remote import RangeBlock
from extract_lanl_paired_context_remote import extract_paired_features, summarize_rows
from prepare_lanl2015_remote import RedTeamEvent


class BytesRangeReader:
    def __init__(self, text: str):
        self.payload = text.encode()

    def read(self, start: int, end: int) -> RangeBlock:
        actual_end = min(end, len(self.payload) - 1)
        return RangeBlock(start, actual_end, len(self.payload), self.payload[start:actual_end + 1])


class PairedContextTests(unittest.TestCase):
    def setUp(self):
        self.target = RedTeamEvent(100000, "U1@DOM1", "C1", "C2")
        self.redteam = "100000,U1@DOM1,C1,C2\n"
        self.manifest = {
            "radius_seconds": 600,
            "controls": [{
                "target_index": 0,
                "target": {
                    "time": 100000,
                    "user": "U1@DOM1",
                    "source_computer": "C1",
                    "destination_computer": "C2",
                },
                "matched": True,
                "control_time": 186400,
                "offset_seconds": 86400,
                "window_start": 185800,
                "window_end": 187000,
            }],
        }
        self.readers = {
            "proc": BytesRangeReader(
                "99950,U1@DOM1,C1,P1,Start\n"
                "100020,U9@DOM1,C9,P9,Start\n"
                "186350,U1@DOM1,C1,P2,Start\n"
            ),
            "dns": BytesRangeReader(
                "100010,C1,C5\n"
                "100020,C9,C8\n"
                "186410,C1,C6\n"
            ),
            "flows": BytesRangeReader(
                "100005,5,C1,80,C7,443,6,10,1000\n"
                "100020,1,C9,81,C8,53,17,2,100\n"
                "186405,3,C1,80,C7,443,6,5,500\n"
            ),
        }

    def test_schema_features_are_pair_specific(self):
        rows = [
            ["100", "U1@DOM1", "C1", "P1", "Start"],
            ["101", "U9@DOM1", "C9", "P9", "Start"],
        ]
        result = summarize_rows("proc", rows, self.target)
        self.assertEqual(result["proc_event_count"], 1)
        self.assertEqual(result["proc_unique_process_count"], 1)

    def test_live_shape_with_fake_readers(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            summary = extract_paired_features(
                repo_id="example/repo",
                redteam_path="redteam.txt",
                control_manifest_path=root / "unused.json",
                output_csv=root / "pairs.csv",
                summary_json=root / "summary.json",
                label_limit=1,
                radius_seconds=600,
                redteam_text=self.redteam,
                control_manifest=self.manifest,
                readers=self.readers,
            )
            self.assertEqual(summary["matched_pair_count"], 1)
            proc = summary["descriptive_features"]["proc_event_count"]
            self.assertEqual(proc["target_median"], 1)
            self.assertEqual(proc["control_median"], 1)
            self.assertEqual(proc["median_paired_difference"], 0)
            flow_bytes = summary["descriptive_features"]["flow_byte_count_sum"]
            self.assertEqual(flow_bytes["target_median"], 1000)
            self.assertEqual(flow_bytes["control_median"], 500)

            with (root / "pairs.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["target_dns_event_count"], "1")
            self.assertEqual(rows[0]["control_dns_event_count"], "1")
            saved = json.loads((root / "summary.json").read_text())
            self.assertIn("not verified benign", saved["control_semantics"])

    def test_manifest_target_mismatch_fails_closed(self):
        bad = json.loads(json.dumps(self.manifest))
        bad["controls"][0]["target"]["user"] = "U999@DOM1"
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with self.assertRaises(ValueError):
                extract_paired_features(
                    repo_id="example/repo",
                    redteam_path="redteam.txt",
                    control_manifest_path=root / "unused.json",
                    output_csv=root / "pairs.csv",
                    summary_json=root / "summary.json",
                    label_limit=1,
                    radius_seconds=600,
                    redteam_text=self.redteam,
                    control_manifest=bad,
                    readers=self.readers,
                )

    def test_unknown_flow_numeric_fields_not_imputed_as_zero_rows(self):
        rows = [["100", "?", "C1", "80", "C7", "443", "6", "?", "?"]]
        result = summarize_rows("flows", rows, self.target)
        self.assertEqual(result["flow_event_count"], 1)
        self.assertEqual(result["flow_numeric_complete_count"], 0)
        self.assertEqual(result["flow_byte_count_sum"], 0)


if __name__ == "__main__":
    unittest.main()
