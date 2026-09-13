"""Compare additive/guarded trust with an attribute-quorum baseline.

The quorum baseline is literature-inspired by trust-score Zero Trust work that
combines an aggregate trust threshold with minimum per-attribute evidence. It is
an exploratory comparator, not a reproduction of another paper's implementation.
"""

from __future__ import annotations

import argparse
import random
from dataclasses import dataclass

from generate_synthetic_data import generate_row
from trust_model import calculate_trust


@dataclass(frozen=True)
class QuorumPolicy:
    allow_threshold: float = 0.75
    step_up_threshold: float = 0.55
    signal_threshold: float = 0.70
    min_passing_signals: int = 7


def safety_factors(signals: dict[str, float]) -> tuple[float, ...]:
    """Return eight normalized factors in the same safe-is-high direction."""
    return (
        signals["compliance"],
        signals["endpoint_health"],
        signals["identity_assurance"],
        signals["patch_posture"],
        signals["security_coverage"],
        signals["freshness"],
        1.0 - signals["threat_risk"],
        1.0 - signals["anomaly_risk"],
    )


def quorum_decision(
    signals: dict[str, float],
    *,
    policy: QuorumPolicy = QuorumPolicy(),
) -> str:
    """Require both aggregate trust and a minimum quorum of strong factors."""
    if not 1 <= policy.min_passing_signals <= 8:
        raise ValueError("min_passing_signals must be between 1 and 8.")
    if not 0.0 <= policy.signal_threshold <= 1.0:
        raise ValueError("signal_threshold must be in [0, 1].")

    base = calculate_trust(
        signals,
        allow_threshold=policy.allow_threshold,
        step_up_threshold=policy.step_up_threshold,
    )
    if base.decision == "DENY":
        return "DENY"

    passing = sum(
        value >= policy.signal_threshold for value in safety_factors(signals)
    )
    if base.decision == "ALLOW" and passing >= policy.min_passing_signals:
        return "ALLOW"
    return "STEP_UP"


def _signals(row: dict[str, object]) -> dict[str, float]:
    names = (
        "compliance",
        "endpoint_health",
        "identity_assurance",
        "patch_posture",
        "security_coverage",
        "freshness",
        "threat_risk",
        "anomaly_risk",
    )
    return {name: float(row[name]) for name in names}


def evaluate(
    *,
    rows: int = 50_000,
    seed: int = 20260903,
    signal_threshold: float = 0.70,
    min_passing_signals: int = 7,
) -> dict[str, object]:
    """Evaluate one quorum configuration on the seeded synthetic population."""
    rng = random.Random(seed)
    policy = QuorumPolicy(
        signal_threshold=signal_threshold,
        min_passing_signals=min_passing_signals,
    )
    totals = {
        "safe": 0,
        "unsafe": 0,
        "false_allow": 0,
        "safe_step_up": 0,
        "safe_deny": 0,
    }
    by_scenario: dict[str, dict[str, int]] = {}

    for row_id in range(1, rows + 1):
        row = generate_row(rng, row_id)
        signals = _signals(row)
        decision = quorum_decision(signals, policy=policy)
        safe = bool(int(row["safe_for_ordinary_access"]))
        scenario = str(row["scenario"])

        totals["safe" if safe else "unsafe"] += 1
        if not safe and decision == "ALLOW":
            totals["false_allow"] += 1
        if safe and decision == "STEP_UP":
            totals["safe_step_up"] += 1
        if safe and decision == "DENY":
            totals["safe_deny"] += 1

        bucket = by_scenario.setdefault(
            scenario, {"ALLOW": 0, "STEP_UP": 0, "DENY": 0, "rows": 0}
        )
        bucket[decision] += 1
        bucket["rows"] += 1

    summary = {
        **totals,
        "false_allow_rate": totals["false_allow"] / totals["unsafe"],
        "safe_step_up_rate": totals["safe_step_up"] / totals["safe"],
        "safe_deny_rate": totals["safe_deny"] / totals["safe"],
    }
    return {"summary": summary, "by_scenario": by_scenario}


def sweep(
    *,
    rows: int = 50_000,
    seed: int = 20260903,
) -> list[dict[str, float | int]]:
    """Sweep transparent quorum hyperparameters without fitting to external data."""
    output = []
    for signal_threshold in (0.60, 0.70, 0.75):
        for min_passing_signals in (5, 6, 7):
            result = evaluate(
                rows=rows,
                seed=seed,
                signal_threshold=signal_threshold,
                min_passing_signals=min_passing_signals,
            )["summary"]
            output.append(
                {
                    "signal_threshold": signal_threshold,
                    "min_passing_signals": min_passing_signals,
                    "false_allow_rate": result["false_allow_rate"],
                    "safe_step_up_rate": result["safe_step_up_rate"],
                    "safe_deny_rate": result["safe_deny_rate"],
                }
            )
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=50_000)
    parser.add_argument("--seed", type=int, default=20260903)
    args = parser.parse_args()

    print("Attribute-Quorum Baseline Sensitivity")
    print("=" * 37)
    for result in sweep(rows=args.rows, seed=args.seed):
        print(
            f"q={result['signal_threshold']:.2f} "
            f"k={result['min_passing_signals']} "
            f"false_allow={result['false_allow_rate']:.2%} "
            f"safe_step_up={result['safe_step_up_rate']:.2%} "
            f"safe_deny={result['safe_deny_rate']:.2%}"
        )


if __name__ == "__main__":
    main()
