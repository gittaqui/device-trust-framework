# Value-dependent missingness sensitivity protocol — 2026-10-30

**Status:** exploratory synthetic sensitivity analysis, not preregistered before outcomes were inspected. No enterprise performance claim.

## Research question and frozen inputs

Holding the *expected per-column missing fraction* fixed, how does preferential loss of less-safe values change false ordinary-ALLOW and legitimate-user friction? Reuse the repository's synthetic generator (50,000 rows, seed 20260903), partial-decision function, input validator, existing weights and thresholds. Scenario labels are generator-defined, not independently adjudicated. Policies: renormalize, neutral, pessimistic, explicit STEP_UP. The confidence policy is algebraically identical to pessimistic and is not a separate comparator.

## Mask mechanism

For row i and signal j, let r_ij be the risk-oriented value: x_ij for threat_risk and anomaly_risk; 1-x_ij for all positive safety/assurance signals. Define

    P(M_ij=1 | x_ij) = sigmoid(alpha_j(beta) + beta*(r_ij-0.5))

for beta = 0, 2, 4. Calibrate alpha_j(beta) by bisection using the fixed complete synthetic input so that the *mean expected missingness probability* is 0.25 **separately for each column**. Realized Bernoulli rates can differ. Beta 0 is MCAR by construction; beta > 0 is MNAR **by construction** because dropout probability depends on the value being hidden. This does not establish an empirical enterprise MNAR mechanism.

For each of seeds 20260904, 20260905, 20260906, draw one uniform per row and signal and reuse it across all beta arms and policies. This creates paired Monte Carlo comparisons across strengths and policies. No scoring, weights, hard gates, or policy thresholds are changed.

## Outcomes and checks

Primary: unsafe ALLOW / scenario-labeled unsafe. Secondary: safe DENY / scenario-labeled safe, safe STEP_UP / scenario-labeled safe, safe ALLOW, per-scenario unsafe ALLOW. Report counts, denominators, realized missing fractions, and conditional dropout in low-risk (r<=0.30) and high-risk (r>=0.70) bins for identity assurance, threat risk and security coverage. Per-seed min–max is mask-RNG variability on a fixed synthetic sample, **not a confidence interval**. Unit tests check calibration, risk orientation, determinism, pairing, denominator reconciliation and invalid inputs.

## Threats to validity

All eight columns have value-dependent loss, potentially exaggerating simultaneous concealment. Mask draws are conditionally independent given values. The calibration uses the full synthetic population, not field-derived failure frequencies. Generator scenario labels and features were co-designed with the policy. The three seeds do not constitute independent enterprise populations. This experiment is exploratory and was documented after viewing outcomes; it must not be described as preregistered, causal, externally validated, or production-optimal.

## Verified peer-reviewed references (2026-10-30)

- Donald B. Rubin (1976), *Inference and missing data*, Biometrika 63(3):581–592, DOI 10.1093/biomet/63.3.581. Publisher: https://academic.oup.com/biomet/article-abstract/63/3/581/270932
- Roderick J. Little (2021), *Missing Data Assumptions*, Annual Review of Statistics and Its Application 8:89–107, DOI 10.1146/annurev-statistics-040720-031104. Publisher: https://www.annualreviews.org/content/journals/10.1146/annurev-statistics-040720-031104

Neither validates this device-trust model or the simulated dropout assumptions.

## Reproduction

~~~bash
python src/generate_synthetic_data.py --rows 50000 --seed 20260903 --output data/synthetic_endpoints.csv
python src/evaluate_value_dependent_missingness.py --input data/synthetic_endpoints.csv --rate 0.25 --seeds 20260904 20260905 20260906 --output results/value_dependent_missingness_2026-10-30.json
python -m unittest discover -s tests -p 'test_value_dependent_missingness.py'
~~~

The compact checked results and detailed JSON SHA-256 are in results/value-dependent-missingness-2026-10-30.md. The beta=0 run uses a different RNG stream from the previously frozen MCAR audit; do not treat its counts as an exact reproduction of that earlier run.
