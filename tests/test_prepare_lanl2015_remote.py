import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from prepare_lanl2015_remote import build_manifest, merge_windows, parse_redteam


class PrepareLanl2015RemoteTests(unittest.TestCase):
    def test_parse_redteam(self):
        events = parse_redteam([
            "151648,U748@DOM1,C17693,C728\n",
            "151993,U6115@DOM1,C17693,C1173\n",
        ])
        self.assertEqual(events[0].time, 151648)
        self.assertEqual(events[1].destination_computer, "C1173")

    def test_merge_overlapping_windows(self):
        events = parse_redteam([
            "100,U1@DOM1,C1,C2\n",
            "150,U2@DOM1,C3,C4\n",
            "500,U3@DOM1,C5,C6\n",
        ])
        self.assertEqual(merge_windows(events, 60, 60), [(40, 210), (440, 560)])

    def test_manifest_does_not_relabel_context_as_attack(self):
        events = parse_redteam([
            "100,U1@DOM1,C1,C2\n",
            "100,U1@DOM1,C1,C2\n",
        ])
        manifest = build_manifest(events, 10, 20)
        self.assertEqual(manifest["redteam_event_count_raw"], 2)
        self.assertEqual(manifest["unique_redteam_events"], 1)
        self.assertEqual(manifest["duplicate_redteam_rows"], 1)
        self.assertIn("not automatically malicious", manifest["research_warning"])

    def test_bad_schema_fails_closed(self):
        with self.assertRaises(ValueError):
            parse_redteam(["100,U1,C1\n"])


if __name__ == "__main__":
    unittest.main()
