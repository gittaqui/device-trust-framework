"""Post-replication dependence audit; descriptive, not a new hypothesis test.

Run after the frozen LANL rows-26–50 extraction. Episode membership is based
solely on overlap of target +/-600-second windows, independent of outcomes.
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import statistics
from pathlib import Path

PRIMARY = ("proc_event_count", "proc_unique_process_count", "proc_start_count")
RADIUS_SECONDS = 600


def load_pairs(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"target_index", "target_time", "target_user", "target_source_computer",
                    "target_destination_computer", "matched", "control_time", "offset_seconds"}
        for feature in PRIMARY:
            required.update((f"target_{feature}", f"control_{feature}"))
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError(f"missing columns: {sorted(required - set(reader.fieldnames or []))}")
        rows = list(reader)
    if len(rows) != 25 or [int(r["target_index"]) for r in rows] != list(range(25)):
        raise ValueError("expected exactly 25 cohort-local target indices 0..24")
    for row in rows:
        if row["matched"].lower() not in {"true", "false"}:
            raise ValueError("invalid matched flag")
        if int(row["target_time"]) < 0:
            raise ValueError("negative target time")
        if row["matched"].lower() == "true":
            if not row["control_time"] or not row["offset_seconds"]:
                raise ValueError("matched pair lacks control provenance")
            if int(row["control_time"]) - int(row["target_time"]) != int(row["offset_seconds"]):
                raise ValueError("control time/offset mismatch")
            for feature in PRIMARY:
                if min(int(row[f"target_{feature}"]), int(row[f"control_{feature}"])) < 0:
                    raise ValueError("negative count")
        else:
            if row["control_time"] or row["offset_seconds"]:
                raise ValueError("unmatched target contains control assignment")
    return rows


def verify_manifest(rows: list[dict[str, str]], manifest: dict) -> None:
    controls = manifest.get("controls")
    if not isinstance(controls, list) or len(controls) != 25:
        raise ValueError("control manifest must contain 25 targets")
    if manifest.get("label_start_zero_based") != 25 or manifest.get("target_label_count") != 25:
        raise ValueError("manifest cohort drift")
    for row, control in zip(rows, controls, strict=True):
        if int(row["target_index"]) != control["target_index"]:
            raise ValueError("manifest target index mismatch")
        if int(row["target_time"]) != control["target"]["time"]:
            raise ValueError("manifest target timestamp mismatch")
        for column, key in (("target_user", "user"), ("target_source_computer", "source_computer"),
                            ("target_destination_computer", "destination_computer")):
            if row[column] != control["target"][key]:
                raise ValueError("manifest target entity mismatch")
        if (row["matched"].lower() == "true") != control["matched"]:
            raise ValueError("manifest match status mismatch")
        if control["matched"]:
            if int(row["control_time"]) != control["control_time"] or int(row["offset_seconds"]) != control["offset_seconds"]:
                raise ValueError("manifest control assignment mismatch")


def assign_episodes(rows: list[dict[str, str]]) -> dict[int, int]:
    """Connected components of overlapping target windows, including unmatched rows."""
    ordered = sorted(rows, key=lambda r: (int(r["target_time"]), int(r["target_index"])))
    episodes = {}
    episode = -1
    last_time = None
    for row in ordered:
        t = int(row["target_time"])
        if last_time is None or t - last_time > 2 * RADIUS_SECONDS:
            episode += 1
        episodes[int(row["target_index"])] = episode
        last_time = t
    return episodes


def group_summary(rows: list[dict[str, str]], feature: str, group_for) -> dict:
    groups = collections.defaultdict(list)
    for row in rows:
        if row["matched"].lower() == "true":
            groups[str(group_for(row))].append(int(row[f"target_{feature}"]) - int(row[f"control_{feature}"]))
    medians = {key: statistics.median(vals) for key, vals in sorted(groups.items())}
    return {
        "group_count": len(groups),
        "group_sizes": {key: len(vals) for key, vals in sorted(groups.items())},
        "group_median_paired_differences": medians,
        "group_median_higher": sum(v > 0 for v in medians.values()),
        "group_median_tied": sum(v == 0 for v in medians.values()),
        "group_median_lower": sum(v < 0 for v in medians.values()),
        "leave_one_group_out": {
            key: {
                "remaining_pairs": sum(len(v) for k, v in groups.items() if k != key),
                "target_higher_pairs": sum(sum(x > 0 for x in v) for k, v in groups.items() if k != key),
                "median_paired_difference": statistics.median(
                    [x for k, v in groups.items() if k != key for x in v]
                ) if len(groups) > 1 else None,
            }
            for key in sorted(groups)
        },
    }


def audit(rows: list[dict[str, str]], input_sha256: str, manifest_sha256: str | None = None) -> dict:
    episodes = assign_episodes(rows)
    matched = [r for r in rows if r["matched"].lower() == "true"]
    features = {}
    for feature in PRIMARY:
        features[feature] = {
            "by_user": group_summary(rows, feature, lambda r: r["target_user"]),
            "by_source_host": group_summary(rows, feature, lambda r: r["target_source_computer"]),
            "by_overlapping_target_window_episode": group_summary(
                rows, feature, lambda r: episodes[int(r["target_index"])]
            ),
            "zero_coverage_controls": sum(int(r[f"control_{feature}"]) == 0 for r in matched),
        }
    return {
        "source_csv_sha256": input_sha256,
        "control_manifest_sha256": manifest_sha256,
        "frozen_target_rows_one_based": [26, 50],
        "total_targets": len(rows),
        "matched_pairs": len(matched),
        "unmatched_targets": len(rows) - len(matched),
        "distinct_target_users_all": len({r["target_user"] for r in rows}),
        "distinct_target_users_matched": len({r["target_user"] for r in matched}),
        "distinct_target_source_hosts_matched": len({r["target_source_computer"] for r in matched}),
        "overlapping_window_episodes_all": len(set(episodes.values())),
        "overlapping_window_episodes_with_matched": len({episodes[int(r["target_index"])] for r in matched}),
        "matched_control_offsets_seconds": dict(sorted(collections.Counter(int(r["offset_seconds"]) for r in matched).items())),
        "primary_feature_dependence_audit": features,
        "interpretation": "Post-hoc dependence and coverage audit, not a new preregistered test. Groups may share source hosts and temporal exposure; group counts are not independent trials. The preregistered per-pair sign-test p-values and Wilson intervals assume independent pair signs and must not be interpreted as valid population-level inferential evidence under this clustering.",
        "claim_boundary": "Matched non-red-team controls are unlabeled, not verified benign. No detection performance, causal effect, or complete device-trust validation is established.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = load_pairs(args.input)
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    verify_manifest(rows, manifest)
    result = audit(rows, hashlib.sha256(args.input.read_bytes()).hexdigest(),
                   hashlib.sha256(args.manifest.read_bytes()).hexdigest())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("matched_pairs", "unmatched_targets", "distinct_target_users_matched", "distinct_target_source_hosts_matched", "overlapping_window_episodes_with_matched")}, indent=2))


if __name__ == "__main__":
    main()
