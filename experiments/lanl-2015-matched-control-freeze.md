# LANL-2015 matched non-red-team control protocol

Date frozen: 2026-09-30

## Purpose

This protocol freezes the first matched control cohort before comparative process/DNS/flow feature analysis. It supplements `experiments/external-validation-freeze.md`.

The term **benign control is intentionally avoided**. LANL supplies exact red-team authentication labels, but absence from `redteam.txt` does not establish benignness. The comparator is a **matched non-red-team temporal control**.

## Frozen target cohort

- Dataset: LANL Comprehensive Multi-Source Cyber-Security Events (2015), DOI `10.17021/1179829`.
- Target labels: first 25 rows in red-team label order, matching the completed bounded extraction.
- Target geometry: +/-600 seconds per label.
- Focus entities: users/computers determined only from those 25 target labels. No process, DNS, flow, or future authentication outcome is used to choose controls.

## Control-selection rule

For each selected target timestamp `t`, test offsets in this fixed order: `+86400, +172800, +259200, +604800, -86400, -172800, -259200, -604800` seconds.

Choose the first candidate whose +/-600-second interval (1) starts at or after epoch second 0, (2) does not overlap any +/-600-second interval around any of the 749 known red-team timestamps, and (3) does not overlap a control interval already assigned to an earlier target. If none qualifies, retain the target as unmatched. Do not widen the search after inspecting telemetry.

This deterministic design approximately preserves time-of-day for 1/2/3/7-day shifts without looking at telemetry outcomes. It does not guarantee equivalent weekday, workload, user activity, or benign status.

## Extraction and analysis

Use the same focus-user/focus-computer set and source filtering rules as the target extraction. A zero-event control remains a valid zero-coverage control and is not replaced.

Permitted comparisons are descriptive target-centered versus matched non-red-team features defined before inspecting differences. Any feature invented after seeing target/control differences is exploratory and requires a new untouched cohort for confirmatory use.

## Claim boundary

Differences are not attack-detection rates, false-positive rates, causal effects, or proof that controls are benign. No MDM compliance, patch posture, EDR health, or proprietary identity-risk variable is inferred from LANL telemetry.

## Stopping and audit rules

Process all 25 targets using the fixed offset order. Retain unmatched targets and zero-coverage controls. The manifest must record target count, total red-team timestamps used for exclusion, offset ordering, window radius, each selected control timestamp/offset, unmatched targets, merged control windows, and the explicit unlabeled-control warning.

## Next step

Generate the manifest from `redteam.txt`, run the existing bounded remote context readers against the frozen control windows with the identical entity filter, and report coverage/count distributions without tuning the selector or trust-model thresholds.
