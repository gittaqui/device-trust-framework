"""Microbenchmark the core device-trust decision path.

This benchmark isolates in-memory policy evaluation. It excludes telemetry
collection, parsing, network I/O, storage, identity-provider calls, and policy
enforcement, so it must not be interpreted as end-to-end production capacity.
"""

from __future__ import annotations

import argparse
import math
import platform
import statistics
import sys
import time
from dataclasses import dataclass

from trust_model import calculate_trust


REPRESENTATIVE_SIGNALS = (
    {"compliance": 0.95, "endpoint_health": 0.92, "identity_assurance": 0.93, "patch_posture": 0.90, "security_coverage": 0.96, "freshness": 0.92, "threat_risk": 0.05, "anomaly_risk": 0.06},
    {"compliance": 0.20, "endpoint_health": 0.85, "identity_assurance": 0.92, "patch_posture": 0.76, "security_coverage": 0.93, "freshness": 0.90, "threat_risk": 0.08, "anomaly_risk": 0.09},
    {"compliance": 0.90, "endpoint_health": 0.70, "identity_assurance": 0.82, "patch_posture": 0.50, "security_coverage": 0.75, "freshness": 0.15, "threat_risk": 0.25, "anomaly_risk": 0.20},
    {"compliance": 0.96, "endpoint_health": 0.90, "identity_assurance": 0.20, "patch_posture": 0.90, "security_coverage": 0.95, "freshness": 0.90, "threat_risk": 0.20, "anomaly_risk": 0.80},
    {"compliance": 0.90, "endpoint_health": 0.30, "identity_assurance": 0.90, "patch_posture": 0.70, "security_coverage": 0.90, "freshness": 0.90, "threat_risk": 0.95, "anomaly_risk": 0.80},
    {"compliance": 0.80, "endpoint_health": 0.60, "identity_assurance": 0.90, "patch_posture": 0.70, "security_coverage": 0.10, "freshness": 0.80, "threat_risk": 0.30, "anomaly_risk": 0.30},
    {"compliance": 0.55, "endpoint_health": 0.52, "identity_assurance": 0.60, "patch_posture": 0.45, "security_coverage": 0.65, "freshness": 0.42, "threat_risk": 0.50, "anomaly_risk": 0.55},
    {"compliance": 0.95, "endpoint_health": 0.60, "identity_assurance": 0.50, "patch_posture": 0.90, "security_coverage": 0.90, "freshness": 0.90, "threat_risk": 0.70, "anomaly_risk": 0.80},
)

T_CRITICAL_95 = {
    3: 3.182,
    4: 2.776,
    5: 2.571,
    6: 2.447,
    7: 2.365,
    8: 2.306,
    9: 2.262,
}


@dataclass(frozen=True)
class BenchmarkSummary:
    decisions: int
    repetitions: int
    mean_seconds: float
    stdev_seconds: float
    ci95_low_seconds: float
    ci95_high_seconds: float
    throughput_per_second: float
    microseconds_per_decision: float
    coefficient_of_variation_pct: float


def summarize(decisions: int, elapsed_seconds: list[float]) -> BenchmarkSummary:
    """Summarize repeated wall-clock measurements with a 95% t interval."""
    if decisions <= 0:
        raise ValueError("decisions must be positive")
    if len(elapsed_seconds) < 4:
        raise ValueError("at least four repetitions are required")
    if any(value <= 0 for value in elapsed_seconds):
        raise ValueError("elapsed times must be positive")

    repetitions = len(elapsed_seconds)
    mean_seconds = statistics.mean(elapsed_seconds)
    stdev_seconds = statistics.stdev(elapsed_seconds)
    df = repetitions - 1
    if df not in T_CRITICAL_95:
        raise ValueError("supported repetitions are 4 through 10")
    half_width = T_CRITICAL_95[df] * stdev_seconds / math.sqrt(repetitions)

    return BenchmarkSummary(
        decisions=decisions,
        repetitions=repetitions,
        mean_seconds=mean_seconds,
        stdev_seconds=stdev_seconds,
        ci95_low_seconds=mean_seconds - half_width,
        ci95_high_seconds=mean_seconds + half_width,
        throughput_per_second=decisions / mean_seconds,
        microseconds_per_decision=(mean_seconds / decisions) * 1_000_000,
        coefficient_of_variation_pct=(stdev_seconds / mean_seconds) * 100,
    )


def execute_batch(decisions: int) -> dict[str, int]:
    """Execute exactly `decisions` trust evaluations and retain outcome counts."""
    counts = {"ALLOW": 0, "STEP_UP": 0, "DENY": 0}
    for index in range(decisions):
        result = calculate_trust(REPRESENTATIVE_SIGNALS[index % len(REPRESENTATIVE_SIGNALS)])
        counts[result.decision] += 1
    return counts


def benchmark(decisions: int, repetitions: int = 7, warmup_decisions: int = 20_000) -> tuple[BenchmarkSummary, dict[str, int]]:
    """Warm up the interpreter, then measure repeated single-process batches."""
    if repetitions not in range(4, 11):
        raise ValueError("repetitions must be between 4 and 10")

    execute_batch(warmup_decisions)
    measurements: list[float] = []
    counts: dict[str, int] | None = None

    for _ in range(repetitions):
        started = time.perf_counter()
        counts = execute_batch(decisions)
        measurements.append(time.perf_counter() - started)

    assert counts is not None
    return summarize(decisions, measurements), counts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sizes", nargs="+", type=int, default=[10_000, 100_000, 500_000])
    parser.add_argument("--repetitions", type=int, default=7)
    parser.add_argument("--warmup", type=int, default=20_000)
    args = parser.parse_args()

    print(f"Python: {sys.version.split()[0]}")
    print(f"Platform: {platform.platform()}")
    print(f"Repetitions: {args.repetitions}; warmup decisions: {args.warmup:,}")
    print()
    print("| Decisions | Mean s | 95% CI s | Decisions/s | us/decision | CV |")
    print("|---:|---:|---:|---:|---:|---:|")
    for size in args.sizes:
        summary, counts = benchmark(size, args.repetitions, args.warmup)
        print(
            f"| {summary.decisions:,} | {summary.mean_seconds:.6f} | "
            f"{summary.ci95_low_seconds:.6f}-{summary.ci95_high_seconds:.6f} | "
            f"{summary.throughput_per_second:,.0f} | "
            f"{summary.microseconds_per_decision:.3f} | "
            f"{summary.coefficient_of_variation_pct:.2f}% |"
        )
        print(f"<!-- outcome checksum: {counts} -->")


if __name__ == "__main__":
    main()
