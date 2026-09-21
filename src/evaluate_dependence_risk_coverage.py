"""Risk-coverage analysis under correlated synthetic telemetry.

Combines the existing Gaussian-copula dependence stress test with Wilson-score
uncertainty intervals. All results are synthetic and quantify Monte Carlo
uncertainty under the authored generator, not deployment uncertainty.
"""
from __future__ import annotations

import argparse
import random

from evaluate_risk_coverage_uncertainty import wilson_interval
from evaluate_signal_dependence import correlated_signals
from generate_synthetic_data import SCENARIOS, SCENARIO_WEIGHTS
from trust_model import calculate_trust

DEFAULT_THRESHOLDS = (0.70, 0.75, 0.80, 0.85, 0.90)
DEFAULT_RHOS = (0.0, 0.3, 0.6, 0.8)


def evaluate_dependence_risk_coverage(
    rho: float,
    *,
    rows: int = 50_000,
    seed: int = 20260920,
    thresholds: tuple[float, ...] = DEFAULT_THRESHOLDS,
    confidence: float = 0.95,
) -> list[dict[str, float | int]]:
    """Evaluate additive-policy risk/coverage under one dependence condition."""
    if rows <= 0:
        raise ValueError("rows must be positive")
    if not 0.0 <= rho < 1.0:
        raise ValueError("rho must be in [0, 1)")

    rng = random.Random(seed)
    names = [name for name, _ in SCENARIO_WEIGHTS]
    probabilities = [weight for _, weight in SCENARIO_WEIGHTS]
    generated: list[tuple[bool, dict[str, float]]] = []

    for _ in range(rows):
        scenario = rng.choices(names, weights=probabilities, k=1)[0]
        generated.append((bool(SCENARIOS[scenario]["safe"]), correlated_signals(rng, scenario, rho)))

    total_safe = sum(int(safe) for safe, _ in generated)
    results: list[dict[str, float | int]] = []
    for threshold in thresholds:
        allowed = [safe for safe, signals in generated if calculate_trust(signals, allow_threshold=threshold).decision == "ALLOW"]
        if not allowed:
            raise ValueError("threshold produced no ALLOW decisions")
        unsafe_allowed = sum(not safe for safe in allowed)
        safe_allowed = len(allowed) - unsafe_allowed
        risk_low, risk_high = wilson_interval(unsafe_allowed, len(allowed), confidence)
        recall_low, recall_high = wilson_interval(safe_allowed, total_safe, confidence)
        results.append({
            "rho": rho,
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
    parser.add_argument("--seed", type=int, default=20260920)
    args = parser.parse_args()
    for rho in DEFAULT_RHOS:
        print(f"rho={rho:.1f}")
        for r in evaluate_dependence_risk_coverage(rho, rows=args.rows, seed=args.seed):
            print(f"  t={r['allow_threshold']:.2f} coverage={r['ordinary_access_coverage']:.2%} risk={r['unsafe_allow_risk']:.3%} [{r['unsafe_allow_risk_ci_low']:.3%}, {r['unsafe_allow_risk_ci_high']:.3%}] safe_recall={r['safe_session_allow_recall']:.2%}")


if __name__ == "__main__":
    main()
