# External-validation freeze and claims protocol

Date frozen: 2026-09-11

## Purpose

This document freezes the transition from exploratory synthetic development to externally sourced telemetry evaluation for the Device Trust Framework. It exists to prevent outcome-dependent tuning, temporal leakage, and overclaiming when an external dataset exposes only a subset of the eight model signals.

The current synthetic experiments remain exploratory. External evaluation performed after this freeze must report deviations from this protocol before reporting outcome-dependent results.

## Methodological basis

Preregistration separates analyses specified before observing outcomes from analyses chosen after seeing them. Nosek et al. (2018) describe this distinction as important for preserving the credibility of confirmatory inference. Kapoor and Narayanan (2023) document how data leakage, including temporal leakage and test-set contamination, can produce overoptimistic scientific claims in machine-learning studies.

This repository uses those principles pragmatically: the external datasets already exist, but the policy parameters, permissible calibration steps, temporal split rules, primary metrics, and claim boundaries are frozen before external outcome analysis.

## Current model state to freeze

Unless explicitly identified as calibration-only, the following research policy state is frozen for the first external evaluation:

- weighted additive trust factors and default weights from `src/trust_model.py`;
- additive allow thresholds: 0.75 and 0.80;
- STEP_UP threshold: 0.55;
- hard gate: `threat_risk >= 0.90` -> DENY;
- hard gate: `security_coverage <= 0.15` -> DENY;
- experimental identity guard: `identity_assurance < 0.40` or `anomaly_risk > 0.75` converts an otherwise-ALLOW result to STEP_UP;
- no threshold may be changed because of evaluation-period results.

The binary compliance baseline remains part of the synthetic comparison. It may be used externally only if an external dataset contains a defensible, independently defined compliance/posture variable. A proxy invented from authentication or process events must not be labeled "compliance" merely to preserve the baseline.

## Claim firewall

External evidence is divided into four levels. A result must not be described using a stronger level than its data support.

### Level 0 — synthetic mechanism analysis

Permitted claims:

- behavior under explicit synthetic feature ranges and labels;
- sensitivity to thresholds, missing values, guard rules, and hypothetical decision costs;
- reproducibility of the implemented policy logic.

Not permitted:

- production detection rate;
- production false-allow rate;
- real enterprise prevalence;
- superiority in deployed environments.

### Level 1 — external unlabeled telemetry plausibility

Primary source: LANL 2017 Unified Host and Network Data Set, using temporally ordered Windows host events.

Permitted claims:

- observed distribution of the transparent authentication/process proxies defined in `src/lanl_2017_host_adapter.py`;
- frequency of novelty, failed-authentication history, explicit-credential use, privilege events, and process novelty;
- how often a *frozen* identity/anomaly guard would request STEP_UP under those proxies;
- computational throughput of the adapter/policy path.

Not permitted:

- false-allow, false-deny, precision, recall, ROC/AUC, attack detection, or full-model accuracy;
- treating the LANL-derived proxies as Intune compliance, Entra risk, Defender risk, or measured endpoint-health state;
- assuming all unlabeled LANL events are benign.

### Level 2 — external labeled component validation

Potential source: the LANL Comprehensive Multi-Source Cyber-Security Events release, whose official page includes independently supplied red-team compromise events.

Permitted claims, if the relevant authentication events can be aligned without leakage:

- discrimination or abstention behavior of the identity/anomaly component against independent red-team labels;
- temporal detection/challenge rates for that component;
- comparison with transparent identity/authentication baselines using exactly the same events.

Not permitted:

- claiming validation of the full eight-signal device-trust model when the dataset does not contain defensible measurements for compliance, endpoint health, patch posture, security coverage, and freshness as defined by the model;
- creating post-hoc proxies after viewing labeled evaluation outcomes and calling the result confirmatory.

### Level 3 — full multidimensional external validation

A full-model effectiveness claim requires an external dataset or prospective study that independently supports the model dimensions used in the claim, provides defensible outcome labels, and allows leakage-controlled temporal evaluation. Until such data exist, the manuscript must characterize full-model performance as synthetic mechanism analysis plus, at most, partial external component validation.

## Temporal split rules

For any externally sourced sequence used for calibration and evaluation:

1. Preserve timestamp order.
2. Compute history-based features using observations strictly prior to the scored event.
3. Do not randomly shuffle events across training/calibration/evaluation intervals.
4. Use the earliest eligible interval for adapter debugging and descriptive inspection.
5. If calibration is required, use a temporally earlier calibration interval.
6. Lock calibrated values before opening the evaluation interval.
7. Use a later, untouched interval for reported evaluation.
8. Do not use evaluation labels or aggregate evaluation metrics to revise feature mappings, exclusions, weights, or thresholds.

If a dataset contains repeated users or devices across intervals, that persistence must be reported rather than treated as statistical independence.

## Calibration policy

The first LANL 2017 bounded run is descriptive and permits **no threshold calibration**.

For a later labeled dataset, the following may be calibrated on a designated temporal calibration interval only:

- normalization constants needed to map raw external telemetry into already defined transparent proxy variables;
- a baseline-specific decision threshold if that baseline intrinsically requires fitting.

The following remain frozen unless a new protocol version is committed before opening the evaluation interval:

- factor semantics;
- default model weights;
- 0.75 and 0.80 additive thresholds;
- 0.55 STEP_UP threshold;
- 0.40 identity-assurance guard;
- 0.75 anomaly-risk guard;
- hard-gate semantics;
- primary outcome definitions.

Any exploratory recalibration after seeing evaluation outcomes must be labeled post-hoc and evaluated on a new untouched interval before being described as confirmatory.

## Primary external outputs

### LANL 2017 unlabeled stage

Pre-specified outputs:

1. total events processed;
2. authentication-event count;
3. process-start count;
4. authentication-failure count and rate;
5. novel user-host edge count and rate;
6. explicit-credential event count and rate;
7. privileged-logon count and rate;
8. novel process-on-host count and rate;
9. distribution of proxy identity assurance;
10. distribution of proxy anomaly risk;
11. frozen identity-guard STEP_UP frequency;
12. processing throughput and peak memory if measured reproducibly.

No significance test is required for this descriptive stage.

### Labeled component stage

If independently labeled red-team events are integrated, report at minimum:

- event count and label prevalence by temporal interval;
- challenge/detection rate on labeled red-team events;
- challenge rate on unlabeled/non-red-team events, explicitly avoiding the term false-positive unless those events are independently established as benign;
- coverage/abstention rate;
- 95% confidence intervals for binomial proportions where appropriate;
- per-day results so aggregate performance cannot conceal temporal failure periods.

## Dataset access and provenance

For every external file, preserve privately or in a non-raw-data provenance manifest:

- official source URL;
- download date;
- original filename;
- SHA-256 checksum;
- dataset citation/DOI;
- adapter commit SHA;
- number of parsed and rejected records;
- temporal coverage actually evaluated.

Raw LANL data must not be committed to this repository.

## Deviations

A deviation is not automatically invalid, but it must be visible. Before presenting affected results, add a dated research-log entry stating:

- what changed;
- why the original rule could not be followed;
- whether outcome data had already been inspected;
- which analyses are therefore exploratory rather than confirmatory.

## Stopping and negative-result rule

External analysis must not stop early because the frozen policy performs poorly. The pre-specified bounded interval must be processed unless a documented technical/data-integrity problem prevents completion. Negative or null findings are retained in the repository and manuscript development history.

## Current status

As of 2026-09-11, no LANL raw data or externally derived performance results are present in this repository. The official LANL 2017 page still requests researcher email and intended-use information before download. The repository therefore contains an ingestion path and this frozen analysis/claims protocol, but **no claim of external effectiveness**.
