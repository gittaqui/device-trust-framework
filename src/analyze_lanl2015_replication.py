"""Predeclared sign-test analysis of frozen LANL-2015 paired process counts.

No classifier performance is inferred: matched non-red-team controls are unlabeled,
not verified benign. No normality assumption, p-hacking or outcome-driven threshold.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from pathlib import Path

PRIMARY_FEATURES = (
    "proc_event_count", "proc_unique_process_count", "proc_start_count",
)
Z_975 = 1.959963984540054


def wilson_95(successes: int, trials: int) -> list[float] | None:
    if not (0 <= successes <= trials):
        raise ValueError("invalid successes/trials")
    if trials == 0:
        return None
    z2 = Z_975 * Z_975
    p = successes / trials
    denominator = 1 + z2 / trials
    center = (p + z2 / (2 * trials)) / denominator
    radius = Z_975 * math.sqrt(
        p * (1 - p) / trials + z2 / (4 * trials * trials)
    ) / denominator
    return [max(0.0, center - radius), min(1.0, center + radius)]


def exact_two_sided_sign_pvalue(higher: int, lower: int) -> float | None:
    if higher < 0 or lower < 0:
        raise ValueError("negative pair count")
    n = higher + lower
    if n == 0:
        return None
    tail = sum(math.comb(n, i) for i in range(min(higher, lower) + 1))
    return min(1.0, 2.0 * tail / (2 ** n))


def summarize_feature(target: list[int], control: list[int]) -> dict:
    if len(target) != len(control):
        raise ValueError("target/control arrays differ in length")
    diffs = [a - b for a, b in zip(target, control, strict=True)]
    higher = sum(d > 0 for d in diffs)
    lower = sum(d < 0 for d in diffs)
    ties = sum(d == 0 for d in diffs)
    non_ties = higher + lower
    return {
        "matched_pairs": len(diffs),
        "target_median": statistics.median(target) if target else None,
        "control_median": statistics.median(control) if control else None,
        "median_paired_difference": statistics.median(diffs) if diffs else None,
        "target_higher_pairs": higher,
        "tied_pairs": ties,
        "control_higher_pairs": lower,
        "non_tied_pairs": non_ties,
        "target_higher_fraction_of_non_ties": higher / non_ties if non_ties else None,
        "target_higher_wilson_95": wilson_95(higher, non_ties),
        "exact_two_sided_sign_p": exact_two_sided_sign_pvalue(higher, lower),
    }


def analyze_csv(path: Path) -> dict:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError("missing CSV header")
        required = {"target_index", "matched"}
        for feature in PRIMARY_FEATURES:
            required |= {f"target_{feature}", f"control_{feature}"}
        missing = required - set(reader.fieldnames)
        if missing:
            raise ValueError(f"missing required columns: {sorted(missing)}")
        rows = list(reader)
    if len(rows) != 25:
        raise ValueError(f"frozen replication requires exactly 25 rows, got {len(rows)}")
    if [int(row["target_index"]) for row in rows] != list(range(25)):
        raise ValueError("unexpected cohort-local target indices")
    targets: dict[str, list[int]] = {key: [] for key in PRIMARY_FEATURES}
    controls: dict[str, list[int]] = {key: [] for key in PRIMARY_FEATURES}
    unmatched = 0
    for row in rows:
        if row["matched"].strip().lower() not in {"true", "false"}:
            raise ValueError("unrecognized matched flag")
        if row["matched"].strip().lower() == "false":
            unmatched += 1
            continue
        for feature in PRIMARY_FEATURES:
            try:
                a, b = int(row[f"target_{feature}"]), int(row[f"control_{feature}"])
            except (ValueError, TypeError) as exc:
                raise ValueError(f"noninteger or missing paired feature {feature}") from exc
            if min(a, b) < 0:
                raise ValueError(f"negative count for {feature}")
            targets[feature].append(a)
            controls[feature].append(b)
    return {
        "analysis_protocol": "experiments/lanl-2015-second-cohort-replication-freeze.md",
        "dataset_doi": "10.17021/1179829",
        "target_label_rows_one_based": [26, 50],
        "total_frozen_targets": 25,
        "matched_pairs": len(rows) - unmatched,
        "unmatched_targets": unmatched,
        "primary_feature_family": {
            key: summarize_feature(targets[key], controls[key])
            for key in PRIMARY_FEATURES
        },
        "multiple_testing_caveat": "Three correlated process features form one replication family; per-feature p-values are descriptive and not independent discoveries.",
        "claim_boundary": "Unlabeled matched controls are not verified benign. These paired contextual process-count comparisons cannot establish sensitivity, specificity, false-positive rate, ROC/AUC, causal effect, or full device-trust model accuracy.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("data/external/lanl-2015/replication-paired-features.csv"))
    parser.add_argument("--output", type=Path, default=Path("results/lanl-2015-replication-statistics.json"))
    args = parser.parse_args()
    result = analyze_csv(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
