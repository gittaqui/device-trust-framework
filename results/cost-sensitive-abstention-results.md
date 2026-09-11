# Cost-sensitive abstention analysis

Date: 2026-09-10

## Research question

How sensitive is the apparent preference among binary compliance, additive trust thresholds, and the identity/behavior guard to the assumed operational cost of STEP_UP and to uncertainty about whether synthetic `identity_risk` states can sometimes be benign?

This is a **synthetic decision-cost sensitivity analysis**. It does not estimate production incident cost, MFA burden, or the real prevalence of benign identity anomalies.

## Cost model

Losses are normalized relative to an unsafe ordinary-access `ALLOW` decision:

- unsafe `ALLOW`: 1.00
- `STEP_UP`: varied over 0.025, 0.05, 0.10, and 0.20
- safe `DENY`: 0.50
- safe `ALLOW`: 0
- unsafe `DENY`: 0

`STEP_UP` is charged for both safe and unsafe sessions because verification/escalation consumes user or operational effort even when it prevents an unsafe ordinary-access decision. The numerical costs are sensitivity parameters, not empirical estimates.

## Seeded synthetic setup

- rows: 50,000
- data seed: `20260903`
- benign-overlap seed: `20260909`
- tested additive allow thresholds: 0.70, 0.75, 0.80, 0.85
- tested guarded thresholds: 0.70, 0.75, 0.80
- benign identity-overlap fractions: 0%, 25%, 50%, 100%

## Preferred policy by assumption

| Benign identity overlap | STEP_UP=0.025 | STEP_UP=0.05 | STEP_UP=0.10 | STEP_UP=0.20 |
|---:|---|---|---|---|
| 0% | guarded 0.80 | guarded 0.80 | guarded 0.75 | guarded 0.75 |
| 25% | guarded 0.80 | guarded 0.80 | guarded 0.75 | guarded 0.75 |
| 50% | guarded 0.80 | guarded 0.80 | guarded 0.75 | guarded 0.75 |
| 100% | additive 0.80 | additive 0.80 | additive 0.75 | additive 0.75 |

A finer 10-percentage-point overlap sweep showed the first change at very high overlap: with STEP_UP cost 0.20, additive 0.75 became preferred at 90% overlap; with STEP_UP costs 0.025--0.10, the guarded policies remained preferred through 90% and changed only at 100% overlap.

## Representative normalized losses

At 0% benign identity overlap:

| Policy | STEP_UP=0.05 | STEP_UP=0.10 | STEP_UP=0.20 |
|---|---:|---:|---:|
| Binary compliance | 0.43428 | 0.43428 | 0.43428 |
| Additive 0.75 | 0.06347 | 0.07452 | 0.09663 |
| Additive 0.80 | 0.01742 | 0.03339 | 0.06534 |
| Guarded 0.75 | 0.01861 | **0.03203** | **0.05885** |
| Guarded 0.80 | **0.01605** | 0.03210 | 0.06419 |

At 100% benign identity overlap:

| Policy | STEP_UP=0.05 | STEP_UP=0.10 | STEP_UP=0.20 |
|---|---:|---:|---:|
| Binary compliance | 0.35604 | 0.35604 | 0.35604 |
| Additive 0.75 | 0.01785 | **0.02890** | **0.05101** |
| Additive 0.80 | **0.01598** | 0.03195 | 0.06390 |
| Guarded 0.75 | 0.01861 | 0.03203 | 0.05885 |
| Guarded 0.80 | 0.01605 | 0.03210 | 0.06419 |

## Interpretation

The experiment rejects a simplistic claim that one threshold/guard is universally best. Under the current synthetic labeling assumptions, strict guarded policies minimize normalized loss when verification is relatively cheap. When verification becomes more expensive, guarded 0.75 becomes preferable because it reduces the number of STEP_UP decisions while accepting a small increase in unsafe ordinary access. If all synthetic `identity_risk` sessions are reinterpreted as benign, additive policies become preferable because the guard continues to challenge sessions that the revised labels now call legitimate.

This is consistent with reject-option decision theory: abstention can reduce classification error, but its usefulness depends on the cost assigned to rejection/verification and on the calibration of ambiguous regions. Chow (1970) formalized the error-reject trade-off, Herbei and Wegkamp (2006) studied classification with a reject option, and Mena, Pujol, and Vitrià (2020) evaluated uncertainty-based rejection wrappers in IEEE Access.

## Limitations

1. All outcome labels and feature distributions in this analysis are synthetic.
2. The cost ratios are deliberately hypothetical and are not measured enterprise costs.
3. Relabeling `identity_risk` rows changes label interpretation without changing their features; this is a sensitivity analysis, not a generative model of real benign identity anomalies.
4. The same synthetic design has influenced policy development, so these results are exploratory and vulnerable to design overfitting.
5. A production choice requires externally sourced, temporally separated telemetry plus organization-specific estimates of verification and incident cost.

## Reproducibility

Run:

```bash
PYTHONPATH=src python src/evaluate_cost_sensitive_abstention.py --rows 50000
```

The accompanying unit tests verify cost semantics, invalid-cost handling, and that preferred policies can change as cost and benign-overlap assumptions change.
