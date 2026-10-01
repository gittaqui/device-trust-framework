# LANL-2015 paired target/control context results

Date: 2026-09-30

**Status:** First descriptive paired external-telemetry comparison using the feature set frozen in `experiments/lanl-2015-paired-feature-freeze.md`. This is not a classifier-performance result.

## Protocol

- Dataset: LANL Comprehensive Multi-Source Cyber-Security Events (2015), DOI `10.17021/1179829`.
- Target cohort: first 25 red-team authentication labels.
- Window: +/-600 seconds.
- Matched non-red-team controls: frozen before feature comparison.
- Matched pairs: 24.
- Unmatched targets retained: 1.
- Control offsets actually used: +1 day (10), +2 days (5), +3 days (3), +7 days (2), -1 day (3), -2 days (1).
- Features were defined from source schemas before target/control differences were inspected.
- Each pair uses the target's own user/source/destination-computer entity set; the comparison no longer uses the union of all 25 target entities.

## Frozen descriptive results

| Feature | Target median | Control median | Median paired difference | Target > control |
|---|---:|---:|---:|---:|
| Process events | 37.5 | 9.0 | +21.5 | 21/24 |
| Unique processes | 13.0 | 4.5 | +7.0 | 22/24 |
| Process starts | 28.0 | 7.5 | +16.5 | 20/24 |
| Process ends | 2.0 | 0.0 | +0.5 | 12/24 |
| DNS events | 0.0 | 0.0 | 0.0 | 1/24 |
| Unique DNS resolutions | 0.0 | 0.0 | 0.0 | 0/24 |
| Flow events | 179.0 | 120.0 | +115.5 | 17/24 |
| Unique flow peers | 1.5 | 1.0 | 0.0 | 10/24 |
| Unique flow ports | 176.5 | 121.5 | +97.5 | 17/24 |
| Flow packet count | 1,066.5 | 730.0 | +404.5 | 16/24 |
| Flow byte count | 105,462 | 71,471 | +69,780.5 | 17/24 |

## Interpretation

The most consistent first-cohort difference is **process activity**: process-event count, unique-process count, and process-start count are higher in a large majority of matched red-team-centered windows.

DNS contributes little in this cohort because both sides are overwhelmingly zero under the pair-specific entity filter.

Flow activity is higher in the aggregate paired summary, but this result is less stable under an exploratory offset-stratified diagnostic. Among the ten +1-day controls, the median flow-event difference is only +8 events, while the +2/+3-day strata show much larger positive differences and the two +7-day pairs are mixed. This means the aggregate flow difference may be sensitive to temporal/workload matching and should not be used as confirmatory evidence from this cohort.

The process difference is more stable across the populated offset strata, but the cohort remains small and selected around known red-team authentication events. It is a candidate signal for independent confirmation, not evidence of attack-detection accuracy.

## Fresh methodological context

A 2026 IEEE intrusion-detection dataset audit (DOI `10.1109/IMNS67862.2026.11655312`) identifies temporal concentration and node-identity leakage as mechanisms that can inflate apparently strong results and advocates attack-aware chronological evaluation. A separate 2026 IEEE Access study (DOI `10.1109/ACCESS.2026.3688204`) demonstrates that temporal NetFlow structure can materially affect model performance. These papers reinforce the decision not to interpret the present time-shifted comparison as a detection result.

## Claim boundary

- Controls are **not verified benign**.
- No sensitivity, specificity, false-positive rate, AUC, causal effect, or production security-effectiveness claim is permitted.
- No threshold or trust-model weight was fitted to these 24 pairs.
- LANL process/DNS/flow data are enterprise telemetry proxies, not MDM compliance, patch posture, EDR health, or proprietary identity-risk ground truth.
- `auth.txt` remains absent from the operational mirror, so the planned authentication-derived baseline is still blocked.

## Next confirmatory design

Do not tune the current 25-pair result.

Before examining labels 26-50, freeze a second-cohort protocol that prioritizes **same-weekday/time-of-day controls** (7-day multiples), retains unmatched and zero-event controls, and uses the same 13 frozen features. The primary confirmation target should be the process-activity features. Flow features should remain secondary because their first-cohort differences were offset-sensitive.
