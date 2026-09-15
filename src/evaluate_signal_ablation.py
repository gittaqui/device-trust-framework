"""Leave-one-signal-out ablation for the synthetic Device Trust experiment.

This experiment measures decision sensitivity to each weighted factor. It does not
estimate causal importance or real-world feature importance.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from trust_model import DEFAULT_WEIGHTS, calculate_trust

SIGNALS = [
    "compliance", "endpoint_health", "identity_assurance", "patch_posture",
    "security_coverage", "freshness", "threat_safety", "anomaly_safety",
]
RAW_SIGNALS = [
    "compliance", "endpoint_health", "identity_assurance", "patch_posture",
    "security_coverage", "freshness", "threat_risk", "anomaly_risk",
]


def ablated_weights(drop: str) -> dict[str, float]:
    """Remove one weighted factor; calculate_trust renormalizes the remainder."""
    if drop not in DEFAULT_WEIGHTS:
        raise ValueError(f"Unknown factor: {drop}")
    return {name: value for name, value in DEFAULT_WEIGHTS.items() if name != drop}


def evaluate_rows(rows: list[dict[str, str]], drop: str | None = None) -> dict[str, float]:
    weights = DEFAULT_WEIGHTS if drop is None else ablated_weights(drop)
    safe = unsafe = false_allow = safe_step_up = safe_deny = 0
    scenario_false_allow: dict[str, list[int]] = {}

    for row in rows:
        signals = {name: float(row[name]) for name in RAW_SIGNALS}
        is_safe = row["safe_for_ordinary_access"] == "1"
        decision = calculate_trust(signals, weights=weights).decision
        scenario = row["scenario"]

        if is_safe:
            safe += 1
            safe_step_up += decision == "STEP_UP"
            safe_deny += decision == "DENY"
        else:
            unsafe += 1
            false_allow += decision == "ALLOW"
            bucket = scenario_false_allow.setdefault(scenario, [0, 0])
            bucket[1] += 1
            bucket[0] += decision == "ALLOW"

    return {
        "false_allow_rate": false_allow / unsafe,
        "safe_step_up_rate": safe_step_up / safe,
        "safe_deny_rate": safe_deny / safe,
        "scenario_false_allow": {
            scenario: allowed / total for scenario, (allowed, total) in scenario_false_allow.items()
        },
    }


def evaluate(input_path: Path) -> tuple[dict[str, float], list[tuple[str, dict[str, float]]]]:
    with input_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    baseline = evaluate_rows(rows)
    ablations = [(factor, evaluate_rows(rows, factor)) for factor in SIGNALS]
    return baseline, ablations


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("data/synthetic_endpoints.csv"))
    args = parser.parse_args()
    baseline, ablations = evaluate(args.input)
    print("Signal ablation: synthetic data only")
    print(f"baseline false ALLOW={baseline['false_allow_rate']:.4%}, safe STEP_UP={baseline['safe_step_up_rate']:.4%}")
    for factor, result in ablations:
        delta_fa = result["false_allow_rate"] - baseline["false_allow_rate"]
        delta_su = result["safe_step_up_rate"] - baseline["safe_step_up_rate"]
        print(f"{factor:20s} false ALLOW={result['false_allow_rate']:.4%} ({delta_fa:+.4%}), "
              f"safe STEP_UP={result['safe_step_up_rate']:.4%} ({delta_su:+.4%})")


if __name__ == "__main__":
    main()
