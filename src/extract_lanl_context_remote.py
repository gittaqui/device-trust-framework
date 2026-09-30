"""Extract bounded LANL-2015 process/DNS/flow context around red-team events.

These sources do not carry attack labels. Records are retained only because they
involve a user/computer implicated by selected red-team authentication labels
inside a bounded temporal window. They remain contextual telemetry, not inferred
malicious ground truth.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import urllib.request
from pathlib import Path
from typing import Iterator

from extract_lanl_auth_remote import (
    ByteRangeReader,
    HTTPRangeReader,
    RedTeamEvent,
    hf_resolve_url,
    merge_windows,
    parse_redteam,
    seek_before_time,
)


SOURCE_SPECS = {
    "proc": {
        "path": "lanl-2015/proc.txt",
        "fieldnames": ["time", "user", "computer", "process", "event_type"],
        "expected_fields": 5,
    },
    "dns": {
        "path": "lanl-2015/dns.txt",
        "fieldnames": ["time", "source_computer", "resolved_computer"],
        "expected_fields": 3,
    },
    "flows": {
        "path": "lanl-2015/flows.txt",
        "fieldnames": [
            "time", "duration", "source_computer", "source_port",
            "destination_computer", "destination_port", "protocol",
            "packet_count", "byte_count",
        ],
        "expected_fields": 9,
    },
}


def _download_small_text(url: str, token: str | None = None) -> str:
    headers = {"User-Agent": "device-trust-framework-research/1.0"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(req, timeout=60) as response:
        return response.read().decode("utf-8")


def iter_csv_window(
    reader: ByteRangeReader,
    start_time: int,
    end_time: int,
    *,
    total_size: int,
    expected_fields: int,
    chunk_bytes: int = 2 * 1024 * 1024,
) -> Iterator[list[str]]:
    """Yield complete, time-ordered CSV records inside one time window."""
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
            row = next(csv.reader([raw.decode("utf-8", errors="strict")]))
            if len(row) != expected_fields:
                raise ValueError(f"expected {expected_fields} fields, got {len(row)}")
            timestamp = int(row[0])
            if last_time is not None and timestamp < last_time:
                raise RuntimeError("source file is not monotonically time ordered")
            last_time = timestamp
            if timestamp < start_time:
                continue
            if timestamp > end_time:
                return
            yield row

        if block.end >= total_size - 1:
            break
        offset = block.end + 1

    if carry:
        row = next(csv.reader([carry.decode("utf-8", errors="strict")]))
        if len(row) != expected_fields:
            raise ValueError(f"expected {expected_fields} fields, got {len(row)}")
        timestamp = int(row[0])
        if start_time <= timestamp <= end_time:
            yield row


def _focus_match(source: str, row: list[str], users: set[str], computers: set[str]) -> bool:
    if source == "proc":
        return row[1] in users or row[2] in computers
    if source == "dns":
        return row[1] in computers or row[2] in computers
    if source == "flows":
        return row[2] in computers or row[4] in computers
    raise ValueError(f"unknown source: {source}")


def extract_source(
    *,
    source: str,
    repo_id: str,
    labels: list[RedTeamEvent],
    windows: list[tuple[int, int]],
    output_csv: Path,
    token: str | None = None,
    reader: ByteRangeReader | None = None,
) -> dict[str, object]:
    spec = SOURCE_SPECS[source]
    users = {e.user for e in labels}
    computers = {e.source_computer for e in labels} | {e.destination_computer for e in labels}
    url = hf_resolve_url(repo_id, str(spec["path"]))
    remote = reader if reader is not None else HTTPRangeReader(url, token=token)
    total_size = remote.size if isinstance(remote, HTTPRangeReader) else remote.read(0, 0).total_size

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(spec["fieldnames"]) + ["context_only"]
    scanned = 0
    retained = 0
    with output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for start, end in windows:
            for row in iter_csv_window(
                remote,
                start,
                end,
                total_size=total_size,
                expected_fields=int(spec["expected_fields"]),
            ):
                scanned += 1
                if not _focus_match(source, row, users, computers):
                    continue
                record = dict(zip(spec["fieldnames"], row, strict=True))
                record["context_only"] = 1
                writer.writerow(record)
                retained += 1
    return {
        "source": source,
        "path": spec["path"],
        "remote_size_bytes": total_size,
        "events_scanned_in_windows": scanned,
        "events_retained_for_focus_entities": retained,
        "label_semantics": "No attack label assigned; records are context only.",
    }


def extract_context(
    *,
    repo_id: str,
    redteam_path: str,
    output_dir: Path,
    summary_path: Path,
    label_limit: int = 25,
    before_seconds: int = 600,
    after_seconds: int = 600,
    token: str | None = None,
    redteam_text: str | None = None,
    readers: dict[str, ByteRangeReader] | None = None,
) -> dict[str, object]:
    if label_limit < 1:
        raise ValueError("label_limit must be >= 1")
    if redteam_text is None:
        redteam_text = _download_small_text(hf_resolve_url(repo_id, redteam_path), token)
    labels_all = parse_redteam(io.StringIO(redteam_text))
    labels = labels_all[:label_limit]
    if not labels:
        raise RuntimeError("no red-team labels found")
    windows = merge_windows(labels, before_seconds, after_seconds)

    per_source: dict[str, object] = {}
    for source in ("proc", "dns", "flows"):
        per_source[source] = extract_source(
            source=source,
            repo_id=repo_id,
            labels=labels,
            windows=windows,
            output_csv=output_dir / f"{source}-bounded.csv",
            token=token,
            reader=None if readers is None else readers.get(source),
        )

    summary: dict[str, object] = {
        "dataset": "LANL Comprehensive Multi-Source Cyber-Security Events (2015)",
        "authoritative_doi": "10.17021/1179829",
        "mirror_repo": repo_id,
        "label_rows_available": len(labels_all),
        "label_rows_selected": len(labels),
        "window_before_seconds": before_seconds,
        "window_after_seconds": after_seconds,
        "merged_window_count": len(windows),
        "merged_windows": [list(w) for w in windows],
        "sources": per_source,
        "ground_truth_warning": (
            "Process, DNS, and flow rows are contextual telemetry only. Window/entity membership "
            "does not make them malicious ground truth."
        ),
        "evidence_scope": (
            "Independent enterprise telemetry/proxy evidence; not actual MDM compliance, patch, "
            "EDR health, or proprietary identity-risk evidence."
        ),
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract bounded LANL process/DNS/flow context remotely.")
    parser.add_argument("--repo-id", default="Taqui/lanl-cyber-datasets")
    parser.add_argument("--redteam-path", default="lanl-2015/redteam.txt")
    parser.add_argument("--output-dir", type=Path, default=Path("data/external/lanl-2015/context"))
    parser.add_argument("--summary", type=Path, default=Path("results/lanl-2015-context-summary.json"))
    parser.add_argument("--label-limit", type=int, default=25)
    parser.add_argument("--before-seconds", type=int, default=600)
    parser.add_argument("--after-seconds", type=int, default=600)
    args = parser.parse_args()
    summary = extract_context(
        repo_id=args.repo_id,
        redteam_path=args.redteam_path,
        output_dir=args.output_dir,
        summary_path=args.summary,
        label_limit=args.label_limit,
        before_seconds=args.before_seconds,
        after_seconds=args.after_seconds,
        token=os.getenv("HF_TOKEN"),
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
