# Experimental Design — Version 0.1

## Baselines

### B0 — Binary compliance
Allow when the endpoint is marked compliant; deny otherwise.

### M1 — Explainable multidimensional trust
Combine normalized signals:

| Signal | Meaning | Direction |
|---|---|---|
| compliance | configuration/policy compliance | higher is safer |
| endpoint_health | device operational/security health | higher is safer |
| identity_assurance | confidence in user/device identity | higher is safer |
| patch_posture | update/patch state | higher is safer |
| security_coverage | active security control coverage | higher is safer |
| freshness | recency of device/telemetry state | higher is safer |
| threat_risk | detected threat risk | higher is riskier |
| anomaly_risk | anomalous behavior risk | higher is riskier |

The baseline implementation uses transparent weights and converts risk signals to
positive contributions using `1 - risk`.

## Safety gates

A device is denied regardless of aggregate score when:
- threat risk is critically high; or
- security coverage is critically low.

This prevents compensation effects where several benign signals could mask one
catastrophic signal.

## Decision bands

- `ALLOW`: trust >= 0.75
- `STEP_UP`: 0.55 <= trust < 0.75
- `DENY`: trust < 0.55
- hard-gate conditions always produce `DENY`

Thresholds are hypotheses, not established standards. Sensitivity analysis will vary
them.

## Synthetic scenario families

1. healthy
2. policy_drift
3. stale
4. identity_risk
5. malware
6. protection_missing
7. mixed_degradation
8. adversarial_compliant

The important adversarial case is a device that remains nominally compliant while
threat or identity indicators become dangerous.

## Ground truth

Synthetic rows are generated from scenario labels. The scenario label determines
whether the session should be considered safe for ordinary access. The label is kept
separate from the model score so that evaluation is not simply score-against-itself.

## Primary metrics

- false-allow rate (unsafe sessions allowed)
- false-deny rate (safe sessions denied)
- safe-session allow rate
- unsafe-session containment rate
- step-up rate
- total evaluation time
- evaluations per second

## Planned studies

### E1 — Baseline comparison
Compare B0 and M1 over 50,000 synthetic sessions.

### E2 — Weight sensitivity
Perturb weights and quantify decision stability.

### E3 — Threshold sensitivity
Sweep allow/step-up thresholds.

### E4 — Missing telemetry
Randomly remove one or more signals and test conservative fallback strategies.

### E5 — Adversarial scenarios
Increase the share of nominally compliant but compromised endpoints.

### E6 — Scale
Evaluate 10K, 100K, and 1M rows.

## Limitations

Synthetic data cannot establish real-world security effectiveness. It is used here to
develop hypotheses, validate logic, expose failure modes, and design a reproducible
benchmark before seeking real or independently sourced datasets.
