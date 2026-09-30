import csv
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from extract_lanl_auth_remote import (
    RangeBlock,
    extract,
    iter_auth_window,
    merge_windows,
    parse_auth_line,
    seek_before_time,
)


class BytesRangeReader:
    def __init__(self, payload: bytes):
        self.payload = payload

    def read(self, start: int, end: int) -> RangeBlock:
        if start >= len(self.payload):
            raise ValueError("start beyond EOF")
        actual_end = min(end, len(self.payload) - 1)
        return RangeBlock(start, actual_end, len(self.payload), self.payload[start:actual_end + 1])


def auth_line(t, user, src, dst, result="Success"):
    return f"{t},{user},U999@DOM1,{src},{dst},Kerberos,Network,LogOn,{result}\n"


class RemoteExtractTests(unittest.TestCase):
    def setUp(self):
        lines = []
        for t in range(10, 201, 10):
            user = "U1@DOM1" if t in {80, 90, 100, 110, 120} else "U2@DOM1"
            src = "C1" if t in {90, 100, 110} else "C8"
            dst = "C2" if t == 100 else "C9"
            lines.append(auth_line(t, user, src, dst))
        self.payload = "".join(lines).encode()
        self.reader = BytesRangeReader(self.payload)

    def test_parse_auth_schema(self):
        event = parse_auth_line(auth_line(100, "U1@DOM1", "C1", "C2").strip())
        self.assertEqual(event.time, 100)
        self.assertEqual(event.source_computer, "C1")
        self.assertEqual(event.result, "Success")

    def test_seek_and_window_do_not_miss_target(self):
        offset = seek_before_time(self.reader, 95, total_size=len(self.payload), probe_bytes=64)
        self.assertGreaterEqual(offset, 0)
        events = list(iter_auth_window(self.reader, 95, 115, total_size=len(self.payload), chunk_bytes=79))
        self.assertEqual([e.time for e in events], [100, 110])

    def test_merge_windows(self):
        class E:
            def __init__(self, time): self.time = time
        self.assertEqual(merge_windows([E(100), E(105), E(300)], 10, 10), [(90, 115), (290, 310)])

    def test_extract_labels_only_exact_tuple(self):
        redteam = "100,U1@DOM1,C1,C2\n"
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "subset.csv"
            summary = Path(td) / "summary.json"
            result = extract(
                repo_id="example/repo",
                auth_path="auth.txt",
                redteam_path="redteam.txt",
                output_csv=out,
                summary_json=summary,
                label_limit=1,
                before_seconds=20,
                after_seconds=20,
                reader=self.reader,
                redteam_text=redteam,
            )
            with out.open(newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            red = [r for r in rows if r["is_exact_redteam"] == "1"]
            self.assertEqual(len(red), 1)
            self.assertEqual(int(red[0]["time"]), 100)
            context = [r for r in rows if int(r["time"]) in {90, 110}]
            self.assertTrue(context)
            self.assertTrue(all(r["is_exact_redteam"] == "0" for r in context))
            self.assertEqual(result["exact_redteam_auth_matches"], 1)
            self.assertEqual(json.loads(summary.read_text())["exact_redteam_auth_matches"], 1)


if __name__ == "__main__":
    unittest.main()
