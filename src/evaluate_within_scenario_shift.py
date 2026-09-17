"""Stress-test trust policies under controlled within-scenario signal shift.

Unlike evaluate_prevalence_shift.py, this experiment freezes scenario prevalence
and labels while applying pre-specified offsets to selected telemetry dimensions.
It is a synthetic covariate/measurement-shift stress test, not real-world evidence.
"""
from __future__ import annotations

import random
from generate_synthetic_data import SCENARIOS, SCENARIO_WEIGHTS
from evaluate_identity_noncompensation import apply_identity_guard
from evaluate_attribute_quorum import quorum_decision
from trust_model import calculate_trust

SIGNALS = ("compliance", "endpoint_health", "identity_assurance", "patch_posture", "security_coverage", "freshness", "threat_risk", "anomaly_risk")

SHIFTS = {
    "baseline": {},
    "identity_assurance_-0.15": {"identity_assurance": -0.15},
    "anomaly_risk_+0.15": {"anomaly_risk": 0.15},
    "posture_erosion_-0.10": {"compliance": -0.10, "endpoint_health": -0.10, "patch_posture": -0.10},
    "mixed_adverse": {"identity_assurance": -0.10, "anomaly_risk": 0.10, "endpoint_health": -0.08, "freshness": -0.08},
}


def _clip(value: float) -> float:
    return max(0.0, min(1.0, value))


def shifted_signals(rng: random.Random, scenario: str, offsets: dict[str, float]) -> dict[str, float]:
    ranges = SCENARIOS[scenario]["ranges"]
    return {signal: _clip(rng.uniform(*ranges[signal]) + offsets.get(signal, 0.0)) for signal in SIGNALS}


def evaluate_shift(offsets: dict[str, float], *, rows: int = 50_000, seed: int = 20260916) -> dict[str, dict[str, float]]:
    unknown = set(offsets).difference(SIGNALS)
    if unknown:
        raise ValueError(f"Unknown signals: {sorted(unknown)}")

    rng = random.Random(seed)
    names = [name for name, _ in SCENARIO_WEIGHTS]
    probabilities = [weight for _, weight in SCENARIO_WEIGHTS]
    policies = ("additive_075", "guarded_075", "quorum_070_7of8")
    totals = {p: {"safe": 0, "unsafe": 0, "false_allow": 0, "safe_step_up": 0} for p in policies}

    for _ in range(rows):
        scenario = rng.choices(names, weights=probabilities, k=1)[0]
        safe = bool(SCENARIOS[scenario]["safe"])
        signals = shifted_signals(rng, scenario, offsets)
        decisions = {
            "additive_075": calculate_trust(signals, allow_threshold=.75).decision,
            "guarded_075": apply_identity_guard(signals, allow_threshold=.75)[0],
            "quorum_070_7of8": quorum_decision(signals),
        }
        for policy, decision in decisions.items():
            totals[policy]["safe" if safe else "unsafe"] += 1
            if not safe and decision == "ALLOW": totals[policy]["false_allow"] += 1
            if safe and decision == "STEP_UP": totals[policy]["safe_step_up"] += 1

    return {p: {
        "false_allow_rate": v["false_allow"] / v["unsafe"],
        "safe_step_up_rate": v["safe_step_up"] / v["safe"],
    } for p, v in totals.items()}


def main() -> None:
    for name, offsets in SHIFTS.items():
        print(name)
        for policy, metrics in evaluate_shift(offsets).items():
            print(f"  {policy:18s} false_allow={metrics['false_allow_rate']:.2%} safe_step_up={metrics['safe_step_up_rate']:.2%}")

if __name__ == "__main__":
    main()
