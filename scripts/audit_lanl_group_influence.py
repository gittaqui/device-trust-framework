"""Frozen LANL second-cohort leave-one-group-out descriptive influence audit.

Inputs are PUBLIC, de-identified LANL enterprise telemetry. Temporal controls are
unlabeled; this audit is NOT a device-trust classifier evaluation or significance test.
No source user/computer identifiers are written to the summary.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

PAIR_SHA256 = "6dfe2e18ed65d2f54d6a73ce5cb8b9848b0ecdf78e3fd36bbf469a52396f14db"
MANIFEST_SHA256 = "190190ac1b75495fdfb18422da8b727bdac88553852edba8d236fb3d544957ff"
FEATURES = ("proc_event_count", "proc_unique_process_count", "proc_start_count")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _nonnegative_int(value: str) -> int:
    if not value or value.strip() != value:
        raise ValueError("missing or malformed integer count")
    v = int(value)
    if v < 0:
        raise ValueError("negative process count")
    return v


def read_frozen(pairs: Path, manifest: Path) -> list[dict[str, str]]:
    if sha256(pairs) != PAIR_SHA256 or sha256(manifest) != MANIFEST_SHA256:
        raise ValueError("frozen evidence hash mismatch")
    with pairs.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        required = {"target_index", "target_time", "target_user", "target_source_computer", "target_destination_computer", "matched", "control_time", "offset_seconds"}
        for f in FEATURES:
            required.update((f"target_{f}", f"control_{f}"))
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError("missing required CSV columns")
        rows = list(reader)
    m = json.loads(manifest.read_text(encoding="utf-8"))
    controls = m.get("controls")
    if (len(rows) != 25 or not isinstance(controls, list) or len(controls) != 25
            or m.get("label_start_zero_based") != 25 or m.get("target_label_count") != 25
            or m.get("radius_seconds") != 600):
        raise ValueError("unexpected frozen cohort or manifest")
    if sum(r["matched"] == "True" for r in rows) != m.get("matched_count") or sum(r["matched"] == "False" for r in rows) != m.get("unmatched_count"):
        raise ValueError("matched coverage disagrees with manifest")
    for i, (row, control) in enumerate(zip(rows, controls, strict=True)):
        if int(row["target_index"]) != i or control["target_index"] != i:
            raise ValueError("target index mismatch")
        if row["matched"] not in ("True", "False") or control["matched"] != (row["matched"] == "True"):
            raise ValueError("match flag mismatch")
        target = control["target"]
        if (row["target_user"] != target["user"] or row["target_source_computer"] != target["source_computer"]
                or row["target_destination_computer"] != target["destination_computer"] or int(row["target_time"]) != target["time"]):
            raise ValueError("target identity mismatch")
        for f in FEATURES:
            _nonnegative_int(row[f"target_{f}"])
        if row["matched"] == "True":
            offset = int(row["offset_seconds"])
            if (offset not in m["candidate_offsets_seconds"] or int(row["control_time"]) - int(row["target_time"]) != offset
                    or control["control_time"] != int(row["control_time"]) or control["offset_seconds"] != offset):
                raise ValueError("control assignment mismatch")
            for f in FEATURES:
                _nonnegative_int(row[f"control_{f}"])
        elif row["control_time"] or row["offset_seconds"] or any(row[f"control_{f}"] for f in FEATURES):
            raise ValueError("unmatched target has unexpected control")
    return rows


def episodes(rows: list[dict[str, str]], radius_seconds: int = 600) -> dict[str, int]:
    """Assign episodes using gaps >2*radius in time-sorted targets.

    Grouping is post-hoc and intentionally ignores entity identities; it is not
    claimed to recover independent incident units.
    """
    if radius_seconds < 0:
        raise ValueError("negative radius")
    ordered = sorted(rows, key=lambda r: (int(r["target_time"]), int(r["target_index"])))
    labels: dict[str, int] = {}
    episode = -1
    last: int | None = None
    for row in ordered:
        t = int(row["target_time"])
        if last is None or t - last > 2 * radius_seconds:
            episode += 1
        labels[row["target_index"]] = episode
        last = t
    return labels


def leave_one_group_out(rows: list[dict[str, str]], feature: str, group_by: str, episode_labels: dict[str, int]) -> dict:
    if feature not in FEATURES or group_by not in ("user", "source_host", "episode"):
        raise ValueError("invalid feature or grouping")
    matched = [r for r in rows if r["matched"] == "True"]
    if not matched:
        raise ValueError("no matched observations")
    groups: dict[str | int, list[dict[str, str]]] = defaultdict(list)
    for r in matched:
        key = {"user": r["target_user"], "source_host": r["target_source_computer"], "episode": episode_labels[r["target_index"]]}[group_by]
        groups[key].append(r)
    if len(groups) < 2:
        raise ValueError("cannot omit the only group")
    rates = []
    for key, omitted in groups.items():
        remaining = [r for r in matched if r not in omitted]
        n = len(remaining)
        if not n:
            raise ValueError("empty leave-one-group-out subset")
        higher = sum(_nonnegative_int(r[f"target_{feature}"]) > _nonnegative_int(r[f"control_{feature}"]) for r in remaining)
        rates.append({"remaining": n, "higher": higher, "rate": higher / n})
    return {"groups": len(groups), "group_sizes": sorted(len(v) for v in groups.values()),
            "min_rate": min(x["rate"] for x in rates), "max_rate": max(x["rate"] for x in rates),
            "min_fraction": min(rates, key=lambda x: x["rate"]), "max_fraction": max(rates, key=lambda x: x["rate"])}


def analyze(rows: list[dict[str, str]]) -> dict:
    indices = [int(r["target_index"]) for r in rows]
    if len(rows) != 25 or sorted(indices) != list(range(25)):
        raise ValueError("requires 25 unique target indices")
    if any(r["matched"] not in ("True", "False") for r in rows):
        raise ValueError("invalid match flag")
    matched = [r for r in rows if r["matched"] == "True"]
    if len(matched) != 18:
        raise ValueError("unexpected frozen matched coverage")
    eps = episodes(rows)
    result = {"total_targets": 25, "matched": 18, "unmatched": 7,
              "matched_users": len({r["target_user"] for r in matched}),
              "matched_source_hosts": len({r["target_source_computer"] for r in matched}),
              "episodes_all_targets": len(set(eps.values())), "features": {}}
    for f in FEATURES:
        higher = sum(_nonnegative_int(r[f"target_{f}"]) > _nonnegative_int(r[f"control_{f}"]) for r in matched)
        result["features"][f] = {"matched_target_higher": higher, "matched_n": 18,
                                 "leave_one_user_out": leave_one_group_out(rows, f, "user", eps),
                                 "leave_one_source_host_out": leave_one_group_out(rows, f, "source_host", eps),
                                 "leave_one_episode_out": leave_one_group_out(rows, f, "episode", eps)}
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pairs", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = analyze(read_frozen(args.pairs, args.manifest))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote descriptive group-influence audit: {args.output}")


if __name__ == "__main__":
    main()
