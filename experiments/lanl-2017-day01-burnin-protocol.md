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


## Execution acceleration rule

The raw day-1 archive is large enough that single-process bzip2 decompression can exceed constrained research-runner time limits. A fast path may therefore use `src/evaluate_lanl_2017_fast.py`, which preserves the frozen feature formulas and history-update order while using `orjson` and bounded frequency counters.

Before the fast path may inspect any event at `Time >= 21,600`, it must reproduce the already-inspected first-100,000-event frozen prefix metrics exactly. On 2026-09-25 it matched all key prefix outputs exactly: 100,000 processed; 45,743 authentication events; 40,371 process starts; 1,008 authentication failures; 7,374 novel user-host edges; 1,295 explicit-credential events; 13,495 privileged-logon events; 26,801 novel process starts; mean identity assurance 0.973553; mean anomaly risk 0.084060; and 417 frozen guard challenges.

This equivalence check was completed before opening the 6-12 hour evaluation window.
