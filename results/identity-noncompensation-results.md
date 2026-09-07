# Identity Non-Compensation Results — 2026-09-06

**Synthetic diagnostic experiment only. These results do not establish production security effectiveness or an optimal access-control policy.**

## Question

Can favorable endpoint signals compensate for severely degraded identity assurance and behavioral risk in the current additive trust model, and how does a simple non-compensatory `STEP_UP` guard compare with raising the global `ALLOW` threshold?

## Policies compared

- **Additive 0.75** — current weighted model with `ALLOW >= 0.75`.
- **Additive 0.80** — same model with a stricter global threshold.
- **Guarded 0.75** — current 0.75 threshold, but an otherwise-`ALLOW` decision becomes `STEP_UP` when `identity_assurance < 0.40` **or** `anomaly_risk > 0.75`.

The guard does not override the existing hard denies for critical threat risk or critically low security coverage.

## Seeded 50,000-row synthetic population

Seed: `20260903`.

| Policy | Unsafe false-allow rate | Safe STEP_UP rate | Safe DENY rate |
|---|---:|---:|---:|
| Additive 0.75 | 12.50% | 5.40% | 0.00% |
| Additive 0.80 | 0.34% | 13.58% | 0.00% |
| Guarded 0.75 | **1.24%** | **5.40%** | 0.00% |

### Selected scenario behavior

| Scenario | Additive 0.75 ALLOW | Additive 0.80 ALLOW | Guarded 0.75 ALLOW |
|---|---:|---:|---:|
| `identity_risk` | 58.31% | 1.84% | **0.00%** |
| `adversarial_compliant` | 7.44% | **0.00%** | 4.83% |
| benign `policy_drift` | 61.94% | 4.30% | 61.94% |

The stricter global threshold is more aggressive against `adversarial_compliant` cases, but it also pushes almost all benign `policy_drift` cases into `STEP_UP`. The identity guard preserves the original treatment of `policy_drift` while eliminating `ALLOW` decisions in the current `identity_risk` scenario.

## Policy-surface diagnostic

To isolate compensation from the synthetic scenario labels, the experiment fixes the six non-identity signals at the midpoint of the current `healthy` scenario ranges and sweeps:

- `identity_assurance` from 0.00 to 1.00 in 0.05 increments;
- `anomaly_risk` from 0.00 to 1.00 in 0.05 increments.

This creates 441 policy-surface points.

| Policy | Grid points classified ALLOW | Share of surface ALLOW |
|---|---:|---:|
| Additive 0.75 | 417 / 441 | **94.56%** |
| Additive 0.80 | 303 / 441 | 68.71% |
| Guarded 0.75 | 208 / 441 | 47.17% |

A concrete compensation example is intentionally covered by a unit test: with otherwise healthy endpoint evidence, `identity_assurance = 0.20` and `anomaly_risk = 0.90` still produces `ALLOW` under the additive 0.75 model. The experimental guard converts that result to `STEP_UP`.

## Interpretation

1. **The current weighted sum has a genuine compensation property.** Strong compliance, endpoint health, patching, security coverage, freshness, and threat-safety evidence can offset extremely weak identity/behavior evidence.
2. **Raising the global threshold reduces the compensation problem but creates broad friction elsewhere.** On the current generator, `ALLOW >= 0.80` nearly eliminates unsafe allows, but 95.70% of benign `policy_drift` cases require `STEP_UP`.
3. **A targeted non-compensatory guard is more selective in this synthetic design.** It reduces aggregate false allows from 12.50% to 1.24% while leaving the synthetic safe STEP_UP rate at 5.40%.
4. **The unchanged safe STEP_UP rate must not be interpreted as evidence that the guard is cost-free.** Safe scenarios in the current generator never enter the guard region (`identity_assurance < 0.40` or `anomaly_risk > 0.75`). The experiment therefore cannot estimate false challenges caused by noisy or legitimately unusual identity behavior.

## Research significance

The useful finding is not that the particular `0.40/0.75` guard is optimal. Those values are exploratory and in-sample. The useful finding is that the current additive model permits cross-domain compensation that may be undesirable for access decisions, and that this behavior can be measured independently of aggregate accuracy.

The manuscript should frame this as a **design and validation question**:

> Which trust dimensions, if any, should be non-compensatory, and how should abstention/step-up policies be calibrated when identity or behavioral evidence crosses domain-specific risk boundaries?

## Limitations

- All population labels and feature distributions are synthetic and project-designed.
- Guard thresholds were not learned from independent data.
- The current safe scenarios do not include legitimate low-assurance/high-anomaly identity cases, so guard-induced user friction is structurally underestimated.
- The policy-surface diagnostic holds endpoint evidence fixed at representative healthy values and is a mechanism test, not a prevalence estimate.
- `STEP_UP` represents abstention/additional verification; no actual MFA completion time, user abandonment, or help-desk burden is measured.

## Reproduce

```bash
python src/evaluate_identity_noncompensation.py --rows 50000 --seed 20260903
python -m unittest discover -s tests -v
```

## Next experiment

Do **not** tune the guard further on the same generator. The next meaningful validation should use independently sourced identity/authentication telemetry (LANL) and/or a controlled endpoint lab with deliberately introduced benign identity uncertainty so both security benefit and challenge burden can be measured.
