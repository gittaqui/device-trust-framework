"""LANL 2017 day-1 burn-in/evaluation analysis.

The first six hours update streaming state only. The next six hours are reported.
No thresholds are fitted and no attack/benign labels are inferred.
"""

from __future__ import annotations

import argparse
import bz2
import json
import math
import resource
import time
from collections import Counter
from pathlib import Path

from src.lanl_2017_host_adapter import AUTH_EVENT_IDS, PROCESS_START_ID, StreamingHostFeatureExtractor, parse_host_event

BURN_IN_END = 21_600
EVAL_END = 43_200


def _quantiles(values: list[float]) -> dict[str, float]:
    if not values:
        return {}
    ordered = sorted(values)
    n = len(ordered)
    out: dict[str, float] = {}
    for p in (0.0, 0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99, 1.0):
        idx = (n - 1) * p
        lo, hi = math.floor(idx), math.ceil(idx)
        value = ordered[lo] if lo == hi else ordered[lo] * (hi - idx) + ordered[hi] * (idx - lo)
        out[f"{p:g}"] = round(float(value), 6)
    return out


def evaluate(path: Path) -> dict[str, object]:
    extractor = StreamingHostFeatureExtractor()
    rejected = burnin_valid = eval_valid = 0
    ids: Counter[int] = Counter()
    auth = starts = failures = outcome_auth = 0
    novel_edges = novel_processes = explicit = privileged = 0
    guard_identity = guard_anomaly = guard_union = 0
    assurance: list[float] = []
    risk: list[float] = []
    freshness: list[float] = []
    users: set[str] = set()
    hosts: set[str] = set()
    burnin_state: dict[str, int] | None = None

    started = time.perf_counter()
    with bz2.open(path, "rt", encoding="utf-8", errors="replace") as handle:
        for raw in handle:
            line = raw.strip()
            if not line:
                continue
            try:
                event = parse_host_event(line)
            except (ValueError, TypeError, json.JSONDecodeError):
                rejected += 1
                continue

            if event.time >= EVAL_END:
                break

            row = extractor.transform(event)

            if event.time < BURN_IN_END:
                burnin_valid += 1
                continue

            if burnin_state is None:
                burnin_state = {
                    "users_with_auth_history": len(extractor.user_success) + len(set(extractor.user_failure) - set(extractor.user_success)),
                    "user_host_sets": len(extractor.user_hosts),
                    "hosts_with_process_history": len(extractor.host_processes),
                    "users_last_seen": len(extractor.user_last_seen),
                    "hosts_last_seen": len(extractor.host_last_seen),
                }

            eval_valid += 1
            ids[event.event_id] += 1
            users.add(event.user or "<unknown>")
            hosts.add(event.computer)

            if event.event_id in AUTH_EVENT_IDS:
                auth += 1
            if event.event_id == PROCESS_START_ID:
                starts += 1
            if event.auth_success is not None:
                outcome_auth += 1
            if event.auth_success is False:
                failures += 1

            novel_edges += int(row["new_user_host_edge"])
            novel_processes += int(row["new_process_on_host"])
            explicit += int(row["explicit_credentials"])
            privileged += int(row["privileged_logon"])

            a = float(row["identity_assurance"])
            r = float(row["anomaly_risk"])
            f = float(row["freshness"])
            assurance.append(a)
            risk.append(r)
            freshness.append(f)

            gi = a < 0.40
            ga = r > 0.75
            guard_identity += int(gi)
            guard_anomaly += int(ga)
            guard_union += int(gi or ga)

    elapsed = time.perf_counter() - started
    if eval_valid == 0:
        raise ValueError("No events found in evaluation window")

    final_state = {
        "users_with_auth_history": len(extractor.user_success) + len(set(extractor.user_failure) - set(extractor.user_success)),
        "user_host_sets": len(extractor.user_hosts),
        "hosts_with_process_history": len(extractor.host_processes),
        "users_last_seen": len(extractor.user_last_seen),
        "hosts_last_seen": len(extractor.host_last_seen),
    }

    return {
        "burn_in": {"time_start": 0, "time_end_exclusive": BURN_IN_END, "valid_records": burnin_valid},
        "evaluation": {
            "time_start": BURN_IN_END,
            "time_end_exclusive": EVAL_END,
            "valid_records": eval_valid,
            "rejected_records_before_stop": rejected,
            "distinct_users": len(users),
            "distinct_hosts": len(hosts),
            "auth_events": auth,
            "auth_event_rate": round(auth / eval_valid, 6),
            "auth_outcome_events": outcome_auth,
            "auth_failures": failures,
            "auth_failure_rate_over_auth_events": round(failures / auth, 6) if auth else 0.0,
            "auth_failure_rate_over_outcome_events": round(failures / outcome_auth, 6) if outcome_auth else 0.0,
            "process_starts": starts,
            "process_start_rate": round(starts / eval_valid, 6),
            "novel_user_host_edges": novel_edges,
            "novel_user_host_edge_rate_over_auth_events": round(novel_edges / auth, 6) if auth else 0.0,
            "novel_process_starts": novel_processes,
            "novel_process_rate_over_process_starts": round(novel_processes / starts, 6) if starts else 0.0,
            "explicit_credential_events": explicit,
            "privileged_logon_events": privileged,
            "identity_assurance_quantiles": _quantiles(assurance),
            "anomaly_risk_quantiles": _quantiles(risk),
            "freshness_quantiles": _quantiles(freshness),
            "guard_identity_trigger_count": guard_identity,
            "guard_anomaly_trigger_count": guard_anomaly,
            "guard_step_up_count": guard_union,
            "guard_step_up_rate": round(guard_union / eval_valid, 6),
            "event_id_counts": dict(ids.most_common()),
        },
        "state_after_burn_in": burnin_state,
        "state_after_evaluation": final_state,
        "elapsed_seconds": round(elapsed, 6),
        "rows_per_second_including_burn_in": round((burnin_valid + eval_valid) / elapsed, 2),
        "peak_rss_kb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(evaluate(args.input), indent=2))


if __name__ == "__main__":
    main()
