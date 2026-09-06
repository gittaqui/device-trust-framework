"""Sweep device-trust thresholds and report per-scenario decision behavior.

Synthetic experiment only. The purpose is to expose sensitivity to the selected
ALLOW threshold and identify which scenario families dominate residual errors.
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from generate_synthetic_data import generate
from trust_model import calculate_trust

SIGNALS = (
    "compliance",
    "endpoint_health",
    "identity_assurance",
    "patch_posture",
    "security_coverage",
    "freshness",
    "threat_risk",
    "anomaly_risk",
)


def evaluate_threshold(
    input_path: Path,
    *,
    allow_threshold: float,
    step_up_threshold: float = 0.55,
) -> tuple[dict[str, float | int], dict[str, dict[str, float | int]]]:
    """Evaluate one threshold and return aggregate plus per-scenario metrics."""
    counts: Counter[str] = Counter()
    scenario_counts: dict[str, Counter[str]] = defaultdict(Counter)

    with input_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            safe = row["safe_for_ordinary_access"] == "1"
            scenario = row["scenario"]
            signals = {name: float(row[name]) for name in SIGNALS}
            decision = calculate_trust(
                signals,
                allow_threshold=allow_threshold,
                step_up_threshold=step_up_threshold,
            ).decision

            counts["safe" if safe else "unsafe"] += 1
            counts[decision] += 1
            scenario_counts[scenario]["n"] += 1
            scenario_counts[scenario][decision] += 1

            if not safe and decision == "ALLOW":
                counts["false_allow"] += 1
                scenario_counts[scenario]["false_allow"] += 1
            if safe and decision == "DENY":
                counts["false_deny"] += 1
                scenario_counts[scenario]["false_deny"] += 1
            if safe and decision == "STEP_UP":
                counts["safe_step_up"] += 1
            if safe and decision == "ALLOW":
                counts["safe_allow"] += 1

    aggregate: dict[str, float | int] = {
        "allow_threshold": allow_threshold,
        "step_up_threshold": step_up_threshold,
        "safe": counts["safe"],
        "unsafe": counts["unsafe"],
        "false_allow_rate": counts["false_allow"] / counts["unsafe"],
        "false_deny_rate": counts["false_deny"] / counts["safe"],
        "safe_step_up_rate": counts["safe_step_up"] / counts["safe"],
        "safe_allow_rate": counts["safe_allow"] / counts["safe"],
    }

    per_scenario: dict[str, dict[str, float | int]] = {}
    for scenario, values in sorted(scenario_counts.items()):
        n = values["n"]
        per_scenario[scenario] = {
            "n": n,
            "allow_rate": values["ALLOW"] / n,
            "step_up_rate": values["STEP_UP"] / n,
            "deny_rate": values["DENY"] / n,
            "false_allow_rate": values["false_allow"] / n,
            "false_deny_rate": values["false_deny"] / n,
        }

    return aggregate, per_scenario


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=50_000)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/synthetic_endpoints.csv"),
    )
    parser.add_argument("--start", type=float, default=0.60)
    parser.add_argument("--stop", type=float, default=0.90)
    parser.add_argument("--step", type=float, default=0.01)
    parser.add_argument("--step-up-threshold", type=float, default=0.55)
    args = parser.parse_args()

    if not args.input.exists():
        generate(args.rows, args.input, seed=20260903)

    threshold = args.start
    print(
        "allow_threshold,false_allow,false_deny,safe_step_up,safe_allow"
    )
    while threshold <= args.stop + 1e-9:
        aggregate, _ = evaluate_threshold(
            args.input,
            allow_threshold=round(threshold, 6),
            step_up_threshold=args.step_up_threshold,
        )
        print(
            f"{threshold:.2f},"
            f"{aggregate['false_allow_rate']:.6f},"
            f"{aggregate['false_deny_rate']:.6f},"
            f"{aggregate['safe_step_up_rate']:.6f},"
            f"{aggregate['safe_allow_rate']:.6f}"
        )
        threshold += args.step

    print("\nPer-scenario decisions at selected thresholds")
    print(
        "allow_threshold,scenario,n,allow_rate,step_up_rate,deny_rate,"
        "false_allow_rate,false_deny_rate"
    )
    for selected in (0.75, 0.80, 0.85):
        _, scenarios = evaluate_threshold(
            args.input,
            allow_threshold=selected,
            step_up_threshold=args.step_up_threshold,
        )
        for scenario, metrics in scenarios.items():
            print(
                f"{selected:.2f},{scenario},{metrics['n']},"
                f"{metrics['allow_rate']:.6f},"
                f"{metrics['step_up_rate']:.6f},"
                f"{metrics['deny_rate']:.6f},"
                f"{metrics['false_allow_rate']:.6f},"
                f"{metrics['false_deny_rate']:.6f}"
            )


if __name__ == "__main__":
    main()
