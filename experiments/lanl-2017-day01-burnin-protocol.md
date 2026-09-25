# LANL 2017 Day-1 Burn-in / Evaluation Protocol

Date frozen: 2026-09-25

## Purpose

The first frozen 100,000-event LANL prefix exposed a cold-start artifact: the streaming adapter began with empty user-host and host-process history, so first-seen counts were inflated by initialization. This follow-up separates state accumulation from reported evaluation **before inspecting later day-1 results**.

## Fixed temporal windows

LANL's `Time` field is treated as elapsed seconds within the released sequence.

- **Burn-in:** `0 <= Time < 21,600` (first 6 hours)
- **Evaluation:** `21,600 <= Time < 43,200` (next 6 hours)
- Events at or after `Time=43,200` are not inspected by this experiment.

The burn-in interval updates all adapter state but contributes no reported proxy-performance counts.

## Frozen adapter and policy state

Use `src/lanl_2017_host_adapter.py` without changing:

- feature definitions;
- proxy weights;
- history-update order;
- identity-assurance guard threshold `< 0.40`;
- anomaly-risk guard threshold `> 0.75`.

No threshold fitting or outcome-based tuning is permitted.

## Pre-specified evaluation outputs

For the 6-hour evaluation interval report:

1. valid and rejected records;
2. event-ID distribution;
3. authentication-related event count/rate;
4. process-start count/rate;
5. authentication-failure count/rate;
6. first-seen user-host edge count/rate;
7. first-seen process-on-host count/rate;
8. explicit-credential and privileged-logon counts;
9. identity-assurance quantiles;
10. anomaly-risk quantiles;
11. freshness quantiles;
12. frozen identity/anomaly guard STEP_UP count/rate;
13. number of distinct users and hosts observed during evaluation;
14. state cardinalities after burn-in and after evaluation;
15. throughput and peak RSS if measured reproducibly.

## Interpretation boundary

This remains **Level-1 external unlabeled telemetry plausibility**.

Permitted: describing proxy distributions and frozen guard challenge frequency after temporal burn-in.

Not permitted: false-positive/false-negative rates, attack detection, precision/recall, or full Device Trust effectiveness.

## Stopping rule

Process the complete evaluation interval unless a data-integrity or parser failure prevents completion. Negative or inconvenient findings are retained.
