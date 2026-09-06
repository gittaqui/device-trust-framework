# Threshold Sensitivity and Per-Scenario Error Analysis

_Date: 2026-09-05_

**Synthetic experiment only. These results do not demonstrate production security effectiveness.**

## Objective

The initial model used a fixed `ALLOW` threshold of `0.75`. This experiment tests
whether the reported result is stable as that threshold changes and identifies the
scenario families responsible for residual false allows.

The `STEP_UP` threshold remains fixed at `0.55`; the `ALLOW` threshold is swept from
`0.60` through `0.90` in increments of `0.01` using the existing 50,000-row generator
with seed `20260903`.

Reproduce with:

```bash
python src/evaluate_threshold_sensitivity.py
```

## Aggregate sensitivity

| ALLOW threshold | False-allow rate | False-deny rate | Safe STEP_UP rate | Safe ALLOW rate |
|---:|---:|---:|---:|---:|
| 0.60 | 53.00% | 0.00% | 0.00% | 100.00% |
| 0.65 | 51.32% | 0.00% | 0.00% | 100.00% |
| 0.70 | 37.32% | 0.00% | 0.06% | 99.94% |
| 0.75 | 12.50% | 0.00% | 5.40% | 94.60% |
| 0.76 | 8.07% | 0.00% | 7.40% | 92.60% |
| 0.77 | 4.77% | 0.00% | 9.59% | 90.41% |
| 0.78 | 2.47% | 0.00% | 11.38% | 88.62% |
| 0.79 | 1.04% | 0.00% | 12.67% | 87.33% |
| 0.80 | 0.34% | 0.00% | 13.58% | 86.42% |
| 0.81 | 0.06% | 0.00% | 13.96% | 86.04% |
| 0.82 | 0.01% | 0.00% | 14.15% | 85.85% |
| 0.83 | 0.00% | 0.00% | 14.18% | 85.82% |
| 0.85 | 0.00% | 0.00% | 14.19% | 85.81% |
| 0.90 | 0.00% | 0.00% | 20.09% | 79.91% |

## Per-scenario behavior

### Current threshold: 0.75

| Scenario | n | ALLOW | STEP_UP | DENY | False-allow rate |
|---|---:|---:|---:|---:|---:|
| healthy | 24,913 | 100.0% | 0.0% | 0.0% | — |
| policy_drift | 4,120 | 61.9% | 38.1% | 0.0% | — |
| stale | 3,989 | 2.8% | 97.2% | 0.0% | 2.8% |
| identity_risk | 3,912 | 58.3% | 41.7% | 0.0% | **58.3%** |
| malware | 3,473 | 0.0% | 0.0% | 100.0% | 0.0% |
| protection_missing | 3,034 | 0.0% | 0.0% | 100.0% | 0.0% |
| mixed_degradation | 3,496 | 0.0% | 32.6% | 67.4% | 0.0% |
| adversarial_compliant | 3,063 | 7.4% | 92.6% | 0.0% | 7.4% |

### Higher threshold: 0.80

| Scenario | n | ALLOW | STEP_UP | DENY | False-allow rate |
|---|---:|---:|---:|---:|---:|
| healthy | 24,913 | 100.0% | 0.0% | 0.0% | — |
| policy_drift | 4,120 | 4.3% | 95.7% | 0.0% | — |
| stale | 3,989 | 0.0% | 100.0% | 0.0% | 0.0% |
| identity_risk | 3,912 | 1.8% | 98.2% | 0.0% | **1.8%** |
| malware | 3,473 | 0.0% | 0.0% | 100.0% | 0.0% |
| protection_missing | 3,034 | 0.0% | 0.0% | 100.0% | 0.0% |
| mixed_degradation | 3,496 | 0.0% | 32.6% | 67.4% | 0.0% |
| adversarial_compliant | 3,063 | 0.0% | 100.0% | 0.0% | 0.0% |

## Interpretation

The model is highly sensitive to the chosen `ALLOW` threshold. The original `0.75`
setting is therefore not defensible as a universal threshold on the basis of this
synthetic generator.

More importantly, the scenario breakdown reveals a structural weakness that aggregate
metrics hide: at `0.75`, the `identity_risk` family accounts for the largest residual
unsafe-ALLOW behavior. High compliance, endpoint health, patch posture, coverage, and
freshness can compensate for low identity assurance and high anomaly risk in the
current additive score. The existing hard gates successfully contain the deliberately
constructed malware and missing-protection scenarios, but equivalent non-compensatory
logic has not yet been justified for identity evidence.

Raising the threshold to `0.80` nearly eliminates synthetic false allows (0.34%), but
creates substantial verification friction: 95.7% of the benign `policy_drift` cases
move to `STEP_UP`. This is not a false denial under the current three-way decision
model, but it is an operational cost that must be measured rather than ignored.

A threshold of `0.83` produces zero false allows on this dataset while preserving an
85.82% safe-ALLOW rate, but selecting it because it performs well on the same synthetic
generator would constitute in-sample tuning. It must not be presented as an optimal or
recommended production threshold.

## Research implication

The next model iteration should test **risk- or resource-dependent thresholds and
non-compensatory constraints** rather than merely tuning one global threshold. This is
consistent with prior enterprise Zero Trust research that treats trust thresholds as
dynamic and risk-dependent rather than universal constants.

## Limitations

- All labels and signal distributions are synthetic and were designed by the project.
- The threshold sweep uses the same generator used to develop the baseline model.
- `STEP_UP` is an abstract abstention/verification outcome; no user-experience cost is
  measured.
- Zero false allows at high thresholds is not evidence of real-world attack detection.
- The experiment does not yet vary the `STEP_UP` threshold or signal weights jointly.
- External telemetry is required before threshold calibration or operational claims.
