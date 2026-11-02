# Correlated telemetry-outage stress test — 2026-11-01

**Synthetic simulation only; exploratory and not preregistered.** 50,000 fixed generated observations (29,033 labeled safe; 20,967 labeled unsafe), three paired masking seeds. Each signal has 25% *expected* dropout under all arms. Existing policy thresholds and hard gates are unchanged.

## Measured masking structure

| Arm | Realized missing cells | Endpoint pair missingness phi | All eight missing |
|---|---:|---:|---:|
| Independent | 24.994% | -0.000 | 0.002% |
| Endpoint common-mode 50% | 25.006% | 0.499 | 0.214% |
| Endpoint common-mode 100% | 25.114% | 1.000 | 0.429% |
| All eight common-mode 100% | 25.125% | 1.000 | 25.125% |

## Primary outcome: unsafe ordinary ALLOW / scenario-labeled unsafe

| Mask arm | Renormalize | Neutral | Pessimistic | Explicit STEP_UP |
|---|---:|---:|---:|---:|
| Independent | 17.47% | 4.54% | 1.46% | 6.07% |
| Endpoint common-mode 50% | 20.13% | 5.78% | 2.82% | 7.67% |
| Endpoint common-mode 100% | 22.63% | 7.13% | 4.09% | 9.43% |
| All eight common-mode 100% | 9.34% | 9.34% | 9.34% | 9.34% |

## Safe-user friction: DENY / STEP_UP (safe denominator)

| Mask arm | Renormalize | Neutral | Pessimistic | Explicit STEP_UP |
|---|---:|---:|---:|---:|
| Independent | 0.08% / 7.59% | 0.27% / 25.55% | 20.97% / 43.62% | 0.00% / 63.86% |
| Endpoint common-mode 50% | 0.63% / 6.81% | 1.79% / 26.39% | 23.31% / 31.85% | 0.00% / 50.62% |
| Endpoint common-mode 100% | 1.23% / 6.04% | 3.30% / 27.58% | 25.91% / 20.00% | 0.00% / 37.40% |
| All eight common-mode 100% | 0.00% / 28.97% | 0.00% / 28.97% | 0.00% / 28.97% | 0.00% / 28.97% |

**Interpretation.** Under fixed per-signal marginal missingness, correlated endpoint-signal loss increased unsafe ordinary-ALLOW for all four policies. For pessimistic scoring, the mean rose from 1.46% (independent) to 4.09% (endpoint common-mode 100%) and 9.34% (all-signal common-mode). Under global common-mode dropout, each row has either all eight measurements or none, so the four policies make identical decisions: the missing rows all STEP_UP, and full rows use the same score/hard gates. This is a structural property of the simulation, not evidence that the policies are equivalent under ordinary partial missingness.

The renormalization result is **not monotone** in correlation: it rose to 22.63% under endpoint-only common-mode but fell to 9.34% under all-signal common-mode. This demonstrates why a single average missingness percentage is inadequate to characterize policy risk. Correlated outages may also change legitimate-user friction substantially; low unsafe-ALLOW cannot be interpreted without the safe-session DENY/STEP_UP breakdown.

## Verification and limits

Seven new unit tests passed, including marginal dropout and empirical correlation checks, all-missing behavior, non-endpoint mask invariance, paired flip reconciliation, repeatability, and input validation. Python compilation passed. The detailed JSON SHA-256 is `761aa3587b658ab70a989d01006e4bcffefe5c522fd00b771e3d77d415a04edc`; input CSV SHA-256 `2f1bbf71744f9ccc73d2f60618488c49b787c385c46bb90116152f9f612811f7`.

Results are descriptive means across three masking seeds applied to the **same synthetic rows**, not independent real-world samples or confidence intervals. No tenant telemetry, outage-duration distributions, independently verified labels, production policy outcomes, or device/time clustering are included. Common-mode group membership and correlation are stipulated, not learned. No real-world false-allow or false-deny claim follows.

**Next:** investigate device/time-clustered outages and pre-register the grouping and correlation model from authorized non-production observations; run repository-wide CI and full manuscript compilation.
