"""Partial-identification sensitivity to unmatched LANL second-cohort controls.

The 25 red-team target rows were frozen before outcome telemetry inspection.
Unmatched control outcomes are unknown, NOT negative/benign observations.
Bounds here are deterministic logical bounds on the 25 *selected* targets,
not confidence intervals, model accuracy, or population-level inference.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
from pathlib import Path

from audit_lanl2015_replication_dependence import PRIMARY, load_pairs, verify_manifest


def matching_bounds(rows: list[dict[str, str]]) -> dict:
    if len(rows) != 25 or [int(r["target_index"]) for r in rows] != list(range(25)):
        raise ValueError("expected exactly the 25 frozen cohort-local targets")
    for row in rows:
        if row["matched"].lower() not in {"true", "false"}:
            raise ValueError("unrecognized matched flag")

    matched = [r for r in rows if r["matched"].lower() == "true"]
    unmatched = [r for r in rows if r["matched"].lower() == "false"]
    n = len(rows)
    summaries = {}
    for feature in PRIMARY:
        higher = tied = lower = 0
        for row in matched:
            target = int(row[f"target_{feature}"])
            control = int(row[f"control_{feature}"])
            if min(target, control) < 0:
                raise ValueError("counts must be nonnegative")
            higher += target > control
            tied += target == control
            lower += target < control
        missing_positive = 0
        missing_zero = 0
        for row in unmatched:
            target = int(row[f"target_{feature}"])
            if target < 0:
                raise ValueError("counts must be nonnegative")
            missing_positive += target > 0
            missing_zero += target == 0
        # A missing nonnegative control can be smaller than a positive target,
        # but cannot be smaller than a target of zero. Both endpoints attainable.
        summaries[feature] = {
            "matched_target_higher": higher,
            "matched_tied": tied,
            "matched_control_higher": lower,
            "unmatched_target_positive": missing_positive,
            "unmatched_target_zero": missing_zero,
            "selected_cohort_target_higher_fraction_lower": higher / n,
            "selected_cohort_target_higher_fraction_upper": (higher + missing_positive) / n,
            "assumptions": "Only nonnegative integer control counts; no missing-at-random assumption or imputation.",
        }

    coverage = {}
    for field in ("target_user", "target_source_computer"):
        groups = collections.defaultdict(lambda: [0, 0])
        for row in rows:
            groups[row[field]][0] += 1
            groups[row[field]][1] += row["matched"].lower() == "true"
        coverage[field] = {
            "group_count": len(groups),
            "groups_with_no_matched_controls": sum(m == 0 for n_total, m in groups.values()),
            "groups": {key: {"targets": total, "matched": m, "unmatched": total - m}
                       for key, (total, m) in sorted(groups.items())},
        }

    return {
        "cohort_rows_one_based": [26, 50],
        "selected_targets": n,
        "matched_controls": len(matched),
        "unmatched_controls": len(unmatched),
        "matching_rate": len(matched) / n,
        "feature_bounds": summaries,
        "matching_coverage_by_entity": coverage,
        "scope": "Sharp finite-cohort bounds for directional comparisons under nonnegative control counts; not a statistical confidence interval, attack-detection accuracy, or estimate for other enterprise populations.",
        "limitations": "Unmatched controls may be systematically different; the selected labels share users, hosts and temporal windows. The analysis cannot bound paired-difference magnitudes without a justified upper bound on missing control counts.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    rows = load_pairs(args.input)
    verify_manifest(rows, json.loads(args.manifest.read_text(encoding="utf-8")))
    result = matching_bounds(rows)
    result["paired_csv_sha256"] = hashlib.sha256(args.input.read_bytes()).hexdigest()
    result["control_manifest_sha256"] = hashlib.sha256(args.manifest.read_bytes()).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"matching_rate": result["matching_rate"], "feature_bounds": result["feature_bounds"]}, indent=2))


if __name__ == "__main__":
    main()
