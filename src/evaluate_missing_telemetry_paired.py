"""Paired missing-telemetry policy audit; synthetic data only.

Unlike the legacy experiment, each observation/mask is shared by all policies.
No operational access-control code is changed by this research script.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import random
from collections import Counter
from pathlib import Path

from evaluate_missing_telemetry import (
    SIGNAL_TO_FACTOR, STRATEGY_IDS, decide_partial, mask_signals,
)


def _validate_row(row: dict[str, str]) -> tuple[bool, str, dict[str, float]]:
    label = row.get("safe_for_ordinary_access")
    if label not in {"0", "1"}:
        raise ValueError("safe_for_ordinary_access must be 0 or 1")
    signals: dict[str, float] = {}
    for name in SIGNAL_TO_FACTOR:
        if row.get(name) is None or row[name] == "":
            raise ValueError(f"Missing required synthetic input: {name}")
        value = float(row[name])
        if not math.isfinite(value) or not 0 <= value <= 1:
            raise ValueError(f"Invalid synthetic input: {name}")
        signals[name] = value
    return label == "1", row.get("scenario", "unclassified"), signals


def audit(
    input_path: Path, *, missing_rate: float, structured: bool, seed: int = 20260904
) -> dict:
    """Run all strategies on the *same* masked rows and return auditable counts.

    RNG stream is independent of strategy name. A separate stream is used for
    each missingness regime and rate; results are paired *within* a regime/rate.
    """
    if not math.isfinite(missing_rate) or not 0 <= missing_rate <= 1:
        raise ValueError("missing_rate must be finite and within [0,1]")
    rng = random.Random(
        seed + round(missing_rate * 1_000_000) * 17 + (1_000_000_000 if structured else 0)
    )
    strategies = tuple(STRATEGY_IDS)
    counts = {strategy: Counter() for strategy in strategies}
    disagreements = {strategy: Counter() for strategy in strategies if strategy != "renormalize"}
    n_safe = n_unsafe = n = 0
    masked_cells = total_cells = 0
    scenario_counts: Counter[str] = Counter()
    with input_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            safe, scenario, signals = _validate_row(row)
            masked = mask_signals(signals, rng, missing_rate, structured=structured)
            total_cells += len(signals)
            masked_cells += len(signals) - len(masked)
            n += 1
            n_safe += int(safe)
            n_unsafe += int(not safe)
            scenario_counts[scenario] += 1
            decisions = {}
            for strategy in strategies:
                _, decision, _ = decide_partial(masked, strategy)
                decisions[strategy] = decision
                counts[strategy][decision] += 1
                if not safe and decision == "ALLOW":
                    counts[strategy]["false_allow"] += 1
                if safe and decision == "DENY":
                    counts[strategy]["false_deny"] += 1
                if safe and decision == "STEP_UP":
                    counts[strategy]["safe_step_up"] += 1
                if safe and decision == "ALLOW":
                    counts[strategy]["safe_allow"] += 1
            for strategy in disagreements:
                if decisions[strategy] != decisions["renormalize"]:
                    disagreements[strategy]["different_decisions"] += 1
                if decisions[strategy] == "ALLOW" and decisions["renormalize"] != "ALLOW":
                    disagreements[strategy]["strategy_only_allow"] += 1
                if decisions["renormalize"] == "ALLOW" and decisions[strategy] != "ALLOW":
                    disagreements[strategy]["reference_only_allow"] += 1
            if decisions["confidence"] != decisions["pessimistic"]:
                raise AssertionError("Algebraically equivalent policies disagreed")
    if n == 0 or n_safe == 0 or n_unsafe == 0:
        raise ValueError("Evaluation needs at least one safe and one unsafe row")
    return {
        "evidence_type": "synthetic-only",
        "input_rows": n,
        "safe_rows": n_safe,
        "unsafe_rows": n_unsafe,
        "mask_model": "critical_signal_biased" if structured else "mcar",
        "nominal_missing_rate": missing_rate,
        "observed_missing_fraction": masked_cells / total_cells,
        "seed": seed,
        "scenario_counts": dict(sorted(scenario_counts.items())),
        "strategies": {
            s: {
                "false_allow_count": counts[s]["false_allow"],
                "false_allow_rate": counts[s]["false_allow"] / n_unsafe,
                "false_deny_count": counts[s]["false_deny"],
                "false_deny_rate": counts[s]["false_deny"] / n_safe,
                "safe_step_up_count": counts[s]["safe_step_up"],
                "safe_step_up_rate": counts[s]["safe_step_up"] / n_safe,
                "safe_allow_count": counts[s]["safe_allow"],
                "safe_allow_rate": counts[s]["safe_allow"] / n_safe,
                "decision_counts": {d: counts[s][d] for d in ("ALLOW", "STEP_UP", "DENY")},
                "paired_vs_renormalize": dict(disagreements.get(s, {})),
            }
            for s in strategies
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--missing-rate", type=float, default=0.25)
    parser.add_argument("--structured", action="store_true")
    parser.add_argument("--seed", type=int, default=20260904)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(args.input, missing_rate=args.missing_rate, structured=args.structured, seed=args.seed)
    output = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output, end="")


if __name__ == "__main__":
    main()
