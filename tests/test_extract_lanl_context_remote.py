import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from extract_lanl_auth_remote import RangeBlock
from extract_lanl_context_remote import extract_context, iter_csv_window


class BytesRangeReader:
    def __init__(self, text: str):
        self.payload = text.encode()

    def read(self, start: int, end: int) -> RangeBlock:
        actual_end = min(end, len(self.payload) - 1)
        return RangeBlock(start, actual_end, len(self.payload), self.payload[start:actual_end + 1])


def make_rows(kind: str) -> str:
    rows = []
    for t in range(10, 201, 10):
        focus = t in {90, 100, 110}
        if kind == "proc":
            rows.append(f"{t},{'U1@DOM1' if focus else 'U2@DOM1'},{'C1' if focus else 'C9'},P1,Start\n")
        elif kind == "dns":
            rows.append(f"{t},{'C1' if focus else 'C9'},C20\n")
        elif kind == "flows":
            rows.append(f"{t},1,{'C1' if focus else 'C9'},80,C20,443,6,2,100\n")
    return "".join(rows)


class ContextExtractTests(unittest.TestCase):
    def test_generic_window(self):
        reader = BytesRangeReader(make_rows("dns"))
        rows = list(iter_csv_window(reader, 95, 115, total_size=len(reader.payload), expected_fields=3, chunk_bytes=37))
        self.assertEqual([int(r[0]) for r in rows], [100, 110])

    def test_context_is_not_attack_labeled(self):
        redteam = "100,U1@DOM1,C1,C2\n"
        readers = {name: BytesRangeReader(make_rows(name)) for name in ("proc", "dns", "flows")}
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            result = extract_context(
                repo_id="example/repo",
                redteam_path="redteam.txt",
                output_dir=root / "context",
                summary_path=root / "summary.json",
                label_limit=1,
                before_seconds=20,
                after_seconds=20,
                redteam_text=redteam,
                readers=readers,
            )
            self.assertIn("does not make them malicious", result["ground_truth_warning"])
            for source in ("proc", "dns", "flows"):
                path = root / "context" / f"{source}-bounded.csv"
                with path.open(newline="", encoding="utf-8") as f:
                    rows = list(csv.DictReader(f))
                self.assertEqual(len(rows), 3)
                self.assertTrue(all(r["context_only"] == "1" for r in rows))
            saved = json.loads((root / "summary.json").read_text())
            self.assertEqual(saved["label_rows_selected"], 1)


if __name__ == "__main__":
    unittest.main()
