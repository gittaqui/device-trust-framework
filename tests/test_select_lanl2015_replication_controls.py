import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from prepare_lanl2015_remote import RedTeamEvent
from select_lanl2015_replication_controls import REPLICATION_OFFSETS_SECONDS, build_replication_manifest

class ReplicationControlTests(unittest.TestCase):
    def events(self, n=60):
        return [RedTeamEvent(1000000+i*10000, f"U{i}@DOM1", f"C{i}", f"C{i+1000}") for i in range(n)]

    def test_exact_second_cohort(self):
        m=build_replication_manifest(self.events())
        targets=[x["target"] for x in m["controls"]]
        self.assertEqual(len(targets),25)
        self.assertEqual(targets[0]["user"],"U25@DOM1")
        self.assertEqual(targets[-1]["user"],"U49@DOM1")

    def test_frozen_offsets(self):
        m=build_replication_manifest(self.events())
        self.assertEqual(m["candidate_offsets_seconds"],list(REPLICATION_OFFSETS_SECONDS))
        self.assertEqual(REPLICATION_OFFSETS_SECONDS[:3],(604800,1209600,1814400))

    def test_overlap_skips_first_offset(self):
        events=self.events(50)
        t=events[25]
        events.append(RedTeamEvent(t.time+604800,"UX@DOM1","CX","CY"))
        m=build_replication_manifest(events)
        self.assertEqual(m["controls"][0]["offset_seconds"],1209600)

    def test_insufficient_rows_fail_closed(self):
        with self.assertRaises(ValueError):
            build_replication_manifest(self.events(49))

    def test_unlabeled_not_benign(self):
        m=build_replication_manifest(self.events())
        self.assertIn("not verified benign",m["control_semantics"])
        self.assertIn("does not establish benignness",m["research_warning"])

if __name__=="__main__":
    unittest.main()
