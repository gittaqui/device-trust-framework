"""Cost-sensitive sensitivity analysis for ALLOW/STEP_UP/DENY policies.

The experiment deliberately varies the relative cost assigned to STEP_UP instead of
assuming one universal operational value. Synthetic labels and costs are research
assumptions, not production estimates. The analysis is intended to expose where policy
rankings depend on those assumptions.
"""

from __future__ import annotations

import argparse
import random
from dataclasses import dataclass

from generate_synthetic_data import generate_row
from evaluate_identity_noncompensation import apply_identity_guard
from trust_model import binary_compliance_decision, calculate_trust

POLICY_THRESHOLDS = (0.70, 0.75, 0.80, 0.85)
GUARDED_THRESHOLDS = (0.70, 0.75, 0.80)
DEFAULT_STEP_UP_COSTS = (0.025, 0.05, 0.10, 0.20)
DEFAULT_OVERLAP_FRACTIONS = (0.0, 0.25, 0.50, 1.0)

@dataclass(frozen=True)
class CostModel:
    """Normalized decision costs relative to an unsafe ordinary ALLOW (= 1.0)."""
    unsafe_allow: float = 1.0
    step_up: float = 0.10
    safe_deny: float = 0.50

    def __post_init__(self) -> None:
        if min(self.unsafe_allow, self.step_up, self.safe_deny) < 0:
            raise ValueError("Decision costs must be non-negative.")
        if self.unsafe_allow <= 0:
            raise ValueError("unsafe_allow must be positive for normalization.")

def _signals(row: dict[str, object]) -> dict[str, float]:
    names = ("compliance", "endpoint_health", "identity_assurance", "patch_posture", "security_coverage", "freshness", "threat_risk", "anomaly_risk")
    return {name: float(row[name]) for name in names}

def _policy_decisions(signals: dict[str, float]) -> dict[str, str]:
    decisions = {"binary": binary_compliance_decision(signals["compliance"])}
    for threshold in POLICY_THRESHOLDS:
        decisions[f"additive_{int(threshold * 100):03d}"] = calculate_trust(signals, allow_threshold=threshold).decision
    for threshold in GUARDED_THRESHOLDS:
        decisions[f"guarded_{int(threshold * 100):03d}"] = apply_identity_guard(signals, allow_threshold=threshold)[0]
    return decisions

def decision_cost(*, safe: bool, decision: str, costs: CostModel) -> float:
    """Return normalized operational loss for one labeled session."""
    if decision == "STEP_UP":
        return costs.step_up
    if safe and decision == "DENY":
        return costs.safe_deny
    if not safe and decision == "ALLOW":
        return costs.unsafe_allow
    if decision not in {"ALLOW", "DENY"}:
        raise ValueError(f"Unknown decision: {decision}")
    return 0.0

def evaluate_cost_sensitivity(rows: int = 50_000, *, data_seed: int = 20260903, overlap_seed: int = 20260909, overlap_fractions: tuple[float, ...] = DEFAULT_OVERLAP_FRACTIONS, step_up_costs: tuple[float, ...] = DEFAULT_STEP_UP_COSTS, safe_deny_cost: float = 0.50) -> dict[float, dict[float, dict[str, object]]]:
    """Evaluate policy expected loss over label-overlap and STEP_UP-cost assumptions."""
    if any(not 0.0 <= fraction <= 1.0 for fraction in overlap_fractions):
        raise ValueError("Overlap fractions must be in [0, 1].")
    if any(cost < 0.0 for cost in step_up_costs):
        raise ValueError("STEP_UP costs must be non-negative.")

    data_rng = random.Random(data_seed)
    overlap_rng = random.Random(overlap_seed)
    generated: list[tuple[dict[str, object], float | None, dict[str, str]]] = []
    for row_id in range(1, rows + 1):
        row = generate_row(data_rng, row_id)
        overlap_score = overlap_rng.random() if row["scenario"] == "identity_risk" else None
        generated.append((row, overlap_score, _policy_decisions(_signals(row))))

    results: dict[float, dict[float, dict[str, object]]] = {}
    for fraction in overlap_fractions:
        labels: list[bool] = []
        relabeled = 0
        for row, overlap_score, _ in generated:
            safe = bool(int(row["safe_for_ordinary_access"]))
            if row["scenario"] == "identity_risk" and overlap_score is not None and overlap_score < fraction:
                safe = True
                relabeled += 1
            labels.append(safe)

        by_cost: dict[float, dict[str, object]] = {}
        for step_cost in step_up_costs:
            costs = CostModel(step_up=step_cost, safe_deny=safe_deny_cost)
            totals: dict[str, float] = {}
            components: dict[str, dict[str, int]] = {}
            for policy in generated[0][2]:
                total = 0.0
                counts = {"unsafe_allow": 0, "step_up": 0, "safe_deny": 0}
                for safe, (_, _, decisions) in zip(labels, generated):
                    decision = decisions[policy]
                    total += decision_cost(safe=safe, decision=decision, costs=costs)
                    if not safe and decision == "ALLOW": counts["unsafe_allow"] += 1
                    if decision == "STEP_UP": counts["step_up"] += 1
                    if safe and decision == "DENY": counts["safe_deny"] += 1
                totals[policy] = total / rows
                components[policy] = counts

            minimum = min(totals.values())
            winners = sorted(policy for policy, value in totals.items() if abs(value - minimum) <= 1e-12)
            by_cost[step_cost] = {"winner": winners[0], "tied_winners": winners, "loss": totals, "components": components}
        results[fraction] = {"relabeled_identity_risk_rows": relabeled, "costs": by_cost}
    return results

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=50_000)
    parser.add_argument("--data-seed", type=int, default=20260903)
    parser.add_argument("--overlap-seed", type=int, default=20260909)
    args = parser.parse_args()
    results = evaluate_cost_sensitivity(rows=args.rows, data_seed=args.data_seed, overlap_seed=args.overlap_seed)
    print("Cost-Sensitive Abstention Analysis")
    print("=" * 35)
    print("Loss normalization: unsafe ALLOW=1.0, safe DENY=0.5")
    for overlap, result in results.items():
        print(f"\nBenign identity overlap={overlap:.0%} (relabeled={result['relabeled_identity_risk_rows']})")
        for step_cost, summary in result["costs"].items():
            winner = summary["winner"]
            print(f"  STEP_UP cost={step_cost:.3f}: winner={winner:12s} normalized loss={summary['loss'][winner]:.4f}")

if __name__ == "__main__":
    main()
