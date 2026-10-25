"""Deterministic validation of synthetic evidence-to-manuscript rendering."""
from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "render_paired_missingness_table", ROOT / "scripts" / "render_paired_missingness_table.py"
)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class TestPairedMissingnessTable(unittest.TestCase):
    def setUp(self):
        self.raw = json.loads((ROOT / "results" / "paired_missing_telemetry_mcar.json").read_text())

    def _checked(self, value):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "fixture.json"
            path.write_text(json.dumps(value))
            return module.checked_json(path, "mcar")

    def test_frozen_evidence_generates_committed_table(self):
        self.assertEqual(module.render(ROOT / "results"),
                         (ROOT / "paper" / "paired-missingness-table.tex").read_text())

    def test_synthetic_provenance_required(self):
        fixture = copy.deepcopy(self.raw)
        fixture["evidence_type"] = "real-world"
        with self.assertRaises(ValueError):
            self._checked(fixture)

    def test_corrupt_denominator_rejected(self):
        fixture = copy.deepcopy(self.raw)
        fixture["safe_rows"] += 1
        with self.assertRaises(ValueError):
            self._checked(fixture)

    def test_corrupt_rate_rejected(self):
        fixture = copy.deepcopy(self.raw)
        fixture["strategies"]["neutral"]["false_allow_rate"] = 0.0
        with self.assertRaises(ValueError):
            self._checked(fixture)

    def test_duplicate_baseline_divergence_rejected(self):
        fixture = copy.deepcopy(self.raw)
        fixture["strategies"]["confidence"]["false_allow_count"] += 1
        fixture["strategies"]["confidence"]["false_allow_rate"] = (
            fixture["strategies"]["confidence"]["false_allow_count"] / fixture["unsafe_rows"]
        )
        with self.assertRaises(ValueError):
            self._checked(fixture)

    def test_missing_strategy_rejected(self):
        fixture = copy.deepcopy(self.raw)
        del fixture["strategies"]["step_up"]
        with self.assertRaises(ValueError):
            self._checked(fixture)

    def test_mismatched_population_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            for key, _, filename in module.SOURCES:
                fixture = json.loads((ROOT / "results" / filename).read_text())
                if key == "critical_signal_biased":
                    fixture["scenario_counts"]["healthy"] += 1
                (Path(temp) / filename).write_text(json.dumps(fixture))
            with self.assertRaises(ValueError):
                module.render(Path(temp))


if __name__ == "__main__":
    unittest.main()
