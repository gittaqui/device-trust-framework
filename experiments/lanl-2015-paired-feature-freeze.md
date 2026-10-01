# LANL-2015 paired context feature freeze

Date frozen: 2026-09-30

## Purpose

This document freezes the first paired process/DNS/flow feature set before any matched target/control feature differences are computed. It extends `lanl-2015-matched-control-freeze.md`.

The comparison remains descriptive. Controls are matched non-red-team temporal controls, not verified benign traffic.

## Pairing and entity scope

For each of the first 25 red-team authentication targets, use its already-frozen matched control timestamp. Both target and control use the same +/-600-second window geometry.

Feature extraction is **pair-specific**:
- process rows are retained when the row user equals the target user or the row computer equals either target source/destination computer;
- DNS rows are retained when source or resolved computer equals either target source/destination computer;
- flow rows are retained when source or destination computer equals either target source/destination computer.

No telemetry value is used to choose a control or alter the entity set.

## Frozen features

### Process
1. `proc_event_count`
2. `proc_unique_process_count`
3. `proc_start_count`
4. `proc_end_count`

### DNS
5. `dns_event_count`
6. `dns_unique_resolved_computer_count`

### Flow
7. `flow_event_count`
8. `flow_unique_peer_computer_count`
9. `flow_unique_port_count`
10. `flow_packet_count_sum`
11. `flow_byte_count_sum`
12. `flow_duration_sum`
13. `flow_numeric_complete_count`

The feature list is derived from the published LANL source schemas, not from observed target/control separation. Unknown numeric flow fields are never converted to zero; aggregate numeric sums use only parseable rows and `flow_numeric_complete_count` records how many rows contributed complete duration/packet/byte values.

## Frozen descriptive outputs

For each feature report:
- number of matched pairs;
- target median;
- control median;
- median paired difference `target - control`;
- target-greater, equal, and control-greater pair counts.

Do not report these as sensitivity, specificity, false-positive rate, causal effect, or production detection performance.

No feature selection, threshold fitting, trust-model weight tuning, or classifier training is permitted on this 25-pair comparison.

## Leakage and evaluation guardrails

The first comparative pass uses only the frozen 25 target/control pairs. Any feature invented after viewing these differences is exploratory and must be evaluated on a later untouched temporal cohort.

Recent intrusion-detection evaluation work has specifically highlighted temporal concentration and identity leakage as ways apparently strong results can be inflated. This project therefore keeps matching deterministic, preserves time ordering, and prohibits outcome-driven control replacement.

## Claim boundary

LANL process/DNS/flow telemetry is independent enterprise evidence but is not MDM compliance, patch posture, EDR health, or proprietary identity-risk ground truth. The paired analysis tests whether simple contextual telemetry distributions differ around known red-team authentication timestamps versus matched non-red-team times for the same implicated entities. It does not validate the full device-trust policy.
