# LANL-2015 second-cohort replication freeze

Date frozen: 2026-10-03

## Purpose

Freeze an untouched replication cohort before inspecting its process, DNS, or flow telemetry. This directly addresses the first-cohort limitation that short-offset controls can change weekday and workload context.

## Frozen cohort

- Dataset: LANL Comprehensive Multi-Source Cyber-Security Events (2015), DOI `10.17021/1179829`.
- Replication targets: red-team rows 26-50 inclusive in existing ordering (Python slice `25:50`).
- Window: +/-600 seconds around each target.
- Entity scope: each target's own red-team user, source computer, and destination computer, as in the first paired analysis.
- Do not inspect cohort telemetry before control selection and feature definitions are fixed.

## Same-weekday control selection

Test offsets in fixed order: `+604800, +1209600, +1814400, -604800, -1209600, -1814400` seconds (plus/minus 7, 14, 21 days). These preserve time-of-day and weekday in the LANL relative-time axis.

Choose the first candidate whose +/-600-second interval starts at or after zero, does not overlap any known red-team +/-600-second interval, and does not overlap an already assigned replication control. If none qualifies, retain the target as unmatched. Do not replace zero-coverage controls.

## Frozen primary replication family

Reuse existing feature definitions unchanged. Primary: process event count, unique process count, process-start count. Secondary: flow event count, unique flow-port count, flow byte count. DNS remains descriptive because first-cohort coverage was sparse.

## Pre-specified paired analysis

For each primary feature report target/control medians, median paired difference, target-higher/tied/control-higher counts, exact two-sided sign test on non-tied pairs, and a 95% Wilson interval for the target-higher proportion among non-tied pairs. Treat the three process measures as a dependent replication family rather than three independent discoveries.

## Claim firewall

Controls are matched non-red-team times, not verified benign sessions. This replication cannot establish sensitivity, specificity, false-positive rate, ROC/AUC, causal attack effects, or production security effectiveness. LANL does not measure MDM compliance, patch posture, EDR health, or proprietary identity-risk scores; this is partial external contextual evidence, not full-model validation.

## Fresh methodological basis

A 2026 IEEE study, `Are Temporal Graph Based Intrusion Detection Results Trustworthy? A Dataset Audit and Evaluation Framework`, DOI `10.1109/IMNS67862.2026.11655312`, identifies temporal concentration and node-identity leakage as mechanisms that can inflate intrusion-detection evaluation and advocates attack-aware chronological evaluation. This motivates stricter temporal control rather than optimizing the first cohort.

## Stopping rule

Process all 25 replication targets under the fixed selector. Retain unmatched targets and zero-coverage controls. Report negative or null replication findings unchanged.

## Next step

Implement cohort-range and same-weekday control selection, add deterministic tests, execute untouched rows 26-50 in CI, and evaluate the frozen primary process family before any model or threshold change.
