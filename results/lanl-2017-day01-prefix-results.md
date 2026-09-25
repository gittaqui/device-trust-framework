# LANL 2017 day-1 bounded host-event result

Date: 2026-09-25

## Status

This is the first completed **Level-1 external unlabeled telemetry plausibility** run under the frozen protocol in `experiments/external-validation-freeze.md`.

It is descriptive external evidence, **not** an attack-detection or full Device Trust effectiveness result.

## Provenance

Source: Imperial College London-hosted public mirror of the LANL Unified Host and Network Data Set.

File: `wls_day-01.bz2`

- compressed size: 408,954,096 bytes
- MD5: `36cfb5acfac150608132d6a8b029e3b1`
- SHA-1: `f61c81579db39510390c8967047873899f5e6b58`
- SHA-256: `65621c6bf500bd69ff24104cae8540fa6e24a70546acbbd802a40bf934b23643`

The computed MD5 and SHA-1 exactly match the mirror's published `wls_hashes` values for day 1.

Dataset citation:

Melissa J. M. Turcotte, Alexander D. Kent, and Curtis Hash, "Unified Host and Network Data Set," in *Data Science for Cyber-Security*, pp. 1–22, 2018. DOI: `10.1142/9781786345646_001`.

## Frozen bounded run

The protocol fixed the first run at the first **100,000 valid host-event records** before external results were inspected.

- processed: **100,000**
- rejected records: **0**
- dataset `Time` field range in prefix: **1–109**

The narrow time range is important: this prefix samples only the very beginning of day 1 and must not be treated as a representative day-level prevalence estimate.

## Pre-specified descriptive outputs

| Output | Result |
|---|---:|
| Authentication-related events | 45,743 (45.743%) |
| Process-start events (4688) | 40,371 (40.371%) |
| Authentication failures | 1,008 |
| Failure rate / broad auth-related events | 2.204% |
| Outcome-bearing authentication events | 30,953 |
| Failure rate / outcome-bearing auth events | 3.257% |
| Novel user-host edges | 7,374 (16.120% of broad auth events) |
| Explicit-credential events (4648) | 1,295 |
| Privileged-logon events (4672) | 13,495 |
| Novel process starts | 26,801 (66.387% of process starts) |
| Mean proxy identity assurance | 0.973553 |
| Mean proxy anomaly risk | 0.084060 |
| Frozen identity/anomaly guard STEP_UP | 417 / 100,000 (0.417%) |

The broad authentication set is the adapter's frozen `AUTH_EVENT_IDS` set and includes authentication-related events such as 4648 and 4672. The outcome-bearing denominator includes only events for which the adapter assigns a success/failure outcome.

## Proxy distributions

### Identity assurance

| Quantile | Value |
|---:|---:|
| min | 0.200000 |
| 1% | 0.729421 |
| 5% | 0.750000 |
| 25% | 1.000000 |
| median | 1.000000 |
| 75% | 1.000000 |
| 95% | 1.000000 |
| 99% | 1.000000 |
| max | 1.000000 |

### Anomaly risk

| Quantile | Value |
|---:|---:|
| min | 0.000000 |
| 1% | 0.000000 |
| 5% | 0.000000 |
| 25% | 0.000000 |
| median | 0.045986 |
| 75% | 0.150000 |
| 95% | 0.350000 |
| 99% | 0.350000 |
| max | 0.750000 |

### Freshness

The 25th through 100th percentiles are all 1.0; the minimum is 0.998773. This is expected for a prefix spanning only `Time=1..109` and means this run cannot meaningfully validate long-horizon freshness behavior.

## Guard behavior

The frozen guard is:

- `identity_assurance < 0.40`, or
- `anomaly_risk > 0.75`.

In the bounded prefix:

- identity trigger: **417**
- anomaly trigger: **0**
- union / STEP_UP: **417 (0.417%)**

The maximum observed anomaly proxy is exactly 0.75, so the strict `> 0.75` anomaly condition never fires in this prefix.

This is descriptive behavior only. Because the 2017 release does not provide independent malicious/benign labels for these events, the 0.417% rate must **not** be described as a detection rate, false-positive rate, or correct challenge rate.

## Event mix

| Event ID | Count |
|---:|---:|
| 4688 | 40,371 |
| 4624 | 22,365 |
| 4634 | 13,879 |
| 4672 | 13,495 |
| 4776 | 5,912 |
| 4769 | 1,730 |
| 4648 | 1,295 |
| 4768 | 575 |
| 4625 | 371 |
| 4800 | 3 |
| 4689 | 3 |
| 4609 | 1 |

## Main scientific finding

The most important result is a **cold-start validity problem**.

The adapter starts with no historical user-host or host-process state. Consequently, **66.387% of process starts are classified as first-seen-on-host** and **16.120% of broad authentication-related events create a first-seen user-host edge** during the very early prefix.

These counts are genuine outputs of the frozen adapter, but they cannot be interpreted as production anomaly prevalence. They mix ordinary first-observation effects with behavioral novelty.

This is exactly why the first frozen run was descriptive rather than an effectiveness test.

## Claim boundary

Permitted:

> The existing streaming adapter successfully ingested 100,000 temporally ordered events from independently sourced real enterprise Windows telemetry with zero rejected records, and its transparent proxies exhibit measurable distributions on those events.

Not permitted:

- the framework detected attacks;
- 0.417% is a false-positive or true-positive rate;
- first-seen processes are malicious or abnormal;
- the proxy scores are equivalent to Intune, Entra, Defender, or production device-risk scores;
- the full eight-signal framework has been externally validated.

## Reproducibility

A dedicated evaluator is committed as `src/evaluate_lanl_2017_bounded.py`.

The raw LANL archive is not committed. Provenance and checksums are recorded in `data/external/lanl-2017-day01-manifest.csv`.

A follow-up burn-in experiment must be frozen **before** examining later day-1 results so that ordinary cold-start effects can be separated from later first-seen behavior.
