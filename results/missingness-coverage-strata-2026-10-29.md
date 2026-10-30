# Synthetic missing-telemetry errors by evidence completeness — 2026-10-29

**Evidence:** synthetic-only, reproducible diagnostic of the existing paired-mask experiment. This document reports no observed enterprise access outcomes.

## Reconciliation and denominator

The generator produces 50,000 observations (29,033 scenario-labeled safe; 20,967 unsafe) with seed `20260903`. With 25% nominal masking and seed `20260904`, the MCAR and critical-signal-biased runs masked 24.89125% and 26.27325% of cells, respectively. The new audit exactly reproduces all previously frozen paired-strategy decision and error **counts** for both regimes; it does not replace or change those results. Within each row, all strategies receive the same mask.

In the following tables, `unsafe n` is the denominator for unsafe-ALLOW rates. Coverage is the **sum of observed factor weights**, not a probability of correctness. `FA` is a synthetic false ALLOW count.

## Critical-signal-biased dropout (50,000 synthetic observations)

| Weighted telemetry coverage | All rows | Unsafe n | Renormalize FA | Neutral FA | Pessimistic FA | Explicit step-up FA |
|---|---:|---:|---:|---:|---:|---:|
| [0, 0.50) | 3,629 | 1,541 | 436 (28.29%) | 0 | 0 | 0 |
| [0.50, 0.75) | 20,314 | 8,492 | 1,878 (22.11%) | 141 | 0 | 0 |
| [0.75, 1) | 22,411 | 9,362 | 1,764 (18.84%) | 754 | 30 | 718 |
| 1.00 | 3,646 | 1,572 | 185 (11.77%) | 185 | 185 | 185 |
| **All** | **50,000** | **20,967** | **4,263 (20.33%)** | **1,080** | **215** | **903** |

The complete-observation row is a useful counterexample to a missingness-only explanation: **185 of 1,572 unsafe synthetic sessions were ALLOW even with all eight signals present**. At full coverage the four policies agree by construction. Of these 185, **166 of 290 identity-risk** cases and **12 of 244 adversarially compliant** cases were ALLOW; the remaining seven were stale cases. This reflects the current score/threshold and scenario-label design, not missing evidence.

### Critical hard-gate signal availability

| Scenario | Gate signal | Gate status | Unsafe n | Renormalize FA | Pessimistic FA |
|---|---|---|---:|---:|---:|
| Malware | `threat_risk` | Observed | 1,864 | 0 | 0 |
| Malware | `threat_risk` | Missing | 1,609 | 206 | 0 |
| Protection missing | `security_coverage` | Observed | 1,644 | 0 | 0 |
| Protection missing | `security_coverage` | Missing | 1,390 | 415 | 0 |

When a generated hard-gate condition is observed, all policies deny those cases. When it is missing, renormalization sometimes allows the unsafe synthetic case. This is **descriptive**, not a causal estimate: observation status co-varies with overall coverage and the masking process.

## MCAR robustness check

| Weighted telemetry coverage | Unsafe n | Renormalize FA | Pessimistic FA | Explicit step-up FA |
|---|---:|---:|---:|---:|
| [0, 0.50) | 1,337 | 331 | 0 | 0 |
| [0.50, 0.75) | 7,997 | 1,494 | 0 | 0 |
| [0.75, 1) | 9,510 | 1,504 | 39 | 979 |
| 1.00 | 2,123 | 301 | 301 | 301 |
| **All** | **20,967** | **3,630** | **340** | **1,280** |

The same qualitative finding appears under MCAR: nonzero false-ALLOW cases persist with complete telemetry (301/2,123 unsafe sessions). Policy comparisons across regimes are not row-mask paired; only comparisons **within** a regime are paired.

## Scientific interpretation and limitations

1. **Two distinct failure channels:** critical evidence can be absent, concealing a known hard-gate condition; and the fully observed scoring rule can ALLOW some scenario-labeled unsafe cases. Missingness handling cannot correct the latter by itself.
2. **Trade-off:** conservative policies reduce synthetic unsafe ALLOW, but previous paired results show they also reduce ordinary access for safe sessions. This table is not a utility or optimal-policy analysis.
3. **No MNAR claim:** the critical-signal-biased mask uses signal-name-dependent dropout probabilities, not signal-value-dependent or adversarial dropout. It should be called a heterogeneous-by-signal stress test, not real-world MNAR.
4. **No inferential generalization:** labels are constructed from scenario definitions, the generator samples from stipulated distributions, and the data lack independently adjudicated access outcomes. No significance test or confidence interval is offered for real-world effectiveness.

**Next:** pre-register a value-dependent dropout stress test and a non-compensatory identity-risk ablation, then evaluate both on independently adjudicated, authorized non-production endpoint observations when available.

**Reproduction:** `experiments/missingness-coverage-strata-protocol.md`, `src/audit_missingness_by_coverage.py`, and `tests/test_audit_missingness_by_coverage.py`. The two full JSON outputs and SHA-256 checksums are available in the dated research package.
