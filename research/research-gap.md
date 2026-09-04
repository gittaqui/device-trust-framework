# Research Gap

## What is already known

- Zero Trust architectures support device-aware and context-aware access decisions.
- Trust scores and risk-adaptive access control have already been proposed.
- Multiple domains have trust-scoring implementations, including IoT, smart-grid,
  cloud, service-mesh, campus, and network environments.
- AI/ML-based trust evaluation is an active research direction.

## What we should **not** claim

We should not claim:
- that device trust scoring is a new concept;
- that Zero Trust currently relies only on binary compliance;
- that the proposed weighted score is inherently superior;
- that synthetic experiments demonstrate production effectiveness.

## Candidate contribution

The proposed contribution is:

> A reproducible and explainable enterprise-endpoint trust framework that compares
> a binary compliance baseline with a multidimensional trust decision under
> controlled benign, degraded, stale, identity-risk, and compromised-device
> scenarios, including missing telemetry, threshold sensitivity, adversarial
> conditions, and large-population performance.

## Why this is potentially publishable

Recent trust-scoring reviews still identify:
- non-standard metrics;
- parameter subjectivity;
- limited explainability;
- limited adversarial evaluation;
- limited scalability testing;
- domain-specific validation.

Our study can directly test several of these limitations with an openly reproducible
benchmark rather than proposing another opaque trust score.
