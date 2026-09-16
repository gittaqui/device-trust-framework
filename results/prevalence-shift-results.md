# Scenario-Prevalence Robustness Study

**Date:** 2026-09-15  
**Evidence class:** synthetic only; not real-world validation.

## Question

Does the relative behavior of the additive 0.75, identity-guarded 0.75, and exploratory attribute-quorum (q=0.70, 7/8) policies remain stable when only the prevalence of the authored endpoint scenarios changes?

Per-scenario signal distributions, model weights, thresholds, and hard gates were held fixed. Each mixture contains 50,000 seeded synthetic sessions (`seed=20260915`). The mixtures are stress-test assumptions, not estimates of enterprise prevalence.

## Results

| Mixture | Policy | Unsafe false ALLOW | Safe STEP_UP |
|---|---|---:|---:|
| Baseline | Additive .75 | 13.03% | 5.29% |
| Baseline | Guarded .75 | 1.30% | 5.29% |
| Baseline | Quorum .70 / 7-of-8 | 0.00% | 6.59% |
| Benign-heavy | Additive .75 | 14.22% | 4.40% |
| Benign-heavy | Guarded .75 | 1.36% | 4.40% |
| Benign-heavy | Quorum .70 / 7-of-8 | 0.00% | 5.44% |
| Identity-heavy | Additive .75 | 26.95% | 6.18% |
| Identity-heavy | Guarded .75 | 1.07% | 6.18% |
| Identity-heavy | Quorum .70 / 7-of-8 | 0.00% | 7.61% |
| Adversarial-heavy | Additive .75 | 12.38% | 5.97% |
| Adversarial-heavy | Guarded .75 | 2.67% | 5.97% |
| Adversarial-heavy | Quorum .70 / 7-of-8 | 0.00% | 7.24% |
| Hard-gate-heavy | Additive .75 | 8.17% | 5.97% |
| Hard-gate-heavy | Guarded .75 | 0.62% | 5.97% |
| Hard-gate-heavy | Quorum .70 / 7-of-8 | 0.00% | 7.24% |

## Interpretation

The qualitative ordering is stable across these five synthetic mixtures: the guarded policy substantially reduces unsafe ordinary access relative to the additive policy without changing safe-session STEP_UP in these authored scenarios; the 7-of-8 quorum eliminates synthetic false ALLOWs but consistently adds roughly 1.0--1.4 percentage points of safe STEP_UP burden.

The additive policy is highly prevalence-sensitive: false ALLOW rises to 26.95% in the identity-heavy mixture because the authored identity-risk scenario is precisely where additive compensation is weakest. Conversely, hard-gate-heavy mixtures lower false ALLOW because malware and protection-missing scenarios are deterministically denied by existing hard gates.

## Limitations

This experiment changes mixture prevalence only. It assumes each scenario's conditional signal distribution remains unchanged, so it is a controlled analogue of prior-probability shift, not a test of covariate or concept shift. The favorable quorum result remains tightly coupled to the synthetic scenario construction and must not be described as real-world superiority. No prevalence mixture here is claimed to represent a real enterprise fleet.

The next robustness study should perturb within-scenario signal distributions (covariate shift) or, preferably, execute the frozen external-validation protocol on independent telemetry.
