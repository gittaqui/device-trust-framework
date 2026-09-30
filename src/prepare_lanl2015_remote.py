"""Prepare a bounded LANL-2015 validation cohort from a Hugging Face mirror.

This module deliberately downloads only the small red-team label file. Large telemetry
files remain remote; the emitted manifest defines temporal/entity extraction targets
for a later streaming pass. LANL red-team labels cover specific malicious
authentication events, not every event inside a surrounding window.
"""
from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

REPO_ID = "Taqui/lanl-cyber-datasets"
REPO_TYPE = "dataset"
REDTEAM_PATH = "lanl-2015/redteam.txt"
EXPECTED_2015 = ("auth.txt", "proc.txt", "flows.txt", "dns.txt", "redteam.txt")


@dataclass(frozen=True)
class RedTeamEvent:
    time: int
    user: str
    source_computer: str
    destination_computer: str


def parse_redteam(lines: Iterable[str]) -> list[RedTeamEvent]:
    events: list[RedTeamEvent] = []
    for line_no, raw in enumerate(lines, 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        row = next(csv.reader([line]))
        if len(row) != 4:
            raise ValueError(f"redteam line {line_no}: expected 4 fields, got {len(row)}")
        try:
            timestamp = int(row[0])
        except ValueError as exc:
            raise ValueError(f"redteam line {line_no}: invalid timestamp {row[0]!r}") from exc
        if timestamp < 0:
            raise ValueError(f"redteam line {line_no}: negative timestamp")
        events.append(RedTeamEvent(timestamp, row[1], row[2], row[3]))
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


def build_manifest(events: list[RedTeamEvent], before: int, after: int) -> dict:
    users = sorted({e.user for e in events})
    computers = sorted({e.source_computer for e in events} | {e.destination_computer for e in events})
    return {
        "dataset": "LANL Comprehensive Multi-Source Cyber-Security Events (2015)",
        "mirror_repo": REPO_ID,
        "label_file": REDTEAM_PATH,
        "label_semantics": "specific known red-team authentication events only",
        "redteam_event_count_raw": len(events),
        "unique_redteam_events": len(set(events)),
        "duplicate_redteam_rows": len(events) - len(set(events)),
        "unique_users": len(users),
        "unique_computers": len(computers),
        "window_before_seconds": before,
        "window_after_seconds": after,
        "merged_time_windows": [list(x) for x in merge_windows(events, before, after)],
        "redteam_users": users,
        "redteam_computers": computers,
        "events": [asdict(e) for e in events],
        "research_warning": (
            "Events surrounding a labeled red-team authentication are context, not automatically malicious. "
            "Do not convert window membership into ground-truth attack labels."
        ),
    }


def hf_inventory() -> list[str]:
    from huggingface_hub import list_repo_files
    return list_repo_files(REPO_ID, repo_type=REPO_TYPE)


def download_redteam() -> Path:
    from huggingface_hub import hf_hub_download
    return Path(hf_hub_download(repo_id=REPO_ID, filename=REDTEAM_PATH, repo_type=REPO_TYPE))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="data/external/lanl-2015/cohort-manifest.json")
    parser.add_argument("--before-seconds", type=int, default=3600)
    parser.add_argument("--after-seconds", type=int, default=3600)
    parser.add_argument("--inventory-output", default="data/external/lanl-2015/hf-inventory.json")
    args = parser.parse_args()

    files = hf_inventory()
    inventory_path = Path(args.inventory_output)
    inventory_path.parent.mkdir(parents=True, exist_ok=True)
    inventory = {
        "repo_id": REPO_ID,
        "file_count": len(files),
        "files": files,
        "lanl_2015_files": [f for f in files if f.startswith("lanl-2015/")],
        "expected_basename_presence": {
            name: any(f == f"lanl-2015/{name}" for f in files) for name in EXPECTED_2015
        },
    }
    inventory_path.write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")

    path = download_redteam()
    with path.open("r", encoding="utf-8", newline="") as handle:
        events = parse_redteam(handle)
    if not events:
        raise RuntimeError("redteam label file contained no events")

    manifest = build_manifest(events, args.before_seconds, args.after_seconds)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"inventory={inventory_path} files={len(files)}")
    print(f"manifest={output} redteam_rows={len(events)} windows={len(manifest['merged_time_windows'])}")


if __name__ == "__main__":
    main()
