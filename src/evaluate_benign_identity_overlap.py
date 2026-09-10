"""Stress-test policy conclusions under benign/unsafe label overlap.

This experiment does not estimate real-world prevalence. It asks how the apparent
security/friction trade-off changes if some synthetic ``identity_risk`` rows
represent legitimate sessions that should receive ordinary access. The relabeling
sets are nested across overlap fractions to support interpretable sensitivity
analysis.
"""

from __future__ import annotations

import argparse
import random
from dataclasses import dataclass

from generate_synthetic_data import generate_row
from evaluate_identity_noncompensation import apply_identity_guard
from trust_model import calculate_trust


OVERLAP_FRACTIONS = (0.0, 0.10, 0.25, 0.50, 1.0)


@dataclass
class Counts:
    safe: int = 0
    unsafe: int = 0
    false_allow: int = 0
    safe_step_up: int = 0
    safe_deny: int = 0


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


def _decisions(signals: dict[str, float]) -> dict[str, str]:
    return {
        "additive_075": calculate_trust(signals, allow_threshold=0.75).decision,
        "additive_080": calculate_trust(signals, allow_threshold=0.80).decision,
        "guarded_075": apply_identity_guard(signals)[0],
    }


def evaluate_label_overlap(
    rows: int = 50_000,
    *,
    data_seed: int = 20260903,
    overlap_seed: int = 20260909,
    fractions: tuple[float, ...] = OVERLAP_FRACTIONS,
) -> dict[float, dict[str, object]]:
    """Evaluate policies as identity-risk labels are progressively made ambiguous.

    ``identity_risk`` rows are assigned a stable pseudo-random overlap score.
    A row is reinterpreted as legitimate for fraction ``f`` when score < ``f``.
    This makes the relabeled sets nested as ``f`` grows.

    The operation is deliberately a label-sensitivity stress test, not a claim
    that any stated fraction occurs in production.
    """
    if any(not 0.0 <= fraction <= 1.0 for fraction in fractions):
        raise ValueError("Overlap fractions must be in [0, 1].")

    data_rng = random.Random(data_seed)
    overlap_rng = random.Random(overlap_seed)

    generated: list[tuple[dict[str, object], float | None]] = []
    identity_risk_rows = 0
    for row_id in range(1, rows + 1):
        row = generate_row(data_rng, row_id)
        overlap_score = None
        if row["scenario"] == "identity_risk":
            overlap_score = overlap_rng.random()
            identity_risk_rows += 1
        generated.append((row, overlap_score))

    results: dict[float, dict[str, object]] = {}

    for fraction in fractions:
        counts = {
            "additive_075": Counts(),
            "additive_080": Counts(),
            "guarded_075": Counts(),
        }
        relabeled = 0

        for row, overlap_score in generated:
            safe = bool(int(row["safe_for_ordinary_access"]))
            if (
                row["scenario"] == "identity_risk"
                and overlap_score is not None
                and overlap_score < fraction
            ):
                safe = True
                relabeled += 1

            decisions = _decisions(_signals(row))
            for policy, decision in decisions.items():
                bucket = counts[policy]
                if safe:
                    bucket.safe += 1
                    if decision == "STEP_UP":
                        bucket.safe_step_up += 1
                    elif decision == "DENY":
                        bucket.safe_deny += 1
                else:
                    bucket.unsafe += 1
                    if decision == "ALLOW":
                        bucket.false_allow += 1

        summary = {}
        for policy, bucket in counts.items():
            summary[policy] = {
                "safe": bucket.safe,
                "unsafe": bucket.unsafe,
                "false_allow": bucket.false_allow,
                "safe_step_up": bucket.safe_step_up,
                "safe_deny": bucket.safe_deny,
                "false_allow_rate": (
                    bucket.false_allow / bucket.unsafe if bucket.unsafe else 0.0
                ),
                "safe_step_up_rate": (
                    bucket.safe_step_up / bucket.safe if bucket.safe else 0.0
                ),
                "safe_deny_rate": (
                    bucket.safe_deny / bucket.safe if bucket.safe else 0.0
                ),
            }

        results[fraction] = {
            "identity_risk_rows": identity_risk_rows,
            "relabeled_identity_risk_rows": relabeled,
            "policies": summary,
        }

    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=50_000)
    parser.add_argument("--data-seed", type=int, default=20260903)
    parser.add_argument("--overlap-seed", type=int, default=20260909)
    args = parser.parse_args()

    results = evaluate_label_overlap(
        rows=args.rows,
        data_seed=args.data_seed,
        overlap_seed=args.overlap_seed,
    )

    print("Benign Identity-Overlap Label Sensitivity")
    print("=" * 41)
    for fraction, result in results.items():
        relabeled = result["relabeled_identity_risk_rows"]
        identity_rows = result["identity_risk_rows"]
        print(
            f"\nTarget overlap={fraction:.0%} "
            f"(relabeled {relabeled}/{identity_rows} identity-risk rows)"
        )
        for policy, metrics in result["policies"].items():
            print(
                f"  {policy:14s} "
                f"false-ALLOW={metrics['false_allow_rate']:.2%} "
                f"safe-STEP_UP={metrics['safe_step_up_rate']:.2%} "
                f"safe-DENY={metrics['safe_deny_rate']:.2%}"
            )


if __name__ == "__main__":
    main()
