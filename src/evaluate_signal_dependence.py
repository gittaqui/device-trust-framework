"""Stress-test trust policies when telemetry signals are statistically dependent.

The original synthetic generator samples each signal independently inside a
scenario-specific range. This experiment instead uses a one-factor Gaussian
copula to induce positive dependence among *safety-oriented* factors while
preserving every scenario's marginal ranges. Risk signals are generated in the
opposite direction so threat/anomaly safety co-move with the other safety factors.

This is a synthetic structural-sensitivity experiment, not real-world evidence.
"""
from __future__ import annotations

import math
import random

from generate_synthetic_data import SCENARIOS, SCENARIO_WEIGHTS
from evaluate_identity_noncompensation import apply_identity_guard
from evaluate_attribute_quorum import quorum_decision
from trust_model import calculate_trust

SIGNALS = (
    "compliance", "endpoint_health", "identity_assurance", "patch_posture",
    "security_coverage", "freshness", "threat_risk", "anomaly_risk",
)
CORRELATIONS = (0.0, 0.3, 0.6, 0.8)


def _normal_cdf(value: float) -> float:
    return 0.5 * (1.0 + math.erf(value / math.sqrt(2.0)))


def correlated_signals(
    rng: random.Random,
    scenario: str,
    rho: float,
) -> dict[str, float]:
    """Sample scenario marginals with a shared latent safety factor.

    ``rho`` is the latent Gaussian correlation. Because each marginal is
    transformed monotonically, observed Pearson correlations need not equal rho.
    """
    if not 0.0 <= rho < 1.0:
        raise ValueError("rho must be in [0, 1).")

    ranges = SCENARIOS[scenario]["ranges"]
    common = rng.gauss(0.0, 1.0)
    common_scale = math.sqrt(rho)
    residual_scale = math.sqrt(1.0 - rho)
    output: dict[str, float] = {}

    for signal in SIGNALS:
        latent = common_scale * common + residual_scale * rng.gauss(0.0, 1.0)
        quantile = _normal_cdf(latent)
        # Raw threat/anomaly risk should fall as the shared safety state rises.
        if signal in {"threat_risk", "anomaly_risk"}:
            quantile = 1.0 - quantile
        low, high = ranges[signal]
        output[signal] = low + (high - low) * quantile

    return output


def evaluate_dependence(
    rho: float,
    *,
    rows: int = 50_000,
    seed: int = 20260917,
) -> dict[str, dict[str, float]]:
    """Evaluate fixed policies under one synthetic dependence condition."""
    if rows <= 0:
        raise ValueError("rows must be positive.")

    rng = random.Random(seed)
    names = [name for name, _ in SCENARIO_WEIGHTS]
    probabilities = [weight for _, weight in SCENARIO_WEIGHTS]
    policies = ("additive_075", "guarded_075", "quorum_070_7of8")
    totals = {
        p: {"safe": 0, "unsafe": 0, "false_allow": 0, "safe_step_up": 0}
        for p in policies
    }

    for _ in range(rows):
        scenario = rng.choices(names, weights=probabilities, k=1)[0]
        safe = bool(SCENARIOS[scenario]["safe"])
        signals = correlated_signals(rng, scenario, rho)
        decisions = {
            "additive_075": calculate_trust(signals, allow_threshold=0.75).decision,
            "guarded_075": apply_identity_guard(signals, allow_threshold=0.75)[0],
            "quorum_070_7of8": quorum_decision(signals),
        }
        for policy, decision in decisions.items():
            bucket = totals[policy]
            bucket["safe" if safe else "unsafe"] += 1
            if not safe and decision == "ALLOW":
                bucket["false_allow"] += 1
            if safe and decision == "STEP_UP":
                bucket["safe_step_up"] += 1

    return {
        policy: {
            "false_allow_rate": values["false_allow"] / values["unsafe"],
            "safe_step_up_rate": values["safe_step_up"] / values["safe"],
        }
        for policy, values in totals.items()
    }


def main() -> None:
    for rho in CORRELATIONS:
        print(f"rho={rho:.1f}")
        for policy, metrics in evaluate_dependence(rho).items():
            print(
                f"  {policy:18s} false_allow={metrics['false_allow_rate']:.2%} "
                f"safe_step_up={metrics['safe_step_up_rate']:.2%}"
            )


if __name__ == "__main__":
    main()
