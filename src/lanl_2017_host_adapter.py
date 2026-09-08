"""Streaming adapter for LANL 2017 Unified Host and Network host events.

The LANL release provides one JSON object per line. This adapter derives
transparent authentication/host-behavior proxies without relabeling them as
Intune, Entra, Defender, or production trust scores.

Official source:
https://csr.lanl.gov/data/2017/
Dataset citation DOI: 10.1142/9781786345646_001
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, TextIO


AUTH_EVENT_IDS = {4624, 4625, 4648, 4672, 4768, 4769, 4770, 4774, 4776}
PROCESS_EVENT_IDS = {4688, 4689}
SUCCESS_LOGON_ID = 4624
FAILED_LOGON_ID = 4625
EXPLICIT_CREDENTIAL_ID = 4648
PRIVILEGE_ID = 4672
PROCESS_START_ID = 4688


def _clip(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


@dataclass(frozen=True)
class HostEvent:
    time: int
    event_id: int
    computer: str
    user: str | None = None
    source: str | None = None
    destination: str | None = None
    status: str | None = None
    logon_type: int | None = None
    process_name: str | None = None
    parent_process_name: str | None = None

    @property
    def auth_success(self) -> bool | None:
        if self.event_id == SUCCESS_LOGON_ID:
            return True
        if self.event_id == FAILED_LOGON_ID:
            return False
        if self.event_id in {4768, 4769, 4770, 4774, 4776} and self.status is not None:
            return self.status == "0x0"
        return None


def parse_host_event(line: str) -> HostEvent:
    """Parse one LANL 2017 host-event JSON line."""
    raw = json.loads(line)
    if "Time" not in raw or "EventID" not in raw:
        raise ValueError("LANL host event requires Time and EventID")

    computer = raw.get("Computer") or raw.get("LogHost") or ""
    if not computer:
        raise ValueError("LANL host event requires Computer or LogHost")

    logon_type = raw.get("LogonType")
    return HostEvent(
        time=int(raw["Time"]),
        event_id=int(raw["EventID"]),
        computer=str(computer),
        user=raw.get("UserName"),
        source=raw.get("Source"),
        destination=raw.get("Destination"),
        status=raw.get("Status"),
        logon_type=int(logon_type) if logon_type is not None else None,
        process_name=raw.get("ProcessName"),
        parent_process_name=raw.get("ParentProcessName"),
    )


class StreamingHostFeatureExtractor:
    """Derive auditable behavioral proxies from prior event history only.

    Features are computed before updating state for the current event to avoid
    direct target leakage from the current observation into its history-based
    novelty/failure features.
    """

    def __init__(self) -> None:
        self.user_success = defaultdict(int)
        self.user_failure = defaultdict(int)
        self.user_hosts: dict[str, set[str]] = defaultdict(set)
        self.user_last_seen: dict[str, int] = {}
        self.host_last_seen: dict[str, int] = {}
        self.host_processes: dict[str, set[str]] = defaultdict(set)

    def transform(self, event: HostEvent) -> dict[str, object]:
        user = event.user or "<unknown>"
        host = event.computer

        successes = self.user_success[user]
        failures = self.user_failure[user]
        prior_auth = successes + failures
        prior_failure_rate = failures / prior_auth if prior_auth else 0.0

        is_auth = event.event_id in AUTH_EVENT_IDS
        new_user_host_edge = (
            1.0 if is_auth and user != "<unknown>" and host not in self.user_hosts[user] else 0.0
        )

        process = event.process_name or ""
        new_process_on_host = (
            1.0
            if event.event_id == PROCESS_START_ID
            and process
            and process not in self.host_processes[host]
            else 0.0
        )

        explicit_credentials = 1.0 if event.event_id == EXPLICIT_CREDENTIAL_ID else 0.0
        privileged_logon = 1.0 if event.event_id == PRIVILEGE_ID else 0.0

        prior_user_time = self.user_last_seen.get(user)
        prior_host_time = self.host_last_seen.get(host)
        gaps = []
        if prior_user_time is not None:
            gaps.append(max(0, event.time - prior_user_time))
        if prior_host_time is not None:
            gaps.append(max(0, event.time - prior_host_time))
        activity_gap = max(gaps) if gaps else 0
        freshness = 1.0 - min(activity_gap / 86_400.0, 1.0)

        current_auth_failure = 1.0 if event.auth_success is False else 0.0

        # Research proxy only. Weights are intentionally explicit and are not
        # asserted to be optimal or equivalent to any product risk score.
        anomaly_risk = _clip(
            0.35 * new_user_host_edge
            + 0.25 * prior_failure_rate
            + 0.15 * explicit_credentials
            + 0.10 * privileged_logon
            + 0.15 * new_process_on_host
        )
        identity_assurance = _clip(
            1.0
            - (
                0.45 * prior_failure_rate
                + 0.25 * new_user_host_edge
                + 0.20 * current_auth_failure
                + 0.10 * explicit_credentials
            )
        )

        row = {
            "time": event.time,
            "event_id": event.event_id,
            "computer": host,
            "user": user,
            "identity_assurance": round(identity_assurance, 6),
            "anomaly_risk": round(anomaly_risk, 6),
            "freshness": round(freshness, 6),
            "new_user_host_edge": int(new_user_host_edge),
            "prior_failure_rate": round(prior_failure_rate, 6),
            "explicit_credentials": int(explicit_credentials),
            "privileged_logon": int(privileged_logon),
            "new_process_on_host": int(new_process_on_host),
        }

        self._update(event, user, host, process)
        return row

    def _update(self, event: HostEvent, user: str, host: str, process: str) -> None:
        if event.auth_success is True:
            self.user_success[user] += 1
        elif event.auth_success is False:
            self.user_failure[user] += 1

        if event.event_id in AUTH_EVENT_IDS and user != "<unknown>":
            self.user_hosts[user].add(host)

        if event.event_id == PROCESS_START_ID and process:
            self.host_processes[host].add(process)

        if user != "<unknown>":
            self.user_last_seen[user] = event.time
        self.host_last_seen[host] = event.time


def iter_host_events(handle: TextIO) -> Iterator[HostEvent]:
    for raw_line in handle:
        line = raw_line.strip()
        if line:
            yield parse_host_event(line)


def summarize(input_path: Path, *, max_rows: int | None = None) -> dict[str, float | int]:
    """Stream a LANL host file and return a bounded reproducibility summary."""
    extractor = StreamingHostFeatureExtractor()
    processed = 0
    auth_events = 0
    process_starts = 0
    auth_failures = 0
    novel_edges = 0
    explicit_creds = 0
    privileged = 0
    novel_processes = 0
    risk_sum = 0.0
    assurance_sum = 0.0

    with input_path.open("r", encoding="utf-8", errors="replace") as source:
        for event in iter_host_events(source):
            row = extractor.transform(event)
            processed += 1
            if event.event_id in AUTH_EVENT_IDS:
                auth_events += 1
            if event.event_id == PROCESS_START_ID:
                process_starts += 1
            if event.auth_success is False:
                auth_failures += 1
            novel_edges += int(row["new_user_host_edge"])
            explicit_creds += int(row["explicit_credentials"])
            privileged += int(row["privileged_logon"])
            novel_processes += int(row["new_process_on_host"])
            risk_sum += float(row["anomaly_risk"])
            assurance_sum += float(row["identity_assurance"])

            if max_rows is not None and processed >= max_rows:
                break

    if processed == 0:
        raise ValueError("No LANL host events were processed")

    return {
        "processed": processed,
        "auth_events": auth_events,
        "process_starts": process_starts,
        "auth_failures": auth_failures,
        "novel_user_host_edges": novel_edges,
        "explicit_credential_events": explicit_creds,
        "privileged_logon_events": privileged,
        "novel_process_starts": novel_processes,
        "mean_identity_assurance": round(assurance_sum / processed, 6),
        "mean_anomaly_risk": round(risk_sum / processed, 6),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Summarize LANL 2017 Windows host events into research proxies."
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--max-rows", type=int, default=None)
    args = parser.parse_args()

    summary = summarize(args.input, max_rows=args.max_rows)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
