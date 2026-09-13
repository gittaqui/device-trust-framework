# Attribute-quorum alternative baseline

Date: 2026-09-12

## Purpose

The current Device Trust Framework uses a weighted additive score plus hard safety gates, and separately evaluates an identity/anomaly STEP_UP guard. This experiment adds a structurally different comparator so the manuscript does not compare only against policies designed inside this repository.

Bhattarai, Kulkarni, and Niamat (NAECON 2024, DOI `10.1109/NAECON61878.2024.10670642`) describe a trust-score Zero Trust model for advanced metering infrastructure in which access requires both an aggregate trust threshold and more than half of the individual attributes to meet their own thresholds. The experiment here is **inspired by that decision structure**, but it is not a reproduction of their implementation and does not claim equivalence to their domain, attributes, thresholds, or case study.

## Baseline definition

For the eight Device Trust safety-oriented factors (six positive signals plus inverted threat/anomaly risk):

1. preserve the repository's existing hard DENY gates;
2. require the existing additive score to reach the 0.75 ALLOW threshold;
3. additionally require at least `k` of eight factors to reach a uniform per-factor threshold `q`;
4. if the additive model would ALLOW but the quorum is not met, return STEP_UP rather than DENY;
5. retain the existing 0.55 lower STEP_UP threshold.

No value in the `q`/`k` sweep is presented as a production recommendation. Uniform per-factor thresholds are intentionally simple so the baseline remains transparent.

## Seeded synthetic sensitivity results

Population: 50,000 generated rows, seed `20260903`. These are synthetic mechanism results only.

| Per-factor q | Required k/8 | Unsafe false ALLOW | Safe STEP_UP | Safe DENY |
|---:|---:|---:|---:|---:|
| 0.60 | 5 | 12.48% | 5.40% | 0.00% |
| 0.60 | 6 | 12.14% | 5.40% | 0.00% |
| 0.60 | 7 | 0.25% | 5.40% | 0.00% |
| 0.70 | 5 | 11.88% | 5.40% | 0.00% |
| 0.70 | 6 | 11.21% | 5.40% | 0.00% |
| 0.70 | 7 | **0.00%** | 6.64% | 0.00% |
| 0.75 | 5 | 11.25% | 5.40% | 0.00% |
| 0.75 | 6 | 8.74% | 5.40% | 0.00% |
| 0.75 | 7 | **0.00%** | 8.20% | 0.00% |

For comparison, earlier experiments on the identical seeded population reported 12.50% false ALLOW / 5.40% safe STEP_UP for additive 0.75 and 1.24% / 5.40% for the hand-crafted identity-guarded 0.75 policy.

## Per-scenario diagnostic for q=0.70, k=7

| Scenario | ALLOW | STEP_UP | DENY |
|---|---:|---:|---:|
| healthy | 100.00% | 0.00% | 0.00% |
| policy_drift | 53.18% | 46.82% | 0.00% |
| stale | 0.00% | 100.00% | 0.00% |
| identity_risk | 0.00% | 100.00% | 0.00% |
| malware | 0.00% | 0.00% | 100.00% |
| protection_missing | 0.00% | 0.00% | 100.00% |
| mixed_degradation | 0.00% | 32.64% | 67.36% |
| adversarial_compliant | 0.00% | 100.00% | 0.00% |

## Interpretation

The main finding is not that `q=0.70, k=7` is optimal. The stronger conclusion is that **non-compensation can be implemented without a signal-specific identity guard**: an aggregate-score-plus-quorum policy removes all false ALLOWs in the current synthetic population at the cost of increasing benign STEP_UP from 5.40% to 6.64%.

However, the result is highly dependent on the synthetic scenario geometry. In particular, the current generator tends to make unsafe identity/adversarial scenarios weak on at least two factors, while healthy rows are strong across all factors and policy-drift rows are mainly weak on compliance. A 7-of-8 quorum therefore aligns unusually well with the generator. This is a design-overfitting risk, not evidence of production superiority.

This baseline is useful for the manuscript because it changes the scientific question from "does our proposed guard beat binary compliance?" to the stronger question "which transparent non-compensatory decision structures retain security under external telemetry and benign overlap?"

## Claim boundary

These percentages are **synthetic results** generated from repository-defined labels and feature ranges. They do not estimate enterprise attack prevalence, false-positive rates, production security efficacy, or real-world user friction. The externally frozen validation protocol remains unchanged; this exploratory baseline must not be tuned using the future external evaluation interval.
