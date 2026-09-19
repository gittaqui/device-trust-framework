# Synthetic ordinary-access risk–coverage analysis

**Status:** controlled synthetic experiment only. These numbers are not production security estimates and do not constitute real-world validation.

## Design

The experiment freezes the existing synthetic generator, scenario prevalence, weights, hard gates, and random seed (`20260903`). It varies only the ordinary `ALLOW` threshold. `STEP_UP` and `DENY` are treated as non-ordinary-access outcomes. For each threshold we report:

- **ordinary-access coverage:** fraction of all sessions receiving `ALLOW`;
- **unsafe-ALLOW risk:** fraction of `ALLOW` decisions whose synthetic scenario label is unsafe for ordinary access;
- **safe-session ALLOW recall:** fraction of synthetically safe sessions receiving `ALLOW`.

This framing is motivated by selective-classification/reject-option literature, which evaluates the trade-off between coverage and error/risk when a system may abstain rather than force a prediction.

## Results

50,000 synthetic sessions; seed `20260903`.

| ALLOW threshold | Ordinary-access coverage | Unsafe-ALLOW risk among allowed | Safe-session ALLOW recall |
|---:|---:|---:|---:|
| 0.60 | 80.29% | 27.68% | 100.00% |
| 0.65 | 79.59% | 27.04% | 100.00% |
| 0.70 | 73.68% | 21.24% | 99.94% |
| 0.75 | 60.17% | 8.71% | 94.60% |
| 0.80 | 50.32% | 0.29% | 86.42% |
| 0.85 | 49.83% | 0.00% | 85.81% |
| 0.90 | 46.40% | 0.00% | 79.91% |
| 0.95 | 3.20% | 0.00% | 5.51% |

## Interpretation

The synthetic generator produces a sharp trade-off around thresholds 0.75–0.85: increasing the threshold from 0.75 to 0.80 reduces conditional unsafe-ALLOW risk from 8.71% to 0.29%, but also reduces safe-session ALLOW recall from 94.60% to 86.42%. At 0.85 the observed synthetic unsafe-ALLOW risk reaches zero, but safe-session ALLOW recall falls further to 85.81%.

The zero observed synthetic risk at thresholds >=0.85 must **not** be interpreted as a security guarantee. It reflects separability in the authored synthetic scenarios and a finite sample. Previous repository experiments already show that dependence and distributional changes can materially worsen policy behavior.

## Limitation

This experiment is descriptive, not confirmatory. The synthetic labels are scenario definitions rather than independently observed security outcomes. The curve therefore characterizes the behavior of this generator/model pair, not enterprise deployment risk. External telemetry with defensible outcome labels remains necessary before making effectiveness claims.
