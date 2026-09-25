"""Fast semantically equivalent LANL 2017 burn-in evaluator.

This path exists to process large external files within practical runtime limits.
Feature semantics and update order are intentionally identical to
src/lanl_2017_host_adapter.py. Before it may inspect the 6-12 hour evaluation
window, it must exactly reproduce the already-inspected frozen 100,000-event
prefix metrics.
"""

from __future__ import annotations

import argparse
import bz2
import json
import math
import resource
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable, Iterator

import orjson

AUTH_EVENT_IDS = {4624, 4625, 4648, 4672, 4768, 4769, 4770, 4774, 4776}
STATUS_AUTH_IDS = {4768, 4769, 4770, 4774, 4776}
BURN_IN_END = 21_600
EVAL_END = 43_200


def _clip(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


class FastState:
    def __init__(self) -> None:
        self.user_success = defaultdict(int)
        self.user_failure = defaultdict(int)
        self.user_hosts = defaultdict(set)
        self.user_last_seen: dict[str, int] = {}
        self.host_last_seen: dict[str, int] = {}
        self.host_processes = defaultdict(set)

    def snapshot(self) -> dict[str, int]:
        auth_users = set(self.user_success) | set(self.user_failure)
        return {
            "users_with_auth_history": len(auth_users),
            "user_host_sets": len(self.user_hosts),
            "hosts_with_process_history": len(self.host_processes),
            "users_last_seen": len(self.user_last_seen),
            "hosts_last_seen": len(self.host_last_seen),
        }

    def transform(self, raw: dict[str, object]) -> dict[str, object]:
        if "Time" not in raw or "EventID" not in raw:
            raise ValueError("LANL host event requires Time and EventID")

        time_value = int(raw["Time"])
        event_id = int(raw["EventID"])
        host = str(raw.get("Computer") or raw.get("LogHost") or "")
        if not host:
            raise ValueError("LANL host event requires Computer or LogHost")

        user = str(raw.get("UserName") or "<unknown>")
        status = raw.get("Status")
        process = str(raw.get("ProcessName") or "")

        if event_id == 4624:
            auth_success: bool | None = True
        elif event_id == 4625:
            auth_success = False
        elif event_id in STATUS_AUTH_IDS and status is not None:
            auth_success = status == "0x0"
        else:
            auth_success = None

        successes = self.user_success[user]
        failures = self.user_failure[user]
        prior_auth = successes + failures
        prior_failure_rate = failures / prior_auth if prior_auth else 0.0

        new_user_host_edge = (
            1.0
            if event_id in AUTH_EVENT_IDS
            and user != "<unknown>"
            and host not in self.user_hosts[user]
            else 0.0
        )
        new_process_on_host = (
            1.0
            if event_id == 4688
            and process
            and process not in self.host_processes[host]
            else 0.0
        )
        explicit_credentials = 1.0 if event_id == 4648 else 0.0
        privileged_logon = 1.0 if event_id == 4672 else 0.0

        gaps: list[int] = []
        if user in self.user_last_seen:
            gaps.append(max(0, time_value - self.user_last_seen[user]))
        if host in self.host_last_seen:
            gaps.append(max(0, time_value - self.host_last_seen[host]))
        activity_gap = max(gaps) if gaps else 0
        freshness = 1.0 - min(activity_gap / 86_400.0, 1.0)

        current_auth_failure = 1.0 if auth_success is False else 0.0
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

        if auth_success is True:
            self.user_success[user] += 1
        elif auth_success is False:
            self.user_failure[user] += 1
        if event_id in AUTH_EVENT_IDS and user != "<unknown>":
            self.user_hosts[user].add(host)
        if event_id == 4688 and process:
            self.host_processes[host].add(process)
        if user != "<unknown>":
            self.user_last_seen[user] = time_value
        self.host_last_seen[host] = time_value

        return {
            "time": time_value,
            "event_id": event_id,
            "user": user,
            "computer": host,
            "auth_success": auth_success,
            "identity_assurance": round(identity_assurance, 6),
            "anomaly_risk": round(anomaly_risk, 6),
            "freshness": round(freshness, 6),
            "new_user_host_edge": int(new_user_host_edge),
            "explicit_credentials": int(explicit_credentials),
            "privileged_logon": int(privileged_logon),
            "new_process_on_host": int(new_process_on_host),
        }


def _iter_json_lines(paths: Iterable[Path]) -> Iterator[bytes]:
    """Yield logical lines across one or more files, preserving split boundaries."""
    carry = b""
    for path in paths:
        opener = bz2.open if path.suffix.lower() == ".bz2" else open
        with opener(path, "rb") as handle:
            while True:
                block = handle.read(8 * 1024 * 1024)
                if not block:
                    break
                data = carry + block
                parts = data.split(b"\n")
                carry = parts.pop()
                for line in parts:
                    if line:
                        yield line
    if carry.strip():
        yield carry


def _quantiles_from_counts(counts: Counter[float]) -> dict[str, float]:
    if not counts:
        return {}
    ordered = sorted(counts.items())
    total = sum(counts.values())

    def value_at(rank: int) -> float:
        seen = 0
        for value, count in ordered:
            seen += count
            if rank < seen:
                return float(value)
        return float(ordered[-1][0])

    out: dict[str, float] = {}
    for probability in (0.0, 0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99, 1.0):
        index = (total - 1) * probability
        lower, upper = math.floor(index), math.ceil(index)
        low_value, high_value = value_at(lower), value_at(upper)
        value = (
            low_value
            if lower == upper
            else low_value * (upper - index) + high_value * (index - lower)
        )
        out[f"{probability:g}"] = round(float(value), 6)
    return out


def evaluate(paths: list[Path]) -> dict[str, object]:
    state = FastState()
    rejected = burnin_valid = eval_valid = 0
    event_ids: Counter[int] = Counter()
    auth_events = process_starts = auth_failures = auth_outcomes = 0
    novel_edges = novel_processes = explicit = privileged = 0
    guard_identity = guard_anomaly = guard_union = 0
    assurance_counts: Counter[float] = Counter()
    risk_counts: Counter[float] = Counter()
    freshness_counts: Counter[float] = Counter()
    eval_users: set[str] = set()
    eval_hosts: set[str] = set()
    burnin_state: dict[str, int] | None = None

    started = time.perf_counter()
    for line in _iter_json_lines(paths):
        try:
            raw = orjson.loads(line)
            time_value = int(raw["Time"])
        except (orjson.JSONDecodeError, KeyError, TypeError, ValueError):
            rejected += 1
            continue

        if time_value >= EVAL_END:
            break

        if time_value >= BURN_IN_END and burnin_state is None:
            burnin_state = state.snapshot()

        try:
            row = state.transform(raw)
        except (KeyError, TypeError, ValueError):
            rejected += 1
            continue

        if time_value < BURN_IN_END:
            burnin_valid += 1
            continue

        eval_valid += 1
        event_id = int(row["event_id"])
        event_ids[event_id] += 1
        eval_users.add(str(row["user"]))
        eval_hosts.add(str(row["computer"]))

        if event_id in AUTH_EVENT_IDS:
            auth_events += 1
        if event_id == 4688:
            process_starts += 1
        if row["auth_success"] is not None:
            auth_outcomes += 1
        if row["auth_success"] is False:
            auth_failures += 1

        novel_edges += int(row["new_user_host_edge"])
        novel_processes += int(row["new_process_on_host"])
        explicit += int(row["explicit_credentials"])
        privileged += int(row["privileged_logon"])

        assurance = float(row["identity_assurance"])
        risk = float(row["anomaly_risk"])
        freshness = float(row["freshness"])
        assurance_counts[assurance] += 1
        risk_counts[risk] += 1
        freshness_counts[freshness] += 1

        identity_trigger = assurance < 0.40
        anomaly_trigger = risk > 0.75
        guard_identity += int(identity_trigger)
        guard_anomaly += int(anomaly_trigger)
        guard_union += int(identity_trigger or anomaly_trigger)

    elapsed = time.perf_counter() - started
    if eval_valid == 0:
        raise ValueError("No records found in frozen evaluation window")

    return {
        "burn_in": {
            "time_start": 0,
            "time_end_exclusive": BURN_IN_END,
            "valid_records": burnin_valid,
        },
        "evaluation": {
            "time_start": BURN_IN_END,
            "time_end_exclusive": EVAL_END,
            "valid_records": eval_valid,
            "rejected_records_before_stop": rejected,
            "distinct_users": len(eval_users),
            "distinct_hosts": len(eval_hosts),
            "auth_events": auth_events,
            "auth_event_rate": round(auth_events / eval_valid, 6),
            "auth_outcome_events": auth_outcomes,
            "auth_failures": auth_failures,
            "auth_failure_rate_over_auth_events": round(auth_failures / auth_events, 6) if auth_events else 0.0,
            "auth_failure_rate_over_outcome_events": round(auth_failures / auth_outcomes, 6) if auth_outcomes else 0.0,
            "process_starts": process_starts,
            "process_start_rate": round(process_starts / eval_valid, 6),
            "novel_user_host_edges": novel_edges,
            "novel_user_host_edge_rate_over_auth_events": round(novel_edges / auth_events, 6) if auth_events else 0.0,
            "novel_process_starts": novel_processes,
            "novel_process_rate_over_process_starts": round(novel_processes / process_starts, 6) if process_starts else 0.0,
            "explicit_credential_events": explicit,
            "privileged_logon_events": privileged,
            "identity_assurance_quantiles": _quantiles_from_counts(assurance_counts),
            "anomaly_risk_quantiles": _quantiles_from_counts(risk_counts),
            "freshness_quantiles": _quantiles_from_counts(freshness_counts),
            "guard_identity_trigger_count": guard_identity,
            "guard_anomaly_trigger_count": guard_anomaly,
            "guard_step_up_count": guard_union,
            "guard_step_up_rate": round(guard_union / eval_valid, 6),
            "event_id_counts": dict(event_ids.most_common()),
        },
        "state_after_burn_in": burnin_state,
        "state_after_evaluation": state.snapshot(),
        "elapsed_seconds": round(elapsed, 6),
        "rows_per_second_including_burn_in": round((burnin_valid + eval_valid) / elapsed, 2),
        "peak_rss_kb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", nargs="+", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(evaluate(args.input), indent=2))


if __name__ == "__main__":
    main()
