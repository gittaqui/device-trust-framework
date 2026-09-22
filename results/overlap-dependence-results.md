# Class-overlap × signal-dependence stress test

Date: 2026-09-21

## Purpose

The authored synthetic scenarios are intentionally separable. This experiment asks whether the additive device-trust policy remains useful when that favorable assumption is deliberately weakened at the same time as within-session evidence becomes correlated.

**These are synthetic stress-test results, not real-world evidence.** The overlap mechanism is an artificial perturbation and must not be interpreted as an estimate of enterprise telemetry distributions.

## Method

For each signal, compute the pooled minimum and maximum across all eight authored scenarios. For overlap level `a`, interpolate each scenario's lower and upper range endpoints toward that pooled range:

`low'=(1-a)low+a*pooled_low`, `high'=(1-a)high+a*pooled_high`.

At `a=0`, the original scenario marginals are retained. Increasing `a` makes safe and unsafe scenarios progressively less separable. A one-factor Gaussian copula induces safety-oriented dependence (`rho=0` or `0.6`); threat/anomaly risk move inversely to the shared safety state. The existing trust model, weights, hard gates, scenario prevalence, and ALLOW threshold 0.80 are frozen. Each condition uses 50,000 sessions and seed `20260921`.

## Results

| rho | overlap | ordinary-access coverage | unsafe risk among ALLOW | safe-session ALLOW recall |
|---:|---:|---:|---:|---:|
| 0.0 | 0.00 | 50.668% | 0.308% | 87.340% |
| 0.0 | 0.25 | 37.710% | 0.143% | 65.111% |
| 0.0 | 0.50 | 5.614% | 0.855% | 9.624% |
| 0.0 | 0.75 | 0.816% | 9.314% | 1.280% |
| 0.6 | 0.00 | 54.036% | 4.031% | 89.667% |
| 0.6 | 0.25 | 34.290% | 7.547% | 54.816% |
| 0.6 | 0.50 | 20.034% | 17.251% | 28.665% |
| 0.6 | 0.75 | 14.788% | 29.862% | 17.934% |

### Per-scenario ALLOW rate at rho=0.6, overlap=0.75

| scenario | label | sessions | ALLOW | ALLOW rate |
|---|---|---:|---:|---:|
| healthy | safe | 25,063 | 4,676 | 18.657% |
| policy_drift | safe | 3,854 | 510 | 13.233% |
| stale | unsafe | 3,997 | 444 | 11.108% |
| identity_risk | unsafe | 4,014 | 512 | 12.755% |
| malware | unsafe | 3,489 | 357 | 10.232% |
| protection_missing | unsafe | 2,975 | 281 | 9.445% |
| mixed_degradation | unsafe | 3,525 | 264 | 7.489% |
| adversarial_compliant | unsafe | 3,083 | 350 | 11.353% |

## Interpretation

The favorable low-risk operating point does not survive simultaneous erosion of separability and positive evidence dependence. At `rho=0.6`, increasing overlap from 0 to 0.75 raises conditional unsafe-ALLOW risk from 4.031% to 29.862%, while safe-session ordinary-access recall falls from 89.667% to 17.934%. This is a collapse in discrimination, not merely a threshold-calibration issue.

The per-scenario table is also important: at the strongest tested stress, every unsafe scenario produces ALLOW decisions. The result therefore argues against presenting a fixed threshold as intrinsically safe and strengthens the case for external validation, calibration monitoring, and explicit uncertainty handling.

## Limitations

The pooled-range interpolation is deliberately adversarial and has no empirical calibration. The Gaussian copula captures only a simple dependence family. Scenario labels, prevalence, and the signal set remain authored. No confidential or production telemetry is used. Sampling uncertainty is not shown here; prior repository experiments separately implement Wilson intervals. These results cannot establish deployment effectiveness.
