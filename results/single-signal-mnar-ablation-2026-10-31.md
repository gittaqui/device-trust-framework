# Single-signal value-dependent missingness ablation — 2026-10-31

**Evidence class:** exploratory synthetic simulation, not enterprise access-control effectiveness. The design and hypotheses were selected after the October 30 all-signal result was known; this is not a preregistered confirmatory study.

Input: 50,000 seeded generated observations (29,033 scenario-labeled safe; 20,967 scenario-labeled unsafe). Three paired mask seeds: 20260904, 20260905, 20260906.
Each of eight signals has calibrated **25% expected** dropout. Beta=4 is applied to exactly the named target signal in single-signal arms; the other seven use MCAR at 25%. The all-eight arm applies beta=4 to all signals. A shared uniform draw for each row/signal/seed pairs the masks across all arms and policies.

## Primary endpoint: unsafe ordinary ALLOW / scenario-labeled unsafe

| Arm | Realized missing cells | Renormalize | Neutral | Pessimistic | Explicit STEP_UP |
|---|---:|---:|---:|---:|---:|
| MCAR baseline | 24.990% | 17.26% | 4.37% | 1.44% | 5.81% |
| Identity assurance only | 24.995% | 25.61% | 6.93% | 0.66% | 6.41% |
| Threat risk only | 24.977% | 21.43% | 4.88% | 1.52% | 5.69% |
| Security coverage only | 24.978% | 21.14% | 4.85% | 1.60% | 6.34% |
| All eight signals | 24.995% | 52.60% | 13.13% | 0.92% | 10.91% |

Means across three fixed-mask seeds; the same generated rows are reused. These are descriptive Monte Carlo rates, **not confidence intervals or estimates of population risk**.

## Legitimate-user friction (safe DENY / safe STEP_UP)

| Arm | Renormalize | Neutral | Pessimistic | Explicit STEP_UP |
|---|---:|---:|---:|---:|
| MCAR baseline | 0.09% / 7.53% | 0.26% / 25.60% | 21.04% / 43.45% | 0.00% / 63.72% |
| Identity assurance only | 0.06% / 7.29% | 0.17% / 23.16% | 18.18% / 43.26% | 0.00% / 61.67% |
| Threat risk only | 0.07% / 7.36% | 0.21% / 24.00% | 19.12% / 42.70% | 0.00% / 57.30% |
| Security coverage only | 0.06% / 7.35% | 0.21% / 23.37% | 18.57% / 43.20% | 0.00% / 59.72% |
| All eight signals | 0.00% / 1.51% | 0.01% / 10.56% | 8.38% / 33.29% | 0.00% / 41.44% |

## Paired per-scenario diagnosis (seed 20260904; renormalize)

| Arm | Identity-risk unsafe ALLOW | Malware unsafe ALLOW | Protection-missing unsafe ALLOW |
|---|---:|---:|---:|
| MCAR baseline | 1838/3912 (46.98%) | 214/3473 (6.16%) | 271/3034 (8.93%) |
| Identity assurance only | 3293/3912 (84.18%) | 220/3473 (6.33%) | 299/3034 (9.85%) |
| Threat risk only | 1854/3912 (47.39%) | 649/3473 (18.69%) | 285/3034 (9.39%) |
| Security coverage only | 1920/3912 (49.08%) | 219/3473 (6.31%) | 926/3034 (30.52%) |
| All eight signals | 3550/3912 (90.75%) | 1916/3473 (55.17%) | 1336/3034 (44.03%) |

## Value-dependent dropout sanity check (seed 20260904)

| Targeted signal | Low-risk dropout (risk <= 0.30) | High-risk dropout (risk >= 0.70) |
|---|---:|---:|
| identity_assurance | 6805/40085 (16.98%) | 2603/3297 (78.95%) |
| threat_risk | 5022/36843 (13.63%) | 3976/5095 (78.04%) |
| security_coverage | 7911/42720 (18.52%) | 2585/3034 (85.20%) |

## Interpretation and boundaries

Renormalization unsafe-ALLOW increases most when identity assurance alone is selectively missing (17.26% MCAR vs 25.61% identity-only), while threat-risk and security-coverage concealment each raise unsafe-ALLOW to approximately 21%. All-eight value-dependent masking increases unsafe-ALLOW to 52.60%. These contrasts isolate **masking interventions in this fixed synthetic generator**, not causal effects in enterprise telemetry. The all-eight effect is not the sum of the three targeted effects: other signals and policy interactions are present.

Identity-only masking predominantly affects the identity-risk scenario; threat-risk masking predominantly affects the malware scenario; security-coverage masking predominantly affects the protection-missing scenario. These patterns partly reflect the generator-defined scenario features and policy hard gates, so they cannot be treated as independently discovered attack signatures.

The pessimistic policy has lower unsafe-ALLOW under most arms but substantial safe DENY/STEP_UP, and its unsafe-ALLOW rate can increase slightly in some single-signal arms. No strategy is recommended as production-optimal from these data.

## Reproduction and verification

~~~bash
python src/generate_synthetic_data.py --rows 50000 --seed 20260903 --output data/synthetic_endpoints.csv
python src/evaluate_single_signal_mnar_ablation.py --input data/synthetic_endpoints.csv --rate 0.25 --beta 4 --seeds 20260904 20260905 20260906 --output results/single_signal_mnar_ablation_2026-10-31.json
python -m unittest discover -s tests -p 'test_single_signal_mnar_ablation.py'
~~~

The baseline MCAR and all-eight arms were cross-checked against the October 30 frozen detailed JSON, with exact matching counts for all four policies and all three seeds. The detailed new JSON is included in the handoff package, not in the GitHub commit.

## Limitations and next experiment

The mask mechanism depends on each potentially unobserved value, a stipulated MNAR-by-construction selection mechanism; its probability is calibrated using the complete synthetic sample. Real telemetry outages could be correlated across signals and devices, and missingness mechanisms cannot generally be identified from observed data alone without assumptions. No tenant measurements, independent safety labels, model calibration, confidence intervals, or significance claims are available. Three mask seeds are not independent populations.

Next: run a held-out, independently adjudicated non-production device evaluation and predefine acceptable false-ALLOW/friction costs; investigate correlated outages and sensitivity to the assumed dropout model.

