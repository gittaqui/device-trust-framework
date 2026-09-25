# Microsoft Cloud Monitoring endpoint-health pilot

Date: 2026-09-25

## Scope

This experiment is **component-level external validation only**. It evaluates whether a transparent, causal reliability-risk proxy derived from Microsoft production application-crash telemetry ranks expert-labeled anomaly points above normal points.

It does **not** validate the full Device Trust Framework. The upstream data are aggregate time series, not per-device Intune, Entra, Defender, patch, or compliance records.

Upstream: `microsoft/cloud-monitoring-dataset` (archived public repository, MIT license).

Microsoft states that the dataset contains 67 real-world production telemetry series across multiple domains, including Windows application crash rate by OS version and country, with anomaly points labeled using domain experts.

## Method

For each Windows application-crash series:

1. Hold out the first 48 observations as causal history.
2. For each subsequent observation, compute the median and median absolute deviation (MAD) using only the preceding 48 values.
3. Convert a positive robust deviation into an `anomaly_risk`.
4. Define `endpoint_health = 1 - anomaly_risk`.
5. Use expert anomaly labels **only for evaluation**, never for score construction.
6. Report ROC AUC for both raw crash value and the causal robust-risk proxy.

The causal score is intentionally simple and interpretable. It is a baseline, not a tuned anomaly detector.

## Coverage

All 19 files in the two Windows application-crash directories were evaluated.

- Raw source observations: **16,645**
- Evaluated after 48-point warm-up: **15,733**
- Expert-labeled anomalies in evaluated region: **1,192**
- Macro-average raw-value ROC AUC across 19 series: **0.8190**
- Macro-average causal robust-risk ROC AUC across 19 series: **0.7684**
- Causal robust-risk AUC range: **0.5609–0.9376**

## Per-series results

| Series | Evaluated | Anomalies | Raw AUC | Causal robust-risk AUC |
|---|---:|---:|---:|---:|
| app1-01 | 310 | 40 | 0.8103 | 0.7577 |
| app1-02 | 662 | 94 | 0.9015 | 0.7462 |
| app1-03 | 662 | 144 | 0.8687 | 0.5609 |
| app1-04 | 662 | 144 | 0.8247 | 0.7708 |
| app1-05 | 662 | 70 | 0.6927 | 0.6742 |
| app1-06 | 662 | 106 | 0.9089 | 0.8292 |
| app1-07 | 662 | 7 | 0.7081 | 0.7507 |
| app1-08 | 662 | 65 | 0.7716 | 0.7357 |
| app1-09 | 128 | 7 | 0.9079 | 0.8701 |
| app2-01 | 1066 | 72 | 0.8371 | 0.7995 |
| app2-02 | 1069 | 28 | 0.9408 | 0.9376 |
| app2-03 | 1070 | 14 | 0.7727 | 0.7955 |
| app2-04 | 1070 | 14 | 0.8279 | 0.7919 |
| app2-05 | 1070 | 203 | 0.8222 | 0.7671 |
| app2-06 | 1068 | 34 | 0.9675 | 0.9211 |
| app2-07 | 1061 | 119 | 0.7784 | 0.6906 |
| app2-08 | 1070 | 9 | 0.5771 | 0.6578 |
| app2-09 | 1070 | 10 | 0.8464 | 0.7736 |
| app2-10 | 1047 | 12 | 0.7963 | 0.7688 |

## Interpretation

The result is useful but deliberately not flattering.

The simple causal robust-risk proxy exhibits substantial cross-series heterogeneity. It achieves strong ranking on some series (for example app2-02 and app2-06) but only weak-to-moderate ranking on others (notably app1-03). The macro-average causal AUC is lower than simply ranking by raw crash value.

This means the manuscript should **not** claim that a fixed robust-z transform is a generally validated endpoint-health estimator. Instead, the data support a narrower conclusion:

> Real production reliability telemetry can provide externally grounded evidence for an endpoint-health dimension, but the transformation from raw telemetry to a trust signal is source- and context-dependent and requires validation rather than a universal threshold.

The large variation also reinforces the framework's existing argument against treating a calibrated score as an invariant security guarantee.

## Limitations

- The source contains aggregate crash-rate time series, not individual device records.
- Crash anomalies validate only a reliability/health component; they do not validate identity, compliance, patch posture, security coverage, threat risk, or access outcomes.
- Expert labels describe anomalous telemetry points, not unsafe access decisions.
- The 48-point causal window and `risk_scale=3` are transparent research choices, not production-optimized parameters.
- No cross-dataset row-level fusion is performed.
- Raw external data are not committed to this repository. The source paths and upstream Git blob SHAs are recorded in `data/external/microsoft-cloud-monitoring-manifest.csv`.

## Reproducibility note

The numerical pass used all 19 upstream CSV files and the same causal scoring equations implemented in `src/microsoft_cloud_health_adapter.py`. Targeted unit tests for the adapter passed locally (3/3). The upstream raw files remain governed by the Microsoft repository's MIT license.
