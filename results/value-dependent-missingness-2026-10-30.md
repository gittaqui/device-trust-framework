# Value-dependent missingness: synthetic sensitivity results — 2026-10-30

**Evidence:** 50,000 generated endpoint-session observations (29,033 labeled safe; 20,967 labeled unsafe). Labels are scenario-defined, not independently adjudicated. This is exploratory and not preregistered. Three seeds (20260904–20260906) reuse the same synthetic rows, with common random draws across beta arms and policies.

## Primary result: unsafe ordinary-ALLOW by missingness strength

Expected missingness is **25% for each of eight columns** in every arm, with a calibrated logistic intercept per column. Beta=0 is MCAR by construction; beta=2 and beta=4 are increasingly value-dependent (MNAR by construction). Percentages are means across three seeds; ranges in brackets are minimum–maximum seed rates, **not confidence intervals**. Denominator: 20,967 synthetic unsafe rows.

| Policy | Beta=0 | Beta=2 | Beta=4 |
|---|---:|---:|---:|
| Renormalize | 17.26% [17.09–17.39] | 34.69% [34.56–34.84] | 52.60% [52.50–52.67] |
| Neutral | 4.37% [4.24–4.48] | 8.41% [8.32–8.50] | 13.13% [13.03–13.32] |
| Pessimistic | 1.44% [1.39–1.46] | 1.33% [1.27–1.38] | 0.92% [0.88–0.96] |
| Explicit STEP_UP | 5.81% [5.66–5.94] | 8.61% [8.57–8.67] | 10.91% [10.74–11.04] |

## Legitimate-user friction (means across seeds)

Rates below divide by 29,033 scenario-labeled safe observations. Each cell is safe DENY / safe STEP_UP.

| Policy | Beta=0 | Beta=2 | Beta=4 |
|---|---:|---:|---:|
| Renormalize | 0.09% / 7.53% | 0.02% / 4.09% | 0.00% / 1.51% |
| Neutral | 0.26% / 25.60% | 0.08% / 17.20% | 0.01% / 10.56% |
| Pessimistic | 21.04% / 43.45% | 13.68% / 39.40% | 8.38% / 33.29% |
| Explicit STEP_UP | 0.00% / 63.72% | 0.00% / 52.64% | 0.00% / 41.44% |

Mean *realized* missing-cell fractions: 24.990% (beta=0), 25.009% (beta=2), 24.995% (beta=4). Equalizing expected missingness isolates the effect of value-dependent concealment rather than simply increasing overall dropout.

## Conditional missingness sanity check (seed 20260904)

| Beta | Signal | Low-risk missing (r<=0.30) | High-risk missing (r>=0.70) |
|---:|---|---:|---:|
| 0 | Identity assurance | 25.12% (10070/40085) | 23.96% (790/3297) |
| 2 | Identity assurance | 20.98% (8411/40085) | 52.29% (1724/3297) |
| 4 | Identity assurance | 16.98% (6805/40085) | 78.95% (2603/3297) |
| 0 | Threat risk | 24.96% (9195/36843) | 24.63% (1255/5095) |
| 2 | Threat risk | 19.03% (7010/36843) | 53.56% (2729/5095) |
| 4 | Threat risk | 13.63% (5022/36843) | 78.04% (3976/5095) |
| 0 | Security coverage | 24.86% (10622/42720) | 25.48% (773/3034) |
| 2 | Security coverage | 21.34% (9116/42720) | 58.50% (1775/3034) |
| 4 | Security coverage | 18.52% (7911/42720) | 85.20% (2585/3034) |

## Per-scenario unsafe ALLOW under renormalization (seed 20260904)

| Beta | Identity risk | Malware | Protection missing |
|---:|---:|---:|---:|
| 0 | 1838/3912 (46.98%) | 214/3473 (6.16%) | 271/3034 (8.93%) |
| 2 | 2846/3912 (72.75%) | 900/3473 (25.91%) | 769/3034 (25.35%) |
| 4 | 3550/3912 (90.75%) | 1916/3473 (55.17%) | 1336/3034 (44.03%) |

## Interpretation, limits, reproduction

Preferentially missing less-safe synthetic signals sharply increases unsafe ALLOW under renormalization, despite matched expected marginal dropout. Pessimistic scoring is comparatively resistant in this particular generator but substantially restricts safe ordinary access. Neither is a real-world optimal-policy finding. The dropout mechanism is stipulated, affects all eight signals, and does not estimate an actual tenant outage mechanism. Synthetic labels are not independent ground truth. Three mask seeds measure Monte Carlo mask variability only, not population uncertainty. No causal, statistical-significance, or production-security claims are made.

Reproduce using experiments/value-dependent-missingness-protocol.md. Detailed generated JSON default SHA-256: **f1e2ad77c81dd2eda79de6354b2a4d7ae96d5587f5c6cb6e815913764f6b22f5**. The full JSON is in the dated research package; it is not required to be committed. The existing October 29 frozen coverage-strata JSON was independently regenerated and matched exactly before this experiment.

**Next:** single-signal value-dependent ablations and independently adjudicated non-production endpoint evaluation.
