"""Paired LANL-2015 process/DNS/flow feature extraction.

This module compares the first frozen red-team target windows with their already
selected matched non-red-team temporal controls. Controls remain unlabeled; the
output is descriptive and must not be interpreted as attack-detection accuracy.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import statistics
import urllib.request
from pathlib import Path
from typing import Iterable

from extract_lanl_auth_remote import ByteRangeReader, HTTPRangeReader, RedTeamEvent, hf_resolve_url, parse_redteam
from extract_lanl_context_remote import SOURCE_SPECS, iter_csv_window

FROZEN_FEATURES = (
    "proc_event_count", "proc_unique_process_count", "proc_start_count", "proc_end_count",
    "dns_event_count", "dns_unique_resolved_computer_count",
    "flow_event_count", "flow_unique_peer_computer_count", "flow_unique_port_count",
    "flow_packet_count_sum", "flow_byte_count_sum", "flow_duration_sum", "flow_numeric_complete_count",
)


def _download_small_text(url: str, token: str | None = None) -> str:
    headers = {"User-Agent": "device-trust-framework-research/1.0"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8")


def _matches_target(source: str, row: list[str], target: RedTeamEvent) -> bool:
    computers = {target.source_computer, target.destination_computer}
    if source == "proc":
        return row[1] == target.user or row[2] in computers
    if source == "dns":
        return row[1] in computers or row[2] in computers
    if source == "flows":
        return row[2] in computers or row[4] in computers
    raise ValueError(f"unknown source: {source}")


def _parse_int(value: str) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def summarize_rows(source: str, rows: Iterable[list[str]], target: RedTeamEvent) -> dict[str, int]:
    selected = [row for row in rows if _matches_target(source, row, target)]
    if source == "proc":
        event_types = [row[4].strip().lower() for row in selected]
        return {
            "proc_event_count": len(selected),
            "proc_unique_process_count": len({row[3] for row in selected}),
            "proc_start_count": sum(kind == "start" for kind in event_types),
            "proc_end_count": sum(kind == "end" for kind in event_types),
        }
    if source == "dns":
        return {
            "dns_event_count": len(selected),
            "dns_unique_resolved_computer_count": len({row[2] for row in selected}),
        }
    if source == "flows":
        computers = {target.source_computer, target.destination_computer}
        peers: set[str] = set()
        ports: set[str] = set()
        packet_sum = byte_sum = duration_sum = numeric_complete = 0
        for row in selected:
            src, dst = row[2], row[4]
            if src not in computers:
                peers.add(src)
            if dst not in computers:
                peers.add(dst)
            ports.update((row[3], row[5]))
            duration = _parse_int(row[1])
            packets = _parse_int(row[7])
            bytes_ = _parse_int(row[8])
            if duration is not None and packets is not None and bytes_ is not None:
                duration_sum += duration
                packet_sum += packets
                byte_sum += bytes_
                numeric_complete += 1
        return {
            "flow_event_count": len(selected),
            "flow_unique_peer_computer_count": len(peers),
            "flow_unique_port_count": len(ports),
            "flow_packet_count_sum": packet_sum,
            "flow_byte_count_sum": byte_sum,
            "flow_duration_sum": duration_sum,
            "flow_numeric_complete_count": numeric_complete,
        }
    raise ValueError(f"unknown source: {source}")


def _reader_size(reader: ByteRangeReader) -> int:
    if isinstance(reader, HTTPRangeReader):
        return reader.size
    return reader.read(0, 0).total_size


def summarize_window(*, source: str, reader: ByteRangeReader, target: RedTeamEvent, start_time: int, end_time: int) -> dict[str, int]:
    spec = SOURCE_SPECS[source]
    return summarize_rows(
        source,
        iter_csv_window(reader, start_time, end_time, total_size=_reader_size(reader), expected_fields=int(spec["expected_fields"])),
        target,
    )


def _validate_manifest_target(control: dict[str, object], target: RedTeamEvent) -> None:
    embedded = control.get("target")
    expected = {
        "time": target.time,
        "user": target.user,
        "source_computer": target.source_computer,
        "destination_computer": target.destination_computer,
    }
    if embedded != expected:
        raise ValueError("control manifest target does not match current red-team label order")


def _descriptive_summary(rows: list[dict[str, object]]) -> dict[str, object]:
    matched = [row for row in rows if bool(row["matched"])]
    features: dict[str, object] = {}
    for feature in FROZEN_FEATURES:
        target_values = [int(row[f"target_{feature}"]) for row in matched]
        control_values = [int(row[f"control_{feature}"]) for row in matched]
        differences = [a - b for a, b in zip(target_values, control_values, strict=True)]
        features[feature] = {
            "matched_pairs": len(matched),
            "target_median": statistics.median(target_values) if target_values else None,
            "control_median": statistics.median(control_values) if control_values else None,
            "median_paired_difference": statistics.median(differences) if differences else None,
            "target_greater_pairs": sum(d > 0 for d in differences),
            "equal_pairs": sum(d == 0 for d in differences),
            "control_greater_pairs": sum(d < 0 for d in differences),
        }
    return features


def extract_paired_features(*, repo_id: str, redteam_path: str, control_manifest_path: Path, output_csv: Path, summary_json: Path,
                            label_limit: int = 25, radius_seconds: int = 600, token: str | None = None,
                            redteam_text: str | None = None, control_manifest: dict[str, object] | None = None,
                            readers: dict[str, ByteRangeReader] | None = None) -> dict[str, object]:
    if label_limit < 1:
        raise ValueError("label_limit must be >= 1")
    if radius_seconds < 0:
        raise ValueError("radius_seconds must be non-negative")
    if redteam_text is None:
        redteam_text = _download_small_text(hf_resolve_url(repo_id, redteam_path), token)
    labels = parse_redteam(io.StringIO(redteam_text))[:label_limit]
    if len(labels) != label_limit:
        raise ValueError("red-team label file contains fewer rows than requested label_limit")
    if control_manifest is None:
        control_manifest = json.loads(control_manifest_path.read_text(encoding="utf-8"))
    controls = control_manifest.get("controls")
    if not isinstance(controls, list) or len(controls) != len(labels):
        raise ValueError("control manifest does not contain one row per selected target")
    if int(control_manifest.get("radius_seconds", -1)) != radius_seconds:
        raise ValueError("control manifest radius does not match extraction radius")

    remotes: dict[str, ByteRangeReader] = {}
    for source in ("proc", "dns", "flows"):
        remotes[source] = readers[source] if readers is not None and source in readers else HTTPRangeReader(
            hf_resolve_url(repo_id, str(SOURCE_SPECS[source]["path"])), token=token
        )

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    rows_out: list[dict[str, object]] = []
    for index, (target, control) in enumerate(zip(labels, controls, strict=True)):
        if not isinstance(control, dict):
            raise ValueError("invalid control manifest row")
        _validate_manifest_target(control, target)
        row: dict[str, object] = {
            "target_index": index, "target_time": target.time, "target_user": target.user,
            "target_source_computer": target.source_computer, "target_destination_computer": target.destination_computer,
            "matched": bool(control.get("matched")), "control_time": control.get("control_time", ""),
            "offset_seconds": control.get("offset_seconds", ""),
        }
        target_features: dict[str, int] = {}
        for source in ("proc", "dns", "flows"):
            target_features.update(summarize_window(
                source=source, reader=remotes[source], target=target,
                start_time=max(0, target.time - radius_seconds), end_time=target.time + radius_seconds,
            ))
        control_features: dict[str, int] = {}
        if row["matched"]:
            for source in ("proc", "dns", "flows"):
                control_features.update(summarize_window(
                    source=source, reader=remotes[source], target=target,
                    start_time=int(control["window_start"]), end_time=int(control["window_end"]),
                ))
        for feature in FROZEN_FEATURES:
            row[f"target_{feature}"] = target_features[feature]
            row[f"control_{feature}"] = control_features.get(feature, "")
        rows_out.append(row)

    fieldnames = [
        "target_index", "target_time", "target_user", "target_source_computer", "target_destination_computer",
        "matched", "control_time", "offset_seconds",
    ] + [f"{side}_{feature}" for feature in FROZEN_FEATURES for side in ("target", "control")]
    with output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows_out)

    summary: dict[str, object] = {
        "dataset": "LANL Comprehensive Multi-Source Cyber-Security Events (2015)",
        "authoritative_doi": "10.17021/1179829", "mirror_repo": repo_id,
        "target_label_count": len(labels),
        "matched_pair_count": sum(bool(row["matched"]) for row in rows_out),
        "unmatched_pair_count": sum(not bool(row["matched"]) for row in rows_out),
        "radius_seconds": radius_seconds,
        "feature_freeze": "experiments/lanl-2015-paired-feature-freeze.md",
        "frozen_features": list(FROZEN_FEATURES),
        "descriptive_features": _descriptive_summary(rows_out),
        "control_semantics": "matched non-red-team temporal controls; unlabeled and not verified benign",
        "claim_boundary": "Descriptive paired external-telemetry comparison only. Not sensitivity, specificity, false-positive rate, causal effect, or production security effectiveness.",
    }
    summary_json.parent.mkdir(parents=True, exist_ok=True)
    summary_json.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract frozen paired LANL context features.")
    parser.add_argument("--repo-id", default="Taqui/lanl-cyber-datasets")
    parser.add_argument("--redteam-path", default="lanl-2015/redteam.txt")
    parser.add_argument("--control-manifest", type=Path, default=Path("data/external/lanl-2015/matched-control-manifest.json"))
    parser.add_argument("--output", type=Path, default=Path("data/external/lanl-2015/paired-context-features.csv"))
    parser.add_argument("--summary", type=Path, default=Path("results/lanl-2015-paired-context-summary.json"))
    parser.add_argument("--label-limit", type=int, default=25)
    parser.add_argument("--radius-seconds", type=int, default=600)
    args = parser.parse_args()
    summary = extract_paired_features(
        repo_id=args.repo_id, redteam_path=args.redteam_path, control_manifest_path=args.control_manifest,
        output_csv=args.output, summary_json=args.summary, label_limit=args.label_limit,
        radius_seconds=args.radius_seconds, token=os.getenv("HF_TOKEN"),
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
