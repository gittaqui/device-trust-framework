# Research Question

## Primary question

**Can an explainable multidimensional device trust model reduce unsafe access
decisions compared with binary endpoint compliance while remaining transparent,
stable under missing signals, and computationally practical at enterprise scale?**

## Research questions

### RQ1 — Decision quality
Does a multidimensional device trust model reduce **false allows** compared with a
binary compliance-only baseline across benign, degraded, compromised, stale, and
identity-risk endpoint scenarios?

### RQ2 — Explainability and sensitivity
How sensitive are access decisions to signal weights, thresholds, missing telemetry,
and individual high-risk indicators?

### RQ3 — Operational feasibility
Can the trust calculation be evaluated at enterprise scale with low computational
overhead and deterministic, auditable decision explanations?

## Initial hypotheses

- **H1:** The multidimensional model will produce a lower false-allow rate than
  binary compliance in adversarial and degraded-device scenarios.
- **H2:** Hard safety gates for severe threat or missing protection will prevent
  high-risk devices from receiving high trust scores despite otherwise favorable
  signals.
- **H3:** A linear, explainable model will remain computationally inexpensive enough
  for large synthetic endpoint populations while providing explicit factor-level
  explanations.

## Scope

The first study focuses on enterprise-managed endpoints and abstract normalized
signals inspired by endpoint management, identity, security, and device-health
systems. It does **not** claim to reproduce Microsoft Intune, Entra, Defender, or any
other commercial product's proprietary scoring logic.
