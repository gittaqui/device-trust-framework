"""Evaluate device-trust behavior when telemetry is partially unavailable.

Synthetic experiment only. This module is intentionally explicit about how missing
signals are handled so that the trade-offs can be audited and reproduced.
"""

from __future__ import annotations

import argparse
import csv
import random
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from generate_synthetic_data import generate
from trust_model import DEFAULT_WEIGHTS

SIGNAL_TO_FACTOR = {
    "compliance": "compliance",
    "endpoint_health": "endpoint_health",
    "identity_assurance": "identity_assurance",
    "patch_posture": "patch_posture",
    "security_coverage": "security_coverage",
    "freshness": "freshness",
    "threat_risk": "threat_safety",
    "anomaly_risk": "anomaly_safety",
}

STRATEGY_IDS = {
    "renormalize": 11,
    "neutral": 23,
    "pessimistic": 37,
    "confidence": 41,
    "step_up": 53,
}


def _factor_values(signals: dict[str, float]) -> dict[str, float]:
    factors: dict[str, float] = {}
    for signal, factor in SIGNAL_TO_FACTOR.items():
        if signal not in signals:
            continue
        value = signals[signal]
        factors[factor] = 1.0 - value if signal.endswith("_risk") else value
    return factors


def decide_partial(
    signals: dict[str, float],
    strategy: str,
    *,
    allow_threshold: float = 0.75,
    step_up_threshold: float = 0.55,
    minimum_coverage: float = 0.75,
) -> tuple[float, str, float]:
    """Return score, decision, and observed weight coverage for partial telemetry."""
    if strategy not in STRATEGY_IDS:
        raise ValueError(f"Unknown strategy: {strategy}")

    # Apply hard gates only when the underlying signal is actually observed.
    if signals.get("threat_risk", -1.0) >= 0.90:
        return 0.0, "DENY", 1.0
    if "security_coverage" in signals and signals["security_coverage"] <= 0.15:
        return 0.0, "DENY", 1.0

    factors = _factor_values(signals)
    observed_weight = sum(DEFAULT_WEIGHTS[name] for name in factors)
    if observed_weight <= 0:
        return 0.0, "STEP_UP", 0.0

    weighted_observed = sum(
        DEFAULT_WEIGHTS[name] * value for name, value in factors.items()
    )

    if strategy == "renormalize":
        score = weighted_observed / observed_weight
    elif strategy == "neutral":
        score = weighted_observed + sum(
            DEFAULT_WEIGHTS[name] * 0.5
            for name in DEFAULT_WEIGHTS
            if name not in factors
        )
    elif strategy == "pessimistic":
        score = weighted_observed
    elif strategy == "confidence":
        score = (weighted_observed / observed_weight) * observed_weight
    else:  # step_up
        score = weighted_observed / observed_weight
        critical_missing = (
            "threat_risk" not in signals or "security_coverage" not in signals
        )
        if observed_weight < minimum_coverage or critical_missing:
            return score, "STEP_UP", observed_weight

    if score >= allow_threshold:
        decision = "ALLOW"
    elif score >= step_up_threshold:
        decision = "STEP_UP"
    else:
        decision = "DENY"
    return score, decision, observed_weight


def mask_signals(
    signals: dict[str, float],
    rng: random.Random,
    missing_rate: float,
    *,
    structured: bool,
) -> dict[str, float]:
    """Mask telemetry under MCAR or a critical-signal-biased outage model."""
    masked = dict(signals)
    critical = {"threat_risk", "security_coverage", "identity_assurance"}

    for signal in list(masked):
        if structured:
            probability = missing_rate * (1.8 if signal in critical else 0.6)
        else:
            probability = missing_rate
        if rng.random() < min(probability, 0.95):
            masked.pop(signal)
    return masked


def evaluate(
    input_path: Path,
    *,
    missing_rate: float,
    strategy: str,
    structured: bool,
    seed: int = 20260904,
) -> dict[str, float | int | str]:
    rng = random.Random(
        seed
        + int(missing_rate * 1000) * 100
        + STRATEGY_IDS[strategy]
        + (100000 if structured else 0)
    )
    counts: Counter[str] = Counter()

    with input_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            safe = row["safe_for_ordinary_access"] == "1"
            signals = {
                name: float(row[name])
                for name in SIGNAL_TO_FACTOR
            }
            masked = mask_signals(
                signals,
                rng,
                missing_rate,
                structured=structured,
            )
            _, decision, _ = decide_partial(masked, strategy)

            counts["safe" if safe else "unsafe"] += 1
            counts[decision] += 1
            if not safe and decision == "ALLOW":
                counts["false_allow"] += 1
            if safe and decision == "DENY":
                counts["false_deny"] += 1
            if safe and decision == "STEP_UP":
                counts["safe_step_up"] += 1
            if safe and decision == "ALLOW":
                counts["safe_allow"] += 1

    return {
        "missing_model": "structured" if structured else "mcar",
        "missing_rate": missing_rate,
        "strategy": strategy,
        "false_allow_rate": counts["false_allow"] / counts["unsafe"],
        "false_deny_rate": counts["false_deny"] / counts["safe"],
        "safe_step_up_rate": counts["safe_step_up"] / counts["safe"],
        "safe_allow_rate": counts["safe_allow"] / counts["safe"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=50_000)
    parser.add_argument("--input", type=Path, default=Path("data/synthetic_endpoints.csv"))
    parser.add_argument("--seed", type=int, default=20260904)
    args = parser.parse_args()

    if not args.input.exists():
        generate(args.rows, args.input, seed=20260903)

    strategies = list(STRATEGY_IDS)
    rates = (0.10, 0.25, 0.40)

    print("model,missing_rate,strategy,false_allow,false_deny,safe_step_up,safe_allow")
    for structured in (False, True):
        for rate in rates:
            for strategy in strategies:
                result = evaluate(
                    args.input,
                    missing_rate=rate,
                    strategy=strategy,
                    structured=structured,
                    seed=args.seed,
                )
                print(
                    f"{result['missing_model']},{rate:.2f},{strategy},"
                    f"{result['false_allow_rate']:.6f},"
                    f"{result['false_deny_rate']:.6f},"
                    f"{result['safe_step_up_rate']:.6f},"
                    f"{result['safe_allow_rate']:.6f}"
                )


if __name__ == "__main__":
    main()
