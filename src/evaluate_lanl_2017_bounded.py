"""Bounded descriptive evaluation for LANL 2017 host telemetry.

This module implements the pre-specified Level-1 outputs in
experiments/external-validation-freeze.md. It performs no threshold fitting and
uses expert/attack labels neither as features nor outcomes.

Raw LANL data must remain outside Git.
"""

from __future__ import annotations

import argparse
import bz2
import json
import math
import resource
import time
from collections import Counter
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, TextIO

from src.lanl_2017_host_adapter import (
    AUTH_EVENT_IDS,
    PROCESS_START_ID,
    StreamingHostFeatureExtractor,
    parse_host_event,
)


@contextmanager
def _open_text(path: Path) -> Iterator[TextIO]:
    if path.suffix.lower() == ".bz2":
        handle = bz2.open(path, "rt", encoding="utf-8", errors="replace")
    else:
        handle = path.open("r", encoding="utf-8", errors="replace")
    try:
        yield handle
    finally:
        handle.close()


def _quantiles(values: list[float]) -> dict[str, float]:
    ordered = sorted(values)
    if not ordered:
        return {}
    result: dict[str, float] = {}
    n = len(ordered)
    for probability in (0.0, 0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99, 1.0):
        index = (n - 1) * probability
        lower = math.floor(index)
        upper = math.ceil(index)
        value = (
            ordered[lower]
            if lower == upper
            else ordered[lower] * (upper - index)
            + ordered[upper] * (index - lower)
        )
        result[f"{probability:g}"] = round(float(value), 6)
    return result


def evaluate_bounded(path: Path, *, max_rows: int = 100_000) -> dict[str, object]:
    if max_rows <= 0:
        raise ValueError("max_rows must be positive")

    extractor = StreamingHostFeatureExtractor()
    event_ids: Counter[int] = Counter()

    processed = rejected = 0
    auth_events = process_starts = auth_failures = 0
    auth_outcome_events = 0
    novel_edges = explicit_credentials = privileged_logons = novel_processes = 0
    guard_identity = guard_anomaly = guard_union = 0
    assurances: list[float] = []
    risks: list[float] = []
    freshness_values: list[float] = []
    first_time: int | None = None
    last_time: int | None = None

    started = time.perf_counter()

    with _open_text(path) as source:
        for raw_line in source:
            if processed >= max_rows:
                break
            line = raw_line.strip()
            if not line:
                continue
            try:
                event = parse_host_event(line)
            except (ValueError, TypeError, json.JSONDecodeError):
                rejected += 1
                continue

            row = extractor.transform(event)
            processed += 1
            event_ids[event.event_id] += 1

            if first_time is None:
                first_time = event.time
            last_time = event.time

            if event.event_id in AUTH_EVENT_IDS:
                auth_events += 1
            if event.event_id == PROCESS_START_ID:
                process_starts += 1
            if event.auth_success is not None:
                auth_outcome_events += 1
            if event.auth_success is False:
                auth_failures += 1

            novel_edges += int(row["new_user_host_edge"])
            explicit_credentials += int(row["explicit_credentials"])
            privileged_logons += int(row["privileged_logon"])
            novel_processes += int(row["new_process_on_host"])

            assurance = float(row["identity_assurance"])
            risk = float(row["anomaly_risk"])
            freshness = float(row["freshness"])
            assurances.append(assurance)
            risks.append(risk)
            freshness_values.append(freshness)

            identity_trigger = assurance < 0.40
            anomaly_trigger = risk > 0.75
            guard_identity += int(identity_trigger)
            guard_anomaly += int(anomaly_trigger)
            guard_union += int(identity_trigger or anomaly_trigger)

    elapsed = time.perf_counter() - started
    if processed == 0:
        raise ValueError("No valid LANL events were processed")

    return {
        "processed": processed,
        "rejected_records": rejected,
        "time_field_first": first_time,
        "time_field_last": last_time,
        "auth_events": auth_events,
        "auth_event_rate": round(auth_events / processed, 6),
        "auth_outcome_events": auth_outcome_events,
        "auth_failures": auth_failures,
        "auth_failure_rate_over_auth_events": round(
            auth_failures / auth_events if auth_events else 0.0, 6
        ),
        "auth_failure_rate_over_outcome_events": round(
            auth_failures / auth_outcome_events if auth_outcome_events else 0.0, 6
        ),
        "process_starts": process_starts,
        "process_start_rate": round(process_starts / processed, 6),
        "novel_user_host_edges": novel_edges,
        "novel_user_host_edge_rate_over_auth_events": round(
            novel_edges / auth_events if auth_events else 0.0, 6
        ),
        "explicit_credential_events": explicit_credentials,
        "privileged_logon_events": privileged_logons,
        "novel_process_starts": novel_processes,
        "novel_process_rate_over_process_starts": round(
            novel_processes / process_starts if process_starts else 0.0, 6
        ),
        "mean_identity_assurance": round(sum(assurances) / processed, 6),
        "mean_anomaly_risk": round(sum(risks) / processed, 6),
        "identity_assurance_quantiles": _quantiles(assurances),
        "anomaly_risk_quantiles": _quantiles(risks),
        "freshness_quantiles": _quantiles(freshness_values),
        "frozen_identity_guard_identity_trigger_count": guard_identity,
        "frozen_identity_guard_anomaly_trigger_count": guard_anomaly,
        "frozen_identity_guard_step_up_count": guard_union,
        "frozen_identity_guard_step_up_rate": round(guard_union / processed, 6),
        "event_id_counts": dict(event_ids.most_common()),
        "elapsed_seconds": round(elapsed, 6),
        "rows_per_second": round(processed / elapsed, 2),
        "peak_rss_kb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run frozen bounded descriptive evaluation on LANL 2017 host events."
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--max-rows", type=int, default=100_000)
    args = parser.parse_args()
    print(json.dumps(evaluate_bounded(args.input, max_rows=args.max_rows), indent=2))


if __name__ == "__main__":
    main()
