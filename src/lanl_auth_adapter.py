"""Streaming adapter for LANL authentication telemetry.

This module converts the LANL Comprehensive Multi-Source Cyber-Security Events
authentication format into normalized research features for the Device Trust
Framework.

It intentionally does NOT label these proxies as Intune compliance, Entra risk,
or any commercial product score.

Expected LANL auth fields:
    time,source_user,destination_user,source_computer,destination_computer,
    authentication_type,logon_type,orientation,success_failure

Example:
    1,C625$@DOM1,U147@DOM1,C625,C625,Negotiate,Batch,LogOn,Success
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, TextIO


@dataclass(frozen=True)
class AuthEvent:
    time: int
    source_user: str
    destination_user: str
    source_computer: str
    destination_computer: str
    authentication_type: str
    logon_type: str
    orientation: str
    success: bool


def _clip(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def parse_auth_line(line: str) -> AuthEvent:
    """Parse one LANL authentication line."""
    fields = next(csv.reader([line]))
    if len(fields) != 9:
        raise ValueError(f"Expected 9 fields, received {len(fields)}")

    result = fields[8].strip().lower()
    if result not in {"success", "fail", "failure"}:
        raise ValueError(f"Unknown authentication result: {fields[8]!r}")

    return AuthEvent(
        time=int(fields[0]),
        source_user=fields[1],
        destination_user=fields[2],
        source_computer=fields[3],
        destination_computer=fields[4],
        authentication_type=fields[5],
        logon_type=fields[6],
        orientation=fields[7],
        success=result == "success",
    )


class StreamingAuthFeatureExtractor:
    """Derive explainable authentication-risk proxies from event history.

    The implementation uses compact aggregate state suitable for large streams.
    Features are deliberately simple so that each value remains auditable.
    """

    def __init__(self) -> None:
        self.user_success = defaultdict(int)
        self.user_failure = defaultdict(int)
        self.user_hosts: dict[str, set[str]] = defaultdict(set)
        self.user_last_seen: dict[str, int] = {}
        self.host_last_seen: dict[str, int] = {}

    def transform(self, event: AuthEvent) -> dict[str, object]:
        user = event.source_user
        host = event.destination_computer

        successes = self.user_success[user]
        failures = self.user_failure[user]
        prior_total = successes + failures

        prior_failure_rate = failures / prior_total if prior_total else 0.0
        new_user_host_edge = 1.0 if host not in self.user_hosts[user] else 0.0

        prior_user_time = self.user_last_seen.get(user)
        prior_host_time = self.host_last_seen.get(host)

        # Recency uses a one-day reference window. LANL timestamps are seconds
        # from an anonymized epoch, so only relative time is used.
        user_gap = 0 if prior_user_time is None else max(0, event.time - prior_user_time)
        host_gap = 0 if prior_host_time is None else max(0, event.time - prior_host_time)
        activity_gap = max(user_gap, host_gap)
        freshness = 1.0 - min(activity_gap / 86_400.0, 1.0)

        # Authentication risk proxy. Novel user-host edges and prior failures
        # increase risk. Failed current events receive an additional penalty.
        current_failure = 0.0 if event.success else 1.0
        auth_risk = _clip(
            0.45 * prior_failure_rate
            + 0.35 * new_user_host_edge
            + 0.20 * current_failure
        )

        identity_assurance = _clip(1.0 - auth_risk)
        anomaly_risk = _clip(
            0.65 * new_user_host_edge
            + 0.35 * prior_failure_rate
        )

        row = {
            "time": event.time,
            "source_user": user,
            "destination_computer": host,
            "authentication_type": event.authentication_type,
            "logon_type": event.logon_type,
            "success": int(event.success),
            "identity_assurance": round(identity_assurance, 6),
            "anomaly_risk": round(anomaly_risk, 6),
            "freshness": round(freshness, 6),
            "new_user_host_edge": int(new_user_host_edge),
            "prior_failure_rate": round(prior_failure_rate, 6),
        }

        if event.success:
            self.user_success[user] += 1
        else:
            self.user_failure[user] += 1

        self.user_hosts[user].add(host)
        self.user_last_seen[user] = event.time
        self.host_last_seen[host] = event.time

        return row


def iter_auth_events(handle: TextIO) -> Iterator[AuthEvent]:
    for raw_line in handle:
        line = raw_line.strip()
        if not line:
            continue
        yield parse_auth_line(line)


def convert(
    input_path: Path,
    output_path: Path,
    *,
    max_rows: int | None = None,
    sample_every: int = 1,
) -> int:
    """Convert LANL auth telemetry to normalized proxy features.

    `sample_every` controls output density while every input event still updates
    history. For example, `sample_every=100` writes one feature row per 100
    processed events but retains full streaming state.
    """
    if sample_every < 1:
        raise ValueError("sample_every must be at least 1")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    extractor = StreamingAuthFeatureExtractor()

    fieldnames = [
        "time",
        "source_user",
        "destination_computer",
        "authentication_type",
        "logon_type",
        "success",
        "identity_assurance",
        "anomaly_risk",
        "freshness",
        "new_user_host_edge",
        "prior_failure_rate",
    ]

    processed = 0
    written = 0

    with input_path.open("r", encoding="utf-8", errors="replace") as source, output_path.open(
        "w", newline="", encoding="utf-8"
    ) as destination:
        writer = csv.DictWriter(destination, fieldnames=fieldnames)
        writer.writeheader()

        for event in iter_auth_events(source):
            processed += 1
            features = extractor.transform(event)

            if processed % sample_every == 0:
                writer.writerow(features)
                written += 1

            if max_rows is not None and processed >= max_rows:
                break

    print(f"Processed {processed:,} authentication events; wrote {written:,} rows")
    return written


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert LANL authentication telemetry to trust-feature proxies."
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-rows", type=int, default=None)
    parser.add_argument(
        "--sample-every",
        type=int,
        default=1,
        help="Write one output row for every N processed events.",
    )
    args = parser.parse_args()

    convert(
        args.input,
        args.output,
        max_rows=args.max_rows,
        sample_every=args.sample_every,
    )


if __name__ == "__main__":
    main()
