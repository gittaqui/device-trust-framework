"""Evaluate whether identity/behavior evidence can be masked by additive trust evidence.

This experiment is deliberately diagnostic. It does not claim that the proposed
identity guard is an optimal production policy. It quantifies compensation in the
current weighted model and compares it with a simple STEP_UP guard and a stricter
global threshold.
"""

from __future__ import annotations

import argparse
import random
from dataclasses import dataclass

from generate_synthetic_data import generate_row
from trust_model import calculate_trust


@dataclass(frozen=True)
class IdentityGuard:
    """Experimental non-compensatory identity/behavior constraints."""

    min_identity_assurance: float = 0.40
    max_anomaly_risk: float = 0.75


def apply_identity_guard(
    signals: dict[str, float],
    *,
    allow_threshold: float = 0.75,
    guard: IdentityGuard = IdentityGuard(),
) -> tuple[str, str | None]:
    """Convert an otherwise-ALLOW decision to STEP_UP when identity evidence is weak.

    Existing hard-deny behavior remains owned by ``calculate_trust``. The guard is
    intentionally an abstention/verification action rather than an automatic denial.
    """
    decision = calculate_trust(signals, allow_threshold=allow_threshold)

    if decision.decision == "ALLOW" and (
        signals["identity_assurance"] < guard.min_identity_assurance
        or signals["anomaly_risk"] > guard.max_anomaly_risk
    ):
        return "STEP_UP", "identity_behavior_guard"

    return decision.decision, decision.hard_gate


def representative_healthy_context() -> dict[str, float]:
    """Return midpoint values of the current synthetic healthy scenario ranges."""
    return {
        "compliance": 0.925,
        "endpoint_health": 0.91,
        "identity_assurance": 0.925,
        "patch_posture": 0.90,
        "security_coverage": 0.95,
        "freshness": 0.925,
        "threat_risk": 0.06,
        "anomaly_risk": 0.075,
    }


def policy_surface(step: float = 0.05) -> list[tuple[float, float, str, str, str]]:
    """Sweep identity assurance and anomaly risk while holding endpoint evidence fixed."""
    points = int(round(1.0 / step))
    values = [round(index * step, 10) for index in range(points + 1)]
    base = representative_healthy_context()
    rows = []

    for identity in values:
        for anomaly in values:
            signals = dict(base)
            signals["identity_assurance"] = identity
            signals["anomaly_risk"] = anomaly

            additive_075 = calculate_trust(signals, allow_threshold=0.75).decision
            additive_080 = calculate_trust(signals, allow_threshold=0.80).decision
            guarded_075, _ = apply_identity_guard(signals)

            rows.append(
                (identity, anomaly, additive_075, additive_080, guarded_075)
            )

    return rows


def summarize_surface(
    rows: list[tuple[float, float, str, str, str]],
) -> dict[str, int]:
    """Summarize how much of the identity/anomaly policy surface remains ALLOW."""
    return {
        "points": len(rows),
        "additive_075_allow": sum(row[2] == "ALLOW" for row in rows),
        "additive_080_allow": sum(row[3] == "ALLOW" for row in rows),
        "guarded_075_allow": sum(row[4] == "ALLOW" for row in rows),
    }


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


def evaluate_population(rows: int = 50_000, seed: int = 20260903) -> dict[str, object]:
    """Compare three policies on the existing seeded synthetic population."""
    rng = random.Random(seed)
    policies = ("additive_075", "additive_080", "guarded_075")
    totals = {
        policy: {
            "false_allow": 0,
            "safe_step_up": 0,
            "safe_deny": 0,
            "safe": 0,
            "unsafe": 0,
        }
        for policy in policies
    }
    by_scenario: dict[str, dict[str, dict[str, int]]] = {}

    for row_id in range(1, rows + 1):
        row = generate_row(rng, row_id)
        signals = _signals(row)
        safe = bool(int(row["safe_for_ordinary_access"]))
        scenario = str(row["scenario"])

        decisions = {
            "additive_075": calculate_trust(signals, allow_threshold=0.75).decision,
            "additive_080": calculate_trust(signals, allow_threshold=0.80).decision,
            "guarded_075": apply_identity_guard(signals)[0],
        }

        by_scenario.setdefault(
            scenario,
            {
                policy: {"ALLOW": 0, "STEP_UP": 0, "DENY": 0, "rows": 0}
                for policy in policies
            },
        )

        for policy, decision in decisions.items():
            totals[policy]["safe" if safe else "unsafe"] += 1
            if not safe and decision == "ALLOW":
                totals[policy]["false_allow"] += 1
            if safe and decision == "STEP_UP":
                totals[policy]["safe_step_up"] += 1
            if safe and decision == "DENY":
                totals[policy]["safe_deny"] += 1

            by_scenario[scenario][policy][decision] += 1
            by_scenario[scenario][policy]["rows"] += 1

    summary = {}
    for policy, values in totals.items():
        summary[policy] = {
            **values,
            "false_allow_rate": values["false_allow"] / values["unsafe"],
            "safe_step_up_rate": values["safe_step_up"] / values["safe"],
            "safe_deny_rate": values["safe_deny"] / values["safe"],
        }

    return {"summary": summary, "by_scenario": by_scenario}


def _rate(bucket: dict[str, int], decision: str) -> float:
    return bucket[decision] / bucket["rows"] if bucket["rows"] else 0.0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=50_000)
    parser.add_argument("--seed", type=int, default=20260903)
    args = parser.parse_args()

    population = evaluate_population(args.rows, args.seed)
    surface = summarize_surface(policy_surface())

    print("Identity Non-Compensation Experiment")
    print("=" * 36)
    for policy, result in population["summary"].items():
        print(f"{policy}")
        print(f"  false-allow rate: {result['false_allow_rate']:.2%}")
        print(f"  safe STEP_UP:     {result['safe_step_up_rate']:.2%}")
        print(f"  safe DENY:        {result['safe_deny_rate']:.2%}")

    print("\nSelected unsafe scenarios")
    for scenario in ("identity_risk", "adversarial_compliant"):
        print(f"{scenario}")
        for policy in ("additive_075", "additive_080", "guarded_075"):
            bucket = population["by_scenario"][scenario][policy]
            print(f"  {policy} ALLOW: {_rate(bucket, 'ALLOW'):.2%}")

    print("\nPolicy-surface diagnostic")
    print(f"  grid points: {surface['points']}")
    print(
        "  additive_075 ALLOW: "
        f"{surface['additive_075_allow']}/{surface['points']}"
    )
    print(
        "  additive_080 ALLOW: "
        f"{surface['additive_080_allow']}/{surface['points']}"
    )
    print(
        "  guarded_075 ALLOW:  "
        f"{surface['guarded_075_allow']}/{surface['points']}"
    )


if __name__ == "__main__":
    main()
