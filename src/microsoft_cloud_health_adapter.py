"""Component-level endpoint-health validation using Microsoft's Cloud Monitoring Dataset.

This module intentionally validates only a reliability/endpoint-health proxy. It
must not be interpreted as full Device Trust validation because the source data
contains aggregate production crash-rate time series rather than per-device
Intune/Entra/Defender state.

Upstream dataset:
https://github.com/microsoft/cloud-monitoring-dataset
License: MIT
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from statistics import median
from typing import Iterable, Sequence


@dataclass(frozen=True)
class CrashPoint:
    timestamp: str
    value: float
    label: int


@dataclass(frozen=True)
class ScoredPoint:
    timestamp: str
    value: float
    label: int
    baseline_median: float
    baseline_mad: float
    robust_z: float
    anomaly_risk: float
    endpoint_health: float


def read_series(path: Path) -> list[CrashPoint]:
    points: list[CrashPoint] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"TimeStamp", "Value", "Label"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"{path} must contain columns {sorted(required)}")
        for row in reader:
            label = int(row["Label"])
            if label not in {0, 1}:
                raise ValueError(f"Unexpected anomaly label {label!r} in {path}")
            points.append(
                CrashPoint(
                    timestamp=row["TimeStamp"],
                    value=float(row["Value"]),
                    label=label,
                )
            )
    return points


def _robust_scale(history: Sequence[float], center: float) -> float:
    mad = median(abs(value - center) for value in history)
    return 1.4826 * mad


def causal_robust_scores(
    points: Sequence[CrashPoint], *, window: int = 48, risk_scale: float = 3.0
) -> list[ScoredPoint]:
    """Score each point using only the preceding ``window`` observations.

    Expert anomaly labels are carried through solely for evaluation and are never
    used to compute the score. Positive deviations are treated as reliability
    degradation because the chosen source series are application crash rates.
    """
    if window < 3:
        raise ValueError("window must be at least 3")
    if risk_scale <= 0:
        raise ValueError("risk_scale must be positive")
    if len(points) <= window:
        return []

    scored: list[ScoredPoint] = []
    for index in range(window, len(points)):
        history = [p.value for p in points[index - window : index]]
        center = median(history)
        scale = _robust_scale(history, center)
        current = points[index]

        if scale > 1e-12:
            robust_z = max(0.0, (current.value - center) / scale)
        else:
            robust_z = 50.0 if current.value > center else 0.0

        anomaly_risk = robust_z / (robust_z + risk_scale) if robust_z > 0 else 0.0
        endpoint_health = 1.0 - anomaly_risk
        scored.append(
            ScoredPoint(
                timestamp=current.timestamp,
                value=current.value,
                label=current.label,
                baseline_median=center,
                baseline_mad=scale / 1.4826 if scale > 0 else 0.0,
                robust_z=robust_z,
                anomaly_risk=anomaly_risk,
                endpoint_health=endpoint_health,
            )
        )
    return scored


def roc_auc(labels: Sequence[int], scores: Sequence[float]) -> float:
    """Compute ROC AUC using average ranks for ties, without external packages."""
    if len(labels) != len(scores):
        raise ValueError("labels and scores must have equal length")
    positives = sum(label == 1 for label in labels)
    negatives = sum(label == 0 for label in labels)
    if positives == 0 or negatives == 0:
        raise ValueError("ROC AUC requires both positive and negative labels")

    ordered = sorted(enumerate(scores), key=lambda item: item[1])
    ranks = [0.0] * len(scores)
    cursor = 0
    while cursor < len(ordered):
        end = cursor + 1
        while end < len(ordered) and ordered[end][1] == ordered[cursor][1]:
            end += 1
        average_rank = ((cursor + 1) + end) / 2.0
        for offset in range(cursor, end):
            ranks[ordered[offset][0]] = average_rank
        cursor = end

    positive_rank_sum = sum(rank for rank, label in zip(ranks, labels) if label == 1)
    return (positive_rank_sum - positives * (positives + 1) / 2.0) / (positives * negatives)


def evaluate(points: Sequence[CrashPoint], *, window: int = 48) -> dict[str, float | int]:
    scored = causal_robust_scores(points, window=window)
    if not scored:
        raise ValueError("series is too short for the requested causal window")
    labels = [point.label for point in scored]
    risks = [point.anomaly_risk for point in scored]
    raw = [point.value for point in scored]
    positives = sum(labels)
    negatives = len(labels) - positives

    return {
        "evaluated_points": len(scored),
        "expert_anomalies": positives,
        "expert_normal": negatives,
        "raw_value_auc": round(roc_auc(labels, raw), 6),
        "causal_robust_risk_auc": round(roc_auc(labels, risks), 6),
    }


def evaluate_paths(paths: Iterable[Path], *, window: int = 48) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    for path in paths:
        metrics = evaluate(read_series(path), window=window)
        results.append({"file": str(path), **metrics})
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate Microsoft crash-rate health proxies.")
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--window", type=int, default=48)
    args = parser.parse_args()
    print(json.dumps(evaluate_paths(args.inputs, window=args.window), indent=2))


if __name__ == "__main__":
    main()
