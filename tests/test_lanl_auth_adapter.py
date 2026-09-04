import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lanl_auth_adapter import StreamingAuthFeatureExtractor, parse_auth_line


class LanlAuthAdapterTests(unittest.TestCase):
    def test_parse_successful_event(self):
        event = parse_auth_line(
            "1,C625$@DOM1,U147@DOM1,C625,C625,Negotiate,Batch,LogOn,Success"
        )
        self.assertEqual(event.time, 1)
        self.assertEqual(event.source_user, "C625$@DOM1")
        self.assertEqual(event.destination_computer, "C625")
        self.assertTrue(event.success)

    def test_new_user_host_edge_has_higher_anomaly_than_repeat(self):
        extractor = StreamingAuthFeatureExtractor()
        first = extractor.transform(
            parse_auth_line(
                "1,U1@DOM1,U1@DOM1,C1,C2,Kerberos,Network,LogOn,Success"
            )
        )
        repeat = extractor.transform(
            parse_auth_line(
                "2,U1@DOM1,U1@DOM1,C1,C2,Kerberos,Network,LogOn,Success"
            )
        )
        self.assertGreater(first["anomaly_risk"], repeat["anomaly_risk"])
        self.assertEqual(first["new_user_host_edge"], 1)
        self.assertEqual(repeat["new_user_host_edge"], 0)

    def test_failed_history_reduces_identity_assurance(self):
        extractor = StreamingAuthFeatureExtractor()
        extractor.transform(
            parse_auth_line(
                "1,U1@DOM1,U1@DOM1,C1,C2,Kerberos,Network,LogOn,Failure"
            )
        )
        after_failure = extractor.transform(
            parse_auth_line(
                "2,U1@DOM1,U1@DOM1,C1,C2,Kerberos,Network,LogOn,Success"
            )
        )
        self.assertLess(after_failure["identity_assurance"], 1.0)
        self.assertGreater(after_failure["prior_failure_rate"], 0.0)


if __name__ == "__main__":
    unittest.main()
