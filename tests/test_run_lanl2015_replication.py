"""Deterministic offline tests for frozen LANL second-cohort execution gate."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from run_lanl2015_replication import (
    LABEL_START, LABEL_COUNT, PRIMARY_FEATURES,
    execute_replication, prepare_replication,
)
from prepare_lanl2015_remote import parse_redteam
from extract_lanl_paired_context_remote import FROZEN_FEATURES


def synthetic_labels(n=60):
    # Pure unit-test fixture; does NOT represent actual LANL records.
    return "".join(
        f"{1000000+i*10000},U{i}@DOM1,C{i},C{i+1000}\n"
        for i in range(n)
    )


class FrozenReplicationRunnerTests(unittest.TestCase):
    def test_frozen_cohort_exact_rows_26_through_50(self):
        selected, manifest = prepare_replication(synthetic_labels())
        events = parse_redteam(selected.splitlines())
        self.assertEqual((LABEL_START, LABEL_COUNT), (25, 25))
        self.assertEqual(len(events), 25)
        self.assertEqual(events[0].user, "U25@DOM1")
        self.assertEqual(events[-1].user, "U49@DOM1")
        self.assertEqual(manifest["target_label_count"], 25)
        self.assertEqual(manifest["candidate_offsets_seconds"], [
            604800, 1209600, 1814400, -604800, -1209600, -1814400
        ])

    def test_missing_replication_cohort_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "at least 50"):
            prepare_replication(synthetic_labels(49))

    def test_preflight_creates_manifest_without_telemetry(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with patch("run_lanl2015_replication.extract_paired_features") as extractor:
                result = execute_replication(
                    redteam_text=synthetic_labels(),
                    control_manifest_path=root / "manifest.json",
                    output_csv=root / "pairs.csv",
                    summary_json=root / "summary.json",
                    preflight_only=True,
                )
                extractor.assert_not_called()
            manifest = json.loads((root / "manifest.json").read_text())
            self.assertEqual(result["status"], "preflight_only")
            self.assertEqual(len(manifest["controls"]), 25)
            self.assertFalse((root / "pairs.csv").exists())
            self.assertIn("not verified benign", manifest["control_semantics"])

    def test_full_runner_preserves_existing_extractor_schema_and_provenance(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            fake_summary = {
                "frozen_features": list(FROZEN_FEATURES),
                "matched_pair_count": 24,
                "unmatched_pair_count": 1,
                "claim_boundary": "Descriptive external-context comparison only",
            }
            with patch("run_lanl2015_replication.extract_paired_features", return_value=copy.deepcopy(fake_summary)) as extractor:
                output = execute_replication(
                    redteam_text=synthetic_labels(),
                    control_manifest_path=root / "manifest.json",
                    output_csv=root / "pairs.csv",
                    summary_json=root / "summary.json",
                )
            args = extractor.call_args.kwargs
            self.assertEqual(args["label_limit"], 25)
            self.assertEqual(args["radius_seconds"], 600)
            labels = parse_redteam(args["redteam_text"].splitlines())
            self.assertEqual(labels[0].user, "U25@DOM1")
            self.assertEqual(labels[-1].user, "U49@DOM1")
            self.assertEqual(output["replication_provenance"]["original_redteam_row_start_one_based"], 26)
            self.assertEqual(output["replication_provenance"]["original_redteam_row_end_one_based_inclusive"], 50)
            saved = json.loads((root / "summary.json").read_text())
            self.assertEqual(saved["frozen_features"], list(FROZEN_FEATURES))
            self.assertEqual(saved["replication_provenance"]["preflight_only"], False)
            self.assertEqual(len(PRIMARY_FEATURES), 3)

    def test_schema_drift_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with patch("run_lanl2015_replication.extract_paired_features", return_value={"frozen_features": ["changed"]}):
                with self.assertRaisesRegex(RuntimeError, "unexpected frozen-feature"):
                    execute_replication(
                        redteam_text=synthetic_labels(),
                        control_manifest_path=root / "manifest.json",
                        output_csv=root / "pairs.csv",
                        summary_json=root / "summary.json",
                    )


if __name__ == "__main__":
    unittest.main()
