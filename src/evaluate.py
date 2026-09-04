"""Evaluate binary compliance versus the proposed trust model."""

from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path

# Allow direct execution from repository root.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from trust_model import binary_compliance_decision, calculate_trust


def load_signals(row: dict[str, str]) -> dict[str, float]:
    names = [
        "compliance", "endpoint_health", "identity_assurance",
        "patch_posture", "security_coverage", "freshness",
        "threat_risk", "anomaly_risk",
    ]
    return {name: float(row[name]) for name in names}


def evaluate(input_path: Path) -> dict[str, object]:
    counts = {
        "rows": 0,
        "safe": 0,
        "unsafe": 0,
        "binary_false_allow": 0,
        "binary_false_deny": 0,
        "trust_false_allow": 0,
        "trust_false_deny": 0,
        "trust_step_up": 0,
        "trust_allow": 0,
        "trust_deny": 0,
    }

    started = time.perf_counter()

    with input_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)

        for row in reader:
            counts["rows"] += 1
            safe = row["safe_for_ordinary_access"] == "1"
            counts["safe" if safe else "unsafe"] += 1

            signals = load_signals(row)

            binary = binary_compliance_decision(signals["compliance"])
            trust = calculate_trust(signals)

            if not safe and binary == "ALLOW":
                counts["binary_false_allow"] += 1
            if safe and binary == "DENY":
                counts["binary_false_deny"] += 1

            if not safe and trust.decision == "ALLOW":
                counts["trust_false_allow"] += 1
            if safe and trust.decision == "DENY":
                counts["trust_false_deny"] += 1

            counts[f"trust_{trust.decision.lower()}"] += 1

    elapsed = time.perf_counter() - started
    rows = counts["rows"]

    return {
        **counts,
        "elapsed_seconds": elapsed,
        "evaluations_per_second": rows / elapsed if elapsed else float("inf"),
        "binary_false_allow_rate": counts["binary_false_allow"] / counts["unsafe"],
        "binary_false_deny_rate": counts["binary_false_deny"] / counts["safe"],
        "trust_false_allow_rate": counts["trust_false_allow"] / counts["unsafe"],
        "trust_false_deny_rate": counts["trust_false_deny"] / counts["safe"],
    }


def print_results(result: dict[str, object]) -> None:
    print("Device Trust Baseline Evaluation")
    print("=" * 34)
    print(f"Rows: {result['rows']:,}")
    print(f"Safe sessions: {result['safe']:,}")
    print(f"Unsafe sessions: {result['unsafe']:,}")
    print()
    print("Binary compliance")
    print(f"  False-allow rate: {result['binary_false_allow_rate']:.2%}")
    print(f"  False-deny rate:  {result['binary_false_deny_rate']:.2%}")
    print()
    print("Multidimensional trust")
    print(f"  False-allow rate: {result['trust_false_allow_rate']:.2%}")
    print(f"  False-deny rate:  {result['trust_false_deny_rate']:.2%}")
    print(f"  ALLOW:   {result['trust_allow']:,}")
    print(f"  STEP_UP: {result['trust_step_up']:,}")
    print(f"  DENY:    {result['trust_deny']:,}")
    print()
    print(f"Evaluation time: {result['elapsed_seconds']:.4f}s")
    print(f"Throughput: {result['evaluations_per_second']:,.0f} rows/s")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("data/synthetic_endpoints.csv"))
    args = parser.parse_args()

    result = evaluate(args.input)
    print_results(result)


if __name__ == "__main__":
    main()
