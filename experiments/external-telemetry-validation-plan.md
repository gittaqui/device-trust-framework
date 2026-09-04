# External Telemetry Validation Plan

_Last updated: 2026-09-04_

## Objective

Strengthen the Device Trust Framework by moving from a purely synthetic benchmark to a **hybrid validation design** that combines:

1. real enterprise telemetry;
2. labeled security/testbed telemetry;
3. a controlled Microsoft endpoint lab where feasible; and
4. synthetic stress tests for conditions not represented in public data.

The goal is not to claim that public datasets reproduce Microsoft Intune, Entra, or Defender semantics. The goal is to test whether the framework's abstract trust dimensions remain useful when derived from independent telemetry sources.

## Primary external source: LANL Comprehensive Multi-Source Cyber-Security Events

Los Alamos National Laboratory released 58 consecutive days of de-identified telemetry from a real corporate Windows environment. The dataset includes Windows authentication, process start/stop, DNS, network-flow, and labeled red-team events. Published descriptions report approximately 1.65 billion events covering 12,425 users, 17,684 computers, and 62,974 processes.

### Why this dataset is high value

- Real enterprise Windows activity rather than a purely generated benchmark.
- Active Directory and workstation authentication behavior.
- Host process telemetry.
- Network context.
- Explicit red-team events that provide independent malicious-behavior ground truth.
- Large enough to support scalability testing.

### Proposed feature mapping

| Framework dimension | External features derived from LANL | Important caveat |
|---|---|---|
| `identity_assurance` | authentication success/failure ratio, unusual source-destination relationships, new user-host pairs, abnormal logon behavior | proxy for identity confidence; not equivalent to Entra Identity Protection |
| `endpoint_health` | process novelty, abnormal process frequency, abnormal host activity | behavioral proxy; not an endpoint-health product score |
| `freshness` | recency of host authentication/process activity | activity freshness, not Intune check-in freshness |
| `threat_risk` | proximity to known red-team events and confirmed malicious activity | labels can support retrospective evaluation |
| `anomaly_risk` | rare authentication edges, abnormal process events, lateral-movement indicators | model-derived feature |
| `compliance` | unavailable directly | must not be inferred and labeled as actual compliance |
| `patch_posture` | unavailable directly | leave missing or obtain from controlled lab |
| `security_coverage` | unavailable directly | leave missing or obtain from controlled lab |

## Secondary source: LANL User-Computer Authentication Associations in Time

This dataset contains 708,304,516 successful user-to-computer authentication events across nine months, covering 11,362 users and 22,284 computers. It is useful for longitudinal identity baselines, credential-hopping analysis, and trust-decay experiments.

### Candidate experiments

- Detect new or rare user-computer edges.
- Measure trust reduction when a user begins authenticating to atypical hosts.
- Compare short-window and long-window behavioral baselines.
- Test whether progressive trust decay reduces unsafe access opportunities without excessive false denials.

## Controlled Microsoft endpoint lab

Public data does not provide the complete endpoint posture needed for the proposed framework. A small non-production lab can supply the missing dimensions without using employer-confidential information.

Possible lab signals:

- device compliance state;
- operating-system and patch state;
- endpoint/security-control presence;
- last check-in / telemetry recency;
- identity assurance and sign-in context where available;
- deliberately induced safe configuration drift;
- deliberately simulated stale endpoints;
- benign security-control disable/re-enable scenarios.

No malware deployment or uncontrolled attack behavior is required. The lab should remain isolated and use only test identities/devices.

## Hybrid benchmark architecture

```text
LANL enterprise telemetry
        |
        +--> identity_assurance
        +--> endpoint_health proxy
        +--> freshness proxy
        +--> threat_risk
        +--> anomaly_risk

Controlled endpoint lab
        |
        +--> compliance
        +--> patch_posture
        +--> security_coverage
        +--> endpoint freshness

Synthetic stress testing
        |
        +--> missing-signal cases
        +--> threshold boundaries
        +--> adversarially compliant cases
        +--> rare combinations not present in external data

              -> normalized trust dimensions
              -> binary baseline vs multidimensional model
              -> false allow / false deny / step-up / scale / stability
```

## Experimental sequence

### E7 — LANL authentication baseline

Derive rolling authentication-risk features per user-host pair and evaluate whether red-team-linked sessions receive lower trust than comparable benign sessions.

### E8 — Host-process enrichment

Add process novelty and host activity features, then measure the incremental value over authentication-only trust.

### E9 — Missing-signal robustness

Treat compliance, patch posture, and security coverage as unavailable on LANL rows and compare conservative missing-data strategies:

- neutral imputation;
- pessimistic imputation;
- confidence penalty;
- explicit `UNKNOWN` / `STEP_UP` decision.

### E10 — Temporal trust

Introduce time-aware trust decay and determine whether dynamic scoring identifies risk earlier around red-team events.

### E11 — Cross-source validation

Compare feature behavior between LANL-derived signals and controlled-lab endpoint posture. The goal is not direct row-level fusion, but evidence that the abstract dimensions behave consistently across independent sources.

## Publication claims we may make only after validation

Potentially supportable:

- the framework was evaluated on both synthetic and independently sourced enterprise telemetry;
- the framework can operate with partial telemetry and explicitly represent missing evidence;
- certain signal combinations materially change false-allow/false-deny behavior;
- the model has measured computational throughput at large scale.

Not supportable without additional evidence:

- equivalence to Intune/Entra/Defender risk scoring;
- effectiveness in a production Microsoft tenant;
- prevention of real breaches;
- superiority over commercial Zero Trust products.

## Reproducibility requirements

- Pin every public dataset version and source URL.
- Preserve checksums where the provider publishes them.
- Store feature-extraction code rather than redistributed large datasets.
- Keep raw external datasets out of Git when licensing or size makes redistribution inappropriate.
- Record every transformation from raw event fields to normalized trust dimensions.
- Separate ground-truth labels from features used to compute trust.
- Publish experiment seeds and configuration files.

## EB-1A relevance

This work is intended to create legitimate technical evidence, not merely satisfy a checklist. If eventually peer reviewed, cited, independently used, referenced, or adopted, it may contribute to evidence of:

- authorship of scholarly articles;
- original scientific/technical contributions of major significance, if independent significance is demonstrated;
- judging/reviewer opportunities that arise from genuine subject-matter expertise;
- final-merits evidence through a coherent record of recognized work in enterprise endpoint and Zero Trust engineering.
