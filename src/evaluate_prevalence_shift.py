"""Evaluate policy robustness under synthetic scenario-prevalence shift.

This experiment changes only scenario mixture weights. Per-scenario feature
ranges, trust-model parameters, and policy thresholds remain frozen. Results are
synthetic stress tests and must not be interpreted as real-world prevalence or
production effectiveness.
"""
from __future__ import annotations

import random
from generate_synthetic_data import SCENARIOS
from evaluate_identity_noncompensation import apply_identity_guard
from evaluate_attribute_quorum import quorum_decision
from trust_model import calculate_trust

MIXES = {
    "baseline": {"healthy": .50, "policy_drift": .08, "stale": .08, "identity_risk": .08, "malware": .07, "protection_missing": .06, "mixed_degradation": .07, "adversarial_compliant": .06},
    "benign_heavy": {"healthy": .75, "policy_drift": .10, "stale": .03, "identity_risk": .03, "malware": .02, "protection_missing": .02, "mixed_degradation": .03, "adversarial_compliant": .02},
    "identity_heavy": {"healthy": .42, "policy_drift": .08, "stale": .06, "identity_risk": .22, "malware": .05, "protection_missing": .04, "mixed_degradation": .06, "adversarial_compliant": .07},
    "adversarial_heavy": {"healthy": .40, "policy_drift": .07, "stale": .06, "identity_risk": .08, "malware": .05, "protection_missing": .04, "mixed_degradation": .05, "adversarial_compliant": .25},
    "hard_gate_heavy": {"healthy": .40, "policy_drift": .07, "stale": .06, "identity_risk": .07, "malware": .18, "protection_missing": .15, "mixed_degradation": .04, "adversarial_compliant": .03},
}

SIGNALS = ("compliance", "endpoint_health", "identity_assurance", "patch_posture", "security_coverage", "freshness", "threat_risk", "anomaly_risk")


def _row_for_scenario(rng: random.Random, name: str) -> tuple[bool, dict[str, float]]:
    spec = SCENARIOS[name]
    signals = {signal: rng.uniform(*spec["ranges"][signal]) for signal in SIGNALS}
    return bool(spec["safe"]), signals


def evaluate_mix(mix: dict[str, float], *, rows: int = 50_000, seed: int = 20260915) -> dict[str, dict[str, float]]:
    if abs(sum(mix.values()) - 1.0) > 1e-9:
        raise ValueError("Scenario weights must sum to 1.0")
    unknown = set(mix).difference(SCENARIOS)
    if unknown:
        raise ValueError(f"Unknown scenarios: {sorted(unknown)}")

    rng = random.Random(seed)
    names = list(mix)
    probabilities = [mix[name] for name in names]
    policies = ("additive_075", "guarded_075", "quorum_070_7of8")
    totals = {p: {"safe": 0, "unsafe": 0, "false_allow": 0, "safe_step_up": 0} for p in policies}

    for _ in range(rows):
        scenario = rng.choices(names, weights=probabilities, k=1)[0]
        safe, signals = _row_for_scenario(rng, scenario)
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
    for name, mix in MIXES.items():
        print(name)
        for policy, metrics in evaluate_mix(mix).items():
            print(f"  {policy:18s} false_allow={metrics['false_allow_rate']:.2%} safe_step_up={metrics['safe_step_up_rate']:.2%}")

if __name__ == "__main__":
    main()
