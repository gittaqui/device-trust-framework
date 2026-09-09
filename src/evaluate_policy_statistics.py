"""Statistical comparison of device-trust access policies.

This analysis is intentionally limited to the repository's synthetic generator.
Confidence intervals quantify sampling uncertainty under that generator; they do not
establish real-world security effectiveness or external validity.
"""

from __future__ import annotations

import argparse
import math
import random
from dataclasses import dataclass

from evaluate_identity_noncompensation import apply_identity_guard
from generate_synthetic_data import generate_row
from trust_model import binary_compliance_decision, calculate_trust


SIGNAL_NAMES = (
    "compliance",
    "endpoint_health",
    "identity_assurance",
    "patch_posture",
    "security_coverage",
    "freshness",
    "threat_risk",
    "anomaly_risk",
)


@dataclass(frozen=True)
class RateEstimate:
    count: int
    denominator: int
    rate: float
    ci_low: float
    ci_high: float


@dataclass(frozen=True)
class McNemarResult:
    first_only_correct: int
    second_only_correct: int
    discordant: int
    chi_square_cc: float
    p_value: float


def wilson_interval(successes: int, total: int, z: float = 1.959963984540054) -> tuple[float, float]:
    """Return a two-sided Wilson score interval for a binomial proportion."""
    if total <= 0:
        raise ValueError("total must be positive")
    if successes < 0 or successes > total:
        raise ValueError("successes must be between zero and total")

    proportion = successes / total
    z2 = z * z
    denominator = 1.0 + z2 / total
    center = (proportion + z2 / (2.0 * total)) / denominator
    half_width = (
        z
        * math.sqrt(
            (proportion * (1.0 - proportion) + z2 / (4.0 * total)) / total
        )
        / denominator
    )
    return max(0.0, center - half_width), min(1.0, center + half_width)


def estimate_rate(successes: int, total: int) -> RateEstimate:
    low, high = wilson_interval(successes, total)
    return RateEstimate(successes, total, successes / total, low, high)


def mcnemar_continuity_corrected(
    first_correct: list[bool], second_correct: list[bool]
) -> McNemarResult:
    """Compare paired binary correctness using continuity-corrected McNemar's test.

    For one fixed evaluation population, McNemar's test is appropriate for comparing
    two deterministic policies because their predictions are paired row-by-row.
    """
    if len(first_correct) != len(second_correct):
        raise ValueError("paired correctness vectors must have equal length")

    first_only = sum(a and not b for a, b in zip(first_correct, second_correct))
    second_only = sum(b and not a for a, b in zip(first_correct, second_correct))
    discordant = first_only + second_only

    if discordant == 0:
        return McNemarResult(first_only, second_only, 0, 0.0, 1.0)

    chi_square = (abs(first_only - second_only) - 1.0) ** 2 / discordant
    # A chi-square variable with one degree of freedom has survival function
    # erfc(sqrt(x / 2)), avoiding a SciPy dependency.
    p_value = math.erfc(math.sqrt(chi_square / 2.0))
    return McNemarResult(first_only, second_only, discordant, chi_square, p_value)


def _signals(row: dict[str, object]) -> dict[str, float]:
    return {name: float(row[name]) for name in SIGNAL_NAMES}


def _ordinary_access_correct(safe: bool, decision: str) -> bool:
    """Treat ALLOW as ordinary access and STEP_UP/DENY as ordinary-access blocks."""
    return decision == "ALLOW" if safe else decision != "ALLOW"


def evaluate(rows: int = 50_000, seed: int = 20260903) -> dict[str, object]:
    """Evaluate four paired policies on the same reproducible synthetic population."""
    rng = random.Random(seed)
    policies = ("binary", "additive_075", "additive_080", "guarded_075")
    decisions: dict[str, list[str]] = {policy: [] for policy in policies}
    safe_labels: list[bool] = []

    for row_id in range(1, rows + 1):
        row = generate_row(rng, row_id)
        signals = _signals(row)
        safe = bool(int(row["safe_for_ordinary_access"]))
        safe_labels.append(safe)

        decisions["binary"].append(binary_compliance_decision(signals["compliance"]))
        decisions["additive_075"].append(calculate_trust(signals, allow_threshold=0.75).decision)
        decisions["additive_080"].append(calculate_trust(signals, allow_threshold=0.80).decision)
        decisions["guarded_075"].append(apply_identity_guard(signals)[0])

    safe_total = sum(safe_labels)
    unsafe_total = rows - safe_total
    metrics: dict[str, dict[str, RateEstimate]] = {}
    correctness: dict[str, list[bool]] = {}

    for policy in policies:
        policy_decisions = decisions[policy]
        false_allows = sum(
            (not safe) and decision == "ALLOW"
            for safe, decision in zip(safe_labels, policy_decisions)
        )
        safe_step_ups = sum(
            safe and decision == "STEP_UP"
            for safe, decision in zip(safe_labels, policy_decisions)
        )
        correct = [
            _ordinary_access_correct(safe, decision)
            for safe, decision in zip(safe_labels, policy_decisions)
        ]
        correctness[policy] = correct

        metrics[policy] = {
            "false_allow": estimate_rate(false_allows, unsafe_total),
            "safe_step_up": estimate_rate(safe_step_ups, safe_total),
            "ordinary_access_accuracy": estimate_rate(sum(correct), rows),
        }

    comparisons = {
        "binary_vs_additive_075": mcnemar_continuity_corrected(
            correctness["binary"], correctness["additive_075"]
        ),
        "binary_vs_additive_080": mcnemar_continuity_corrected(
            correctness["binary"], correctness["additive_080"]
        ),
        "binary_vs_guarded_075": mcnemar_continuity_corrected(
            correctness["binary"], correctness["guarded_075"]
        ),
        "additive_075_vs_additive_080": mcnemar_continuity_corrected(
            correctness["additive_075"], correctness["additive_080"]
        ),
        "additive_075_vs_guarded_075": mcnemar_continuity_corrected(
            correctness["additive_075"], correctness["guarded_075"]
        ),
        "additive_080_vs_guarded_075": mcnemar_continuity_corrected(
            correctness["additive_080"], correctness["guarded_075"]
        ),
    }

    return {
        "rows": rows,
        "seed": seed,
        "safe_rows": safe_total,
        "unsafe_rows": unsafe_total,
        "metrics": metrics,
        "comparisons": comparisons,
    }


def _format_rate(estimate: RateEstimate) -> str:
    return (
        f"{estimate.rate:.2%} "
        f"(95% CI {estimate.ci_low:.2%}--{estimate.ci_high:.2%})"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=50_000)
    parser.add_argument("--seed", type=int, default=20260903)
    args = parser.parse_args()

    result = evaluate(args.rows, args.seed)
    print("Paired Policy Statistical Evaluation")
    print("=" * 36)
    print(
        f"rows={result['rows']:,}; safe={result['safe_rows']:,}; "
        f"unsafe={result['unsafe_rows']:,}; seed={result['seed']}"
    )

    for policy, metrics in result["metrics"].items():
        print(f"\n{policy}")
        print(f"  false ALLOW:       {_format_rate(metrics['false_allow'])}")
        print(f"  safe STEP_UP:      {_format_rate(metrics['safe_step_up'])}")
        print(
            "  ordinary accuracy: "
            f"{_format_rate(metrics['ordinary_access_accuracy'])}"
        )

    print("\nPaired McNemar comparisons")
    for name, comparison in result["comparisons"].items():
        p_text = f"{comparison.p_value:.3g}" if comparison.p_value > 0.0 else "<1e-300"
        print(
            f"  {name}: first-only={comparison.first_only_correct}, "
            f"second-only={comparison.second_only_correct}, "
            f"chi2_cc={comparison.chi_square_cc:.3f}, p={p_text}"
        )


if __name__ == "__main__":
    main()
