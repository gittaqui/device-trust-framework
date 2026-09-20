"""Wilson-score uncertainty intervals for synthetic risk-coverage analysis.

This module augments the point-estimate risk-coverage experiment with 95% Wilson
score intervals for binomial proportions. In particular, an observed zero unsafe
ALLOW count is not reported as proof of zero underlying risk. All observations
are synthetic scenario draws; intervals quantify Monte Carlo sampling uncertainty
under this generator, not real-world deployment uncertainty.
"""

from __future__ import annotations

import argparse
import math
import random
from statistics import NormalDist

from generate_synthetic_data import generate_row
from trust_model import calculate_trust

DEFAULT_THRESHOLDS = (0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95)


def wilson_interval(successes: int, trials: int, confidence: float = 0.95) -> tuple[float, float]:
    """Return a two-sided Wilson score interval for a binomial proportion."""
    if trials <= 0:
        raise ValueError("trials must be positive")
    if not 0 <= successes <= trials:
        raise ValueError("successes must be between zero and trials")
    if not 0 < confidence < 1:
        raise ValueError("confidence must be in (0, 1)")

    z = NormalDist().inv_cdf(1.0 - (1.0 - confidence) / 2.0)
    p = successes / trials
    z2 = z * z
    denominator = 1.0 + z2 / trials
    center = (p + z2 / (2.0 * trials)) / denominator
    half_width = (
        z
        * math.sqrt(p * (1.0 - p) / trials + z2 / (4.0 * trials * trials))
        / denominator
    )
    return max(0.0, center - half_width), min(1.0, center + half_width)


def _signals(row: dict[str, object]) -> dict[str, float]:
    names = (
        "compliance", "endpoint_health", "identity_assurance", "patch_posture",
        "security_coverage", "freshness", "threat_risk", "anomaly_risk",
    )
    return {name: float(row[name]) for name in names}


def evaluate_uncertainty(
    rows: int = 50_000,
    *,
    seed: int = 20260903,
    thresholds: tuple[float, ...] = DEFAULT_THRESHOLDS,
    confidence: float = 0.95,
) -> list[dict[str, float | int]]:
    """Evaluate risk/coverage point estimates and Wilson uncertainty intervals."""
    if rows <= 0:
        raise ValueError("rows must be positive")

    rng = random.Random(seed)
    generated = [generate_row(rng, row_id) for row_id in range(1, rows + 1)]
    total_safe = sum(int(row["safe_for_ordinary_access"]) for row in generated)
    if total_safe == 0:
        raise ValueError("generated sample contains no safe sessions")

    results: list[dict[str, float | int]] = []
    for threshold in thresholds:
        allowed = [
            row for row in generated
            if calculate_trust(_signals(row), allow_threshold=threshold).decision == "ALLOW"
        ]
        if not allowed:
            raise ValueError("threshold produced no ALLOW decisions")

        unsafe_allowed = sum(1 - int(row["safe_for_ordinary_access"]) for row in allowed)
        safe_allowed = len(allowed) - unsafe_allowed
        risk_low, risk_high = wilson_interval(unsafe_allowed, len(allowed), confidence)
        recall_low, recall_high = wilson_interval(safe_allowed, total_safe, confidence)

        results.append({
            "allow_threshold": threshold,
            "allowed": len(allowed),
            "unsafe_allowed": unsafe_allowed,
            "ordinary_access_coverage": len(allowed) / rows,
            "unsafe_allow_risk": unsafe_allowed / len(allowed),
            "unsafe_allow_risk_ci_low": risk_low,
            "unsafe_allow_risk_ci_high": risk_high,
            "safe_session_allow_recall": safe_allowed / total_safe,
            "safe_session_allow_recall_ci_low": recall_low,
            "safe_session_allow_recall_ci_high": recall_high,
        })
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=50_000)
    parser.add_argument("--seed", type=int, default=20260903)
    args = parser.parse_args()

    print("Synthetic risk-coverage uncertainty analysis (95% Wilson intervals)")
    print("threshold  allowed  unsafe  risk [95% CI]       safe-recall [95% CI]")
    for result in evaluate_uncertainty(rows=args.rows, seed=args.seed):
        print(
            f"{result['allow_threshold']:.2f}       {result['allowed']:5d}    "
            f"{result['unsafe_allowed']:5d}   {result['unsafe_allow_risk']:.4f} "
            f"[{result['unsafe_allow_risk_ci_low']:.4f}, {result['unsafe_allow_risk_ci_high']:.4f}]   "
            f"{result['safe_session_allow_recall']:.4f} "
            f"[{result['safe_session_allow_recall_ci_low']:.4f}, "
            f"{result['safe_session_allow_recall_ci_high']:.4f}]"
        )


if __name__ == "__main__":
    main()
