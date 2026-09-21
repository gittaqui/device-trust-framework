# Dependence-aware risk-coverage study

**Study date:** 2026-09-20  
**Synthetic only:** yes  
**Rows per condition:** 50,000  
**Seed:** `20260920`

## Question

Does the apparently low-risk ALLOW operating region survive when endpoint telemetry signals are positively dependent rather than independently sampled within each authored scenario?

The experiment reuses the one-factor Gaussian-copula generator from `evaluate_signal_dependence.py`, preserving scenario marginal ranges, labels, prevalence, model weights and hard gates. It sweeps the additive model's ALLOW threshold and adds 95% Wilson intervals. `rho` is the latent Gaussian dependence parameter; observed Pearson correlations are not asserted to equal it.

## Results

| rho | threshold | coverage | unsafe risk among ALLOW | 95% Wilson CI | safe-session ALLOW recall |
|---:|---:|---:|---:|---:|---:|
| 0.0 | 0.75 | 60.25% | 9.072% | 8.753–9.402% | 94.70% |
| 0.0 | 0.80 | 50.29% | 0.239% | 0.185–0.307% | 86.72% |
| 0.0 | 0.85 | 49.82% | 0.000% | 0.000–0.015% | 86.12% |
| 0.3 | 0.75 | 61.25% | 11.141% | 10.793–11.498% | 94.08% |
| 0.3 | 0.80 | 52.10% | 2.088% | 1.922–2.269% | 88.18% |
| 0.3 | 0.85 | 49.83% | 0.000% | 0.000–0.015% | 86.13% |
| 0.6 | 0.75 | 62.18% | 12.687% | 12.321–13.061% | 93.84% |
| 0.6 | 0.80 | 53.87% | 4.084% | 3.854–4.327% | 89.32% |
| 0.6 | 0.85 | 49.95% | 0.040% | 0.022–0.074% | 86.31% |
| 0.8 | 0.75 | 62.65% | 13.468% | 13.094–13.850% | 93.72% |
| 0.8 | 0.80 | 54.95% | 5.376% | 5.116–5.649% | 89.87% |
| 0.8 | 0.85 | 50.13% | 0.195% | 0.148–0.258% | 86.49% |

## Interpretation

The earlier independent-signal study's attractive threshold-0.80 operating point is not structurally stable. At the same threshold, conditional unsafe-ALLOW risk rises from 0.239% at rho=0 to 5.376% at rho=0.8, while ordinary-access coverage changes only from 50.29% to 54.95%. The 95% Wilson intervals are narrow enough under this synthetic sample to rule out Monte Carlo noise as an explanation for that difference.

More importantly, the observed zero unsafe-ALLOW count at threshold 0.85 does not survive stronger dependence. It remains zero at rho=0.3, becomes 0.040% at rho=0.6, and reaches 0.195% (95% CI 0.148–0.258%) at rho=0.8. Thus a threshold that appeared failure-free under independent authored draws can admit unsafe synthetic sessions once signals co-move.

## Limitations

These are not real-world endpoint results. Wilson intervals quantify finite-sample uncertainty conditional on this generator only; they do not cover generator misspecification, novel attacks, measurement error, temporal dependence, prevalence shift, or external validity. The one-factor Gaussian copula is itself an authored dependence model and does not establish realistic enterprise telemetry correlation. No production or confidential employer data was used.

## Manuscript implication

The paper should not recommend a universal ALLOW threshold from synthetic point estimates. Threshold selection must be reported jointly with dependence assumptions, risk/coverage trade-offs and uncertainty, and any deployment recommendation must await external validation.
