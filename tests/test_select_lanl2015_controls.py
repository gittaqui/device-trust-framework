import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from prepare_lanl2015_remote import RedTeamEvent
from select_lanl2015_controls import FROZEN_OFFSETS_SECONDS, build_control_manifest, select_controls


class Lanl2015MatchedControlTests(unittest.TestCase):
    def event(self, time, user="U1@DOM1", src="C1", dst="C2"):
        return RedTeamEvent(time, user, src, dst)

    def test_uses_first_frozen_offset_when_clear(self):
        target = self.event(100000)
        controls = select_controls([target], [target], radius_seconds=600)
        self.assertTrue(controls[0]["matched"])
        self.assertEqual(controls[0]["offset_seconds"], FROZEN_OFFSETS_SECONDS[0])
        self.assertEqual(controls[0]["control_time"], 186400)

    def test_skips_candidate_overlapping_known_redteam(self):
        target = self.event(100000)
        blocking = self.event(186400, "U2@DOM1", "C3", "C4")
        controls = select_controls([target], [target, blocking], radius_seconds=600)
        self.assertEqual(controls[0]["offset_seconds"], 172800)

    def test_controls_cannot_overlap_each_other(self):
        targets = [self.event(100000), self.event(100100, "U2@DOM1", "C3", "C4")]
        controls = select_controls(targets, targets, radius_seconds=600)
        self.assertTrue(all(c["matched"] for c in controls))
        self.assertNotEqual(controls[0]["offset_seconds"], controls[1]["offset_seconds"])
        a0, a1 = controls[0]["window_start"], controls[0]["window_end"]
        b0, b1 = controls[1]["window_start"], controls[1]["window_end"]
        self.assertTrue(a1 < b0 or b1 < a0)

    def test_manifest_never_calls_controls_benign(self):
        events = [self.event(100000), self.event(200000, "U2@DOM1", "C3", "C4")]
        manifest = build_control_manifest(events, label_limit=1, radius_seconds=600)
        self.assertIn("not verified benign", manifest["control_semantics"])
        self.assertIn("does not establish benignness", manifest["research_warning"])
        self.assertEqual(manifest["target_label_count"], 1)
        self.assertEqual(manifest["redteam_rows_used_for_exclusion"], 2)

    def test_negative_radius_fails_closed(self):
        with self.assertRaises(ValueError):
            select_controls([self.event(100)], [self.event(100)], radius_seconds=-1)


if __name__ == "__main__":
    unittest.main()
