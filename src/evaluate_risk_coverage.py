"""Risk-coverage analysis for ordinary ALLOW decisions.

This experiment interprets STEP_UP/DENY as non-ordinary-access outcomes and measures
the trade-off between ordinary-access coverage and unsafe ALLOW risk as the ALLOW
threshold varies. All labels are synthetic scenario labels; results are not estimates
of production security performance.
"""

from __future__ import annotations

import argparse
import random

from generate_synthetic_data import generate_row
from trust_model import calculate_trust

DEFAULT_THRESHOLDS = (0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95)


def _signals(row: dict[str, object]) -> dict[str, float]:
    names = (
        "compliance", "endpoint_health", "identity_assurance", "patch_posture",
        "security_coverage", "freshness", "threat_risk", "anomaly_risk",
    )
    return {name: float(row[name]) for name in names}


def evaluate_risk_coverage(
    rows: int = 50_000,
    *,
    seed: int = 20260903,
    thresholds: tuple[float, ...] = DEFAULT_THRESHOLDS,
) -> list[dict[str, float | int]]:
    """Return ordinary-access coverage and conditional unsafe-ALLOW risk."""
    if rows <= 0:
        raise ValueError("rows must be positive")
    if any(not 0.55 <= threshold <= 1.0 for threshold in thresholds):
        raise ValueError("thresholds must be in [0.55, 1.0]")

    rng = random.Random(seed)
    generated = [generate_row(rng, row_id) for row_id in range(1, rows + 1)]
    total_safe = sum(int(row["safe_for_ordinary_access"]) for row in generated)

    results: list[dict[str, float | int]] = []
    for threshold in thresholds:
        allowed = []
        for row in generated:
            decision = calculate_trust(_signals(row), allow_threshold=threshold).decision
            if decision == "ALLOW":
                allowed.append(row)

        unsafe_allowed = sum(
            1 - int(row["safe_for_ordinary_access"])
            for row in allowed
        )
        safe_allowed = len(allowed) - unsafe_allowed
        results.append({
            "allow_threshold": threshold,
            "allowed": len(allowed),
            "ordinary_access_coverage": len(allowed) / rows,
            "unsafe_allow_risk": unsafe_allowed / len(allowed) if allowed else 0.0,
            "safe_session_allow_recall": safe_allowed / total_safe if total_safe else 0.0,
        })
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=50_000)
    parser.add_argument("--seed", type=int, default=20260903)
    args = parser.parse_args()

    print("Synthetic ordinary-access risk-coverage analysis")
    print("threshold  coverage  unsafe-risk  safe-recall")
    for result in evaluate_risk_coverage(rows=args.rows, seed=args.seed):
        print(
            f"{result['allow_threshold']:.2f}       "
            f"{result['ordinary_access_coverage']:.4f}    "
            f"{result['unsafe_allow_risk']:.4f}      "
            f"{result['safe_session_allow_recall']:.4f}"
        )


if __name__ == "__main__":
    main()
