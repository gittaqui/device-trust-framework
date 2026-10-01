"""Deterministically select matched non-red-team temporal controls for LANL-2015.

Controls are explicitly unlabeled/non-red-team, not verified benign. Selection uses
only red-team timestamps and a frozen offset order; telemetry outcomes are never
consulted.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from prepare_lanl2015_remote import RedTeamEvent, download_redteam, merge_windows, parse_redteam

FROZEN_OFFSETS_SECONDS = (86400, 172800, 259200, 604800, -86400, -172800, -259200, -604800)


def _overlaps(a_start: int, a_end: int, b_start: int, b_end: int) -> bool:
    return a_start <= b_end and b_start <= a_end


def select_controls(
    targets: list[RedTeamEvent],
    all_redteam: list[RedTeamEvent],
    *,
    radius_seconds: int = 600,
    offsets: tuple[int, ...] = FROZEN_OFFSETS_SECONDS,
) -> list[dict[str, object]]:
    if radius_seconds < 0:
        raise ValueError("radius_seconds must be non-negative")
    red_windows = [(max(0, e.time - radius_seconds), e.time + radius_seconds) for e in all_redteam]
    used: list[tuple[int, int]] = []
    selected: list[dict[str, object]] = []

    for index, target in enumerate(targets):
        choice: tuple[int, int, int, int] | None = None
        for offset in offsets:
            candidate = target.time + offset
            start, end = candidate - radius_seconds, candidate + radius_seconds
            if start < 0:
                continue
            if any(_overlaps(start, end, r0, r1) for r0, r1 in red_windows):
                continue
            if any(_overlaps(start, end, c0, c1) for c0, c1 in used):
                continue
            choice = (candidate, offset, start, end)
            used.append((start, end))
            break

        row: dict[str, object] = {
            "target_index": index,
            "target": asdict(target),
            "matched": choice is not None,
        }
        if choice is not None:
            candidate, offset, start, end = choice
            row.update({
                "control_time": candidate,
                "offset_seconds": offset,
                "window_start": start,
                "window_end": end,
            })
        selected.append(row)
    return selected


def build_control_manifest(
    all_redteam: list[RedTeamEvent],
    *,
    label_limit: int = 25,
    radius_seconds: int = 600,
) -> dict[str, object]:
    if label_limit < 1:
        raise ValueError("label_limit must be >= 1")
    targets = all_redteam[:label_limit]
    controls = select_controls(targets, all_redteam, radius_seconds=radius_seconds)
    matched = [c for c in controls if c["matched"]]
    pseudo_events = [
        RedTeamEvent(int(c["control_time"]), "", "", "")
        for c in matched
    ]
    return {
        "dataset": "LANL Comprehensive Multi-Source Cyber-Security Events (2015)",
        "authoritative_doi": "10.17021/1179829",
        "control_semantics": "matched non-red-team temporal controls; unlabeled and not verified benign",
        "target_label_count": len(targets),
        "redteam_rows_used_for_exclusion": len(all_redteam),
        "radius_seconds": radius_seconds,
        "candidate_offsets_seconds": list(FROZEN_OFFSETS_SECONDS),
        "matched_count": len(matched),
        "unmatched_count": len(controls) - len(matched),
        "controls": controls,
        "merged_control_windows": [list(x) for x in merge_windows(pseudo_events, radius_seconds, radius_seconds)],
        "research_warning": (
            "Absence from redteam.txt does not establish benignness. Control windows must not be "
            "reported as known-benign traffic or used to compute a false-positive rate."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("data/external/lanl-2015/matched-control-manifest.json"))
    parser.add_argument("--label-limit", type=int, default=25)
    parser.add_argument("--radius-seconds", type=int, default=600)
    args = parser.parse_args()

    path = download_redteam()
    with path.open("r", encoding="utf-8", newline="") as handle:
        events = parse_redteam(handle)
    manifest = build_control_manifest(events, label_limit=args.label_limit, radius_seconds=args.radius_seconds)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(args.output),
        "matched": manifest["matched_count"],
        "unmatched": manifest["unmatched_count"],
    }, indent=2))


if __name__ == "__main__":
    main()
