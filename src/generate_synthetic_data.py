"""Generate reproducible synthetic endpoint-session data."""

from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path


SCENARIOS = {
    "healthy": {
        "safe": 1,
        "ranges": {
            "compliance": (0.85, 1.0),
            "endpoint_health": (0.82, 1.0),
            "identity_assurance": (0.85, 1.0),
            "patch_posture": (0.80, 1.0),
            "security_coverage": (0.90, 1.0),
            "freshness": (0.85, 1.0),
            "threat_risk": (0.0, 0.12),
            "anomaly_risk": (0.0, 0.15),
        },
    },
    "policy_drift": {
        "safe": 1,
        "ranges": {
            "compliance": (0.0, 0.35),
            "endpoint_health": (0.75, 0.95),
            "identity_assurance": (0.85, 1.0),
            "patch_posture": (0.65, 0.90),
            "security_coverage": (0.85, 1.0),
            "freshness": (0.80, 1.0),
            "threat_risk": (0.0, 0.15),
            "anomaly_risk": (0.0, 0.15),
        },
    },
    "stale": {
        "safe": 0,
        "ranges": {
            "compliance": (0.75, 1.0),
            "endpoint_health": (0.55, 0.80),
            "identity_assurance": (0.70, 0.95),
            "patch_posture": (0.35, 0.65),
            "security_coverage": (0.60, 0.90),
            "freshness": (0.05, 0.30),
            "threat_risk": (0.15, 0.35),
            "anomaly_risk": (0.10, 0.35),
        },
    },
    "identity_risk": {
        "safe": 0,
        "ranges": {
            "compliance": (0.85, 1.0),
            "endpoint_health": (0.80, 1.0),
            "identity_assurance": (0.05, 0.35),
            "patch_posture": (0.80, 1.0),
            "security_coverage": (0.90, 1.0),
            "freshness": (0.80, 1.0),
            "threat_risk": (0.10, 0.30),
            "anomaly_risk": (0.55, 0.90),
        },
    },
    "malware": {
        "safe": 0,
        "ranges": {
            "compliance": (0.75, 1.0),
            "endpoint_health": (0.10, 0.45),
            "identity_assurance": (0.75, 1.0),
            "patch_posture": (0.55, 0.90),
            "security_coverage": (0.65, 1.0),
            "freshness": (0.75, 1.0),
            "threat_risk": (0.90, 1.0),
            "anomaly_risk": (0.65, 1.0),
        },
    },
    "protection_missing": {
        "safe": 0,
        "ranges": {
            "compliance": (0.60, 0.95),
            "endpoint_health": (0.45, 0.75),
            "identity_assurance": (0.80, 1.0),
            "patch_posture": (0.55, 0.85),
            "security_coverage": (0.0, 0.15),
            "freshness": (0.65, 0.95),
            "threat_risk": (0.20, 0.55),
            "anomaly_risk": (0.20, 0.55),
        },
    },
    "mixed_degradation": {
        "safe": 0,
        "ranges": {
            "compliance": (0.35, 0.75),
            "endpoint_health": (0.35, 0.70),
            "identity_assurance": (0.45, 0.75),
            "patch_posture": (0.25, 0.65),
            "security_coverage": (0.45, 0.80),
            "freshness": (0.25, 0.60),
            "threat_risk": (0.35, 0.70),
            "anomaly_risk": (0.35, 0.75),
        },
    },
    "adversarial_compliant": {
        "safe": 0,
        "ranges": {
            "compliance": (0.90, 1.0),
            "endpoint_health": (0.45, 0.75),
            "identity_assurance": (0.35, 0.70),
            "patch_posture": (0.80, 1.0),
            "security_coverage": (0.80, 1.0),
            "freshness": (0.80, 1.0),
            "threat_risk": (0.55, 0.88),
            "anomaly_risk": (0.60, 0.95),
        },
    },
}

SCENARIO_WEIGHTS = [
    ("healthy", 0.50),
    ("policy_drift", 0.08),
    ("stale", 0.08),
    ("identity_risk", 0.08),
    ("malware", 0.07),
    ("protection_missing", 0.06),
    ("mixed_degradation", 0.07),
    ("adversarial_compliant", 0.06),
]


def choose_scenario(rng: random.Random) -> str:
    names = [name for name, _ in SCENARIO_WEIGHTS]
    weights = [weight for _, weight in SCENARIO_WEIGHTS]
    return rng.choices(names, weights=weights, k=1)[0]


def generate_row(rng: random.Random, row_id: int) -> dict[str, object]:
    scenario_name = choose_scenario(rng)
    scenario = SCENARIOS[scenario_name]

    row = {
        "id": row_id,
        "scenario": scenario_name,
        "safe_for_ordinary_access": scenario["safe"],
    }
    for signal, (low, high) in scenario["ranges"].items():
        row[signal] = round(rng.uniform(low, high), 6)
    return row


def generate(rows: int, output: Path, seed: int = 20260903) -> None:
    rng = random.Random(seed)
    output.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "id", "scenario", "safe_for_ordinary_access",
        "compliance", "endpoint_health", "identity_assurance",
        "patch_posture", "security_coverage", "freshness",
        "threat_risk", "anomaly_risk",
    ]

    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row_id in range(1, rows + 1):
            writer.writerow(generate_row(rng, row_id))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=50_000)
    parser.add_argument("--output", type=Path, default=Path("data/synthetic_endpoints.csv"))
    parser.add_argument("--seed", type=int, default=20260903)
    args = parser.parse_args()

    generate(args.rows, args.output, args.seed)
    print(f"Generated {args.rows:,} rows at {args.output}")


if __name__ == "__main__":
    main()
