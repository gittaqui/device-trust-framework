"""Bounded remote extraction for LANL-2015 authentication telemetry.

The LANL authentication corpus is time ordered and too large to materialize in
small research sandboxes. This module uses HTTP byte-range requests plus a
binary search on the leading timestamp to read only bounded time windows.

Research integrity rules:
- only exact tuples present in redteam.txt receive ``is_exact_redteam=1``;
- temporal neighbors remain unlabeled context, not inferred attacks;
- no MDM/EDR/compliance semantics are inferred from LANL authentication rows.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Iterator, Protocol


@dataclass(frozen=True)
class AuthEvent:
    time: int
    source_user: str
    destination_user: str
    source_computer: str
    destination_computer: str
    authentication_type: str
    logon_type: str
    orientation: str
    result: str


@dataclass(frozen=True)
class RedTeamEvent:
    time: int
    user: str
    source_computer: str
    destination_computer: str


@dataclass(frozen=True)
class RangeBlock:
    start: int
    end: int
    total_size: int
    data: bytes


class ByteRangeReader(Protocol):
    def read(self, start: int, end: int) -> RangeBlock: ...


_CONTENT_RANGE = re.compile(r"^bytes (\d+)-(\d+)/(\d+)$")


class HTTPRangeReader:
    """HTTP reader that fails closed when byte ranges are not honored."""

    def __init__(self, url: str, *, token: str | None = None, timeout: int = 60) -> None:
        self.url = url
        self.token = token
        self.timeout = timeout
        self._size: int | None = None

    @property
    def size(self) -> int:
        if self._size is None:
            self._size = self.read(0, 0).total_size
        return self._size

    def read(self, start: int, end: int) -> RangeBlock:
        if start < 0 or end < start:
            raise ValueError("invalid byte range")
        headers = {
            "Range": f"bytes={start}-{end}",
            "Accept-Encoding": "identity",
            "User-Agent": "device-trust-framework-research/1.0",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = urllib.request.Request(self.url, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                status = getattr(response, "status", response.getcode())
                if status != 206:
                    raise RuntimeError(
                        f"server did not honor Range request: HTTP {status}; "
                        "refusing to materialize the large file"
                    )
                content_range = response.headers.get("Content-Range", "")
                match = _CONTENT_RANGE.match(content_range)
                if not match:
                    raise RuntimeError(f"invalid Content-Range header: {content_range!r}")
                actual_start, actual_end, total = map(int, match.groups())
                expected_len = actual_end - actual_start + 1
                data = response.read(expected_len)
                if len(data) != expected_len:
                    raise RuntimeError(
                        f"short range read: expected {expected_len} bytes, got {len(data)}"
                    )
                self._size = total
                return RangeBlock(actual_start, actual_end, total, data)
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"range request failed: HTTP {exc.code} for {self.url}") from exc


def hf_resolve_url(repo_id: str, path: str, revision: str = "main") -> str:
    repo = urllib.parse.quote(repo_id, safe="/")
    rev = urllib.parse.quote(revision, safe="")
    file_path = urllib.parse.quote(path, safe="/")
    return f"https://huggingface.co/datasets/{repo}/resolve/{rev}/{file_path}"


def parse_auth_line(line: str) -> AuthEvent:
    row = next(csv.reader([line]))
    if len(row) != 9:
        raise ValueError(f"expected 9 authentication fields, got {len(row)}")
    try:
        timestamp = int(row[0])
    except ValueError as exc:
        raise ValueError(f"invalid authentication timestamp: {row[0]!r}") from exc
    result = row[8].strip()
    if result.lower() not in {"success", "fail", "failure"}:
        raise ValueError(f"unknown authentication result: {result!r}")
    return AuthEvent(timestamp, *row[1:8], result)


def parse_redteam(lines: Iterable[str]) -> list[RedTeamEvent]:
    events: list[RedTeamEvent] = []
    for line_no, raw in enumerate(lines, 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        row = next(csv.reader([line]))
        if len(row) != 4:
            raise ValueError(f"redteam line {line_no}: expected 4 fields, got {len(row)}")
        events.append(RedTeamEvent(int(row[0]), row[1], row[2], row[3]))
    return events


def merge_windows(events: Iterable[RedTeamEvent], before: int, after: int) -> list[tuple[int, int]]:
    if before < 0 or after < 0:
        raise ValueError("window sizes must be non-negative")
    windows = sorted((max(0, e.time - before), e.time + after) for e in events)
    merged: list[list[int]] = []
    for start, end in windows:
        if not merged or start > merged[-1][1] + 1:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    return [(start, end) for start, end in merged]


def _first_complete_line(block: RangeBlock) -> tuple[int, bytes] | None:
    data = block.data
    if block.start == 0:
        line_start = 0
    else:
        first_newline = data.find(b"\n")
        if first_newline < 0 or first_newline + 1 >= len(data):
            return None
        line_start = first_newline + 1
    line_end = data.find(b"\n", line_start)
    if line_end < 0:
        return None
    return block.start + line_start, data[line_start:line_end]


def _timestamp_from_line(raw: bytes) -> int:
    first = raw.split(b",", 1)[0]
    return int(first)


def seek_before_time(
    reader: ByteRangeReader,
    target_time: int,
    *,
    total_size: int,
    probe_bytes: int = 64 * 1024,
) -> int:
    """Return a byte offset known to be at/before ``target_time``.

    The returned offset may precede the target by up to the convergence band;
    callers must scan forward and filter by exact timestamp.
    """
    if target_time <= 1 or total_size <= probe_bytes:
        return 0
    low = 0
    high = total_size - 1
    iterations = 0
    while high - low > probe_bytes and iterations < 80:
        iterations += 1
        mid = (low + high) // 2
        end = min(total_size - 1, mid + probe_bytes - 1)
        record = _first_complete_line(reader.read(mid, end))
        if record is None:
            high = mid
            continue
        record_offset, raw = record
        timestamp = _timestamp_from_line(raw)
        if timestamp < target_time:
            new_low = max(mid + 1, record_offset)
            if new_low <= low:
                new_low = low + 1
            low = min(new_low, high)
        else:
            high = mid
    return max(0, low - probe_bytes)


def iter_auth_window(
    reader: ByteRangeReader,
    start_time: int,
    end_time: int,
    *,
    total_size: int,
    chunk_bytes: int = 2 * 1024 * 1024,
) -> Iterator[AuthEvent]:
    if end_time < start_time:
        raise ValueError("end_time must be >= start_time")
    offset = seek_before_time(reader, start_time, total_size=total_size)
    carry = b""
    first_chunk = True
    last_time: int | None = None

    while offset < total_size:
        end = min(total_size - 1, offset + chunk_bytes - 1)
        block = reader.read(offset, end)
        data = block.data
        if first_chunk and offset > 0:
            nl = data.find(b"\n")
            if nl < 0:
                offset = block.end + 1
                continue
            data = data[nl + 1 :]
        first_chunk = False

        payload = carry + data
        parts = payload.split(b"\n")
        carry = parts.pop() if parts else b""
        for raw in parts:
            if not raw:
                continue
            line = raw.decode("utf-8", errors="strict")
            event = parse_auth_line(line)
            if last_time is not None and event.time < last_time:
                raise RuntimeError("authentication file is not monotonically time ordered")
            last_time = event.time
            if event.time < start_time:
                continue
            if event.time > end_time:
                return
            yield event

        if block.end >= total_size - 1:
            break
        offset = block.end + 1

    if carry:
        event = parse_auth_line(carry.decode("utf-8", errors="strict"))
        if start_time <= event.time <= end_time:
            yield event


def _download_small_text(url: str, *, token: str | None = None, timeout: int = 60) -> str:
    headers = {"User-Agent": "device-trust-framework-research/1.0"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8")


def extract(
    *,
    repo_id: str,
    auth_path: str,
    redteam_path: str,
    output_csv: Path,
    summary_json: Path,
    label_limit: int = 25,
    before_seconds: int = 600,
    after_seconds: int = 600,
    token: str | None = None,
    reader: ByteRangeReader | None = None,
    redteam_text: str | None = None,
) -> dict[str, object]:
    if label_limit < 1:
        raise ValueError("label_limit must be >= 1")
    red_url = hf_resolve_url(repo_id, redteam_path)
    auth_url = hf_resolve_url(repo_id, auth_path)
    if redteam_text is None:
        redteam_text = _download_small_text(red_url, token=token)
    labels_all = parse_redteam(io.StringIO(redteam_text))
    labels = labels_all[:label_limit]
    if not labels:
        raise RuntimeError("no red-team labels found")

    windows = merge_windows(labels, before_seconds, after_seconds)
    exact = {(x.time, x.user, x.source_computer, x.destination_computer) for x in labels}
    focus_users = {x.user for x in labels}
    focus_computers = {x.source_computer for x in labels} | {x.destination_computer for x in labels}

    remote_reader = reader if reader is not None else HTTPRangeReader(auth_url, token=token)
    total_size = remote_reader.size if isinstance(remote_reader, HTTPRangeReader) else remote_reader.read(0, 0).total_size

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "time", "source_user", "destination_user", "source_computer", "destination_computer",
        "authentication_type", "logon_type", "orientation", "result", "is_exact_redteam",
    ]
    scanned = 0
    retained = 0
    exact_matches = 0
    with output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for start, end in windows:
            for event in iter_auth_window(remote_reader, start, end, total_size=total_size):
                scanned += 1
                if not (
                    event.source_user in focus_users
                    or event.source_computer in focus_computers
                    or event.destination_computer in focus_computers
                ):
                    continue
                is_red = int((event.time, event.source_user, event.source_computer, event.destination_computer) in exact)
                exact_matches += is_red
                row = asdict(event)
                row["is_exact_redteam"] = is_red
                writer.writerow(row)
                retained += 1

    summary: dict[str, object] = {
        "dataset": "LANL Comprehensive Multi-Source Cyber-Security Events (2015)",
        "authoritative_doi": "10.17021/1179829",
        "mirror_repo": repo_id,
        "auth_path": auth_path,
        "redteam_path": redteam_path,
        "auth_remote_size_bytes": total_size,
        "label_rows_available": len(labels_all),
        "label_rows_selected": len(labels),
        "window_before_seconds": before_seconds,
        "window_after_seconds": after_seconds,
        "merged_window_count": len(windows),
        "merged_windows": [list(x) for x in windows],
        "auth_events_scanned_in_windows": scanned,
        "auth_events_retained_for_focus_entities": retained,
        "exact_redteam_auth_matches": exact_matches,
        "ground_truth_semantics": "Only exact redteam tuples are labeled malicious; temporal neighbors are context.",
        "evidence_scope": "Independent enterprise authentication telemetry/proxy evidence; not MDM/EDR compliance ground truth.",
    }
    summary_json.parent.mkdir(parents=True, exist_ok=True)
    summary_json.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract a bounded LANL auth cohort with HTTP byte ranges.")
    parser.add_argument("--repo-id", default="Taqui/lanl-cyber-datasets")
    parser.add_argument("--auth-path", default="lanl-2015/auth.txt")
    parser.add_argument("--redteam-path", default="lanl-2015/redteam.txt")
    parser.add_argument("--output", type=Path, default=Path("data/external/lanl-2015/auth-bounded.csv"))
    parser.add_argument("--summary", type=Path, default=Path("results/lanl-2015-bounded-extraction-summary.json"))
    parser.add_argument("--label-limit", type=int, default=25)
    parser.add_argument("--before-seconds", type=int, default=600)
    parser.add_argument("--after-seconds", type=int, default=600)
    args = parser.parse_args()
    summary = extract(
        repo_id=args.repo_id,
        auth_path=args.auth_path,
        redteam_path=args.redteam_path,
        output_csv=args.output,
        summary_json=args.summary,
        label_limit=args.label_limit,
        before_seconds=args.before_seconds,
        after_seconds=args.after_seconds,
        token=os.getenv("HF_TOKEN"),
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
