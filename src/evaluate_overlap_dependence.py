"""Stress device-trust decisions under class overlap and signal dependence.

Scenario-specific ranges are interpolated toward pooled ranges across all
scenarios, deliberately eroding authored separability. A one-factor Gaussian
copula controls positive dependence among safety-oriented evidence. This is a
synthetic stress test, not a model of real enterprise telemetry.
"""
from __future__ import annotations

import argparse
import math
import random

from generate_synthetic_data import SCENARIOS, SCENARIO_WEIGHTS
from trust_model import calculate_trust

DEFAULT_OVERLAPS = (0.0, 0.25, 0.50, 0.75)
DEFAULT_RHOS = (0.0, 0.6)
RISK_SIGNALS = {"threat_risk", "anomaly_risk"}


def _normal_cdf(value: float) -> float:
    return 0.5 * (1.0 + math.erf(value / math.sqrt(2.0)))


def pooled_ranges() -> dict[str, tuple[float, float]]:
    signals = next(iter(SCENARIOS.values()))["ranges"]
    return {
        signal: (
            min(spec["ranges"][signal][0] for spec in SCENARIOS.values()),
            max(spec["ranges"][signal][1] for spec in SCENARIOS.values()),
        )
        for signal in signals
    }


def overlap_signals(
    rng: random.Random, scenario: str, rho: float, overlap: float
) -> dict[str, float]:
    """Sample one scenario after controlled erosion of class separability."""
    if not 0.0 <= overlap <= 1.0:
        raise ValueError("overlap must be in [0, 1]")
    if not 0.0 <= rho < 1.0:
        raise ValueError("rho must be in [0, 1)")

    original = SCENARIOS[scenario]["ranges"]
    pooled = pooled_ranges()
    common = rng.gauss(0.0, 1.0)
    common_scale = math.sqrt(rho)
    residual_scale = math.sqrt(1.0 - rho)
    values: dict[str, float] = {}

    for signal, (low, high) in original.items():
        latent = common_scale * common + residual_scale * rng.gauss(0.0, 1.0)
        quantile = _normal_cdf(latent)
        # Higher shared latent state means safer evidence in every dimension.
        if signal in RISK_SIGNALS:
            quantile = 1.0 - quantile
        pooled_low, pooled_high = pooled[signal]
        stressed_low = (1.0 - overlap) * low + overlap * pooled_low
        stressed_high = (1.0 - overlap) * high + overlap * pooled_high
        values[signal] = stressed_low + quantile * (stressed_high - stressed_low)
    return values


def evaluate_overlap_dependence(
    rho: float,
    overlap: float,
    *,
    rows: int = 50_000,
    seed: int = 20260921,
    allow_threshold: float = 0.80,
) -> dict[str, object]:
    if rows <= 0:
        raise ValueError("rows must be positive")

    rng = random.Random(seed)
    names = [name for name, _ in SCENARIO_WEIGHTS]
    probabilities = [weight for _, weight in SCENARIO_WEIGHTS]
    by_scenario = {name: {"total": 0, "allowed": 0} for name in names}

    for _ in range(rows):
        scenario = rng.choices(names, weights=probabilities, k=1)[0]
        signals = overlap_signals(rng, scenario, rho, overlap)
        allowed = calculate_trust(signals, allow_threshold=allow_threshold).decision == "ALLOW"
        by_scenario[scenario]["total"] += 1
        by_scenario[scenario]["allowed"] += int(allowed)

    total_allowed = sum(v["allowed"] for v in by_scenario.values())
    unsafe_allowed = sum(v["allowed"] for name, v in by_scenario.items() if not bool(SCENARIOS[name]["safe"]))
    total_safe = sum(v["total"] for name, v in by_scenario.items() if bool(SCENARIOS[name]["safe"]))
    safe_allowed = sum(v["allowed"] for name, v in by_scenario.items() if bool(SCENARIOS[name]["safe"]))

    for values in by_scenario.values():
        values["allow_rate"] = values["allowed"] / values["total"]

    return {
        "rho": rho,
        "overlap": overlap,
        "rows": rows,
        "ordinary_access_coverage": total_allowed / rows,
        "unsafe_allow_risk": unsafe_allowed / total_allowed if total_allowed else 0.0,
        "safe_session_allow_recall": safe_allowed / total_safe,
        "by_scenario": by_scenario,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=50_000)
    parser.add_argument("--seed", type=int, default=20260921)
    args = parser.parse_args()
    for rho in DEFAULT_RHOS:
        for overlap in DEFAULT_OVERLAPS:
            result = evaluate_overlap_dependence(rho, overlap, rows=args.rows, seed=args.seed)
            print(f"rho={rho:.1f} overlap={overlap:.2f} coverage={result['ordinary_access_coverage']:.2%} unsafe_risk={result['unsafe_allow_risk']:.2%} safe_recall={result['safe_session_allow_recall']:.2%}")


if __name__ == "__main__":
    main()
