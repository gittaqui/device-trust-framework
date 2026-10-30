# Coverage-stratified missing-evidence protocol (2026-10-29)

**Purpose.** Localize synthetic unsafe-ALLOW decisions by weighted telemetry completeness and scenario. This is a post-hoc diagnostic of the *already frozen* paired-mask experiment, not a new model or production access policy.

## Frozen inputs and design

- Reuse `src/generate_synthetic_data.py` (50,000 rows, seed `20260903`), `src/evaluate_missing_telemetry_paired.py`'s row validator and mask RNG (seed `20260904`), and `src/evaluate_missing_telemetry.py`'s current coverage/decision function.
- Compare nominal 25% missingness under the original MCAR and critical-signal-biased regimes. The mask is sampled once per observation and shared by every policy within a regime; different regimes do **not** share masks.
- Per-row coverage is the sum of weights for observed factors, not decision confidence. Four predeclared bins: `[0,0.50)`, `[0.50,0.75)`, `[0.75,1)`, and `1.00` (full observation, floating-point tolerance `1e-12`).
- Partition by scenario, coverage, and scenario × coverage. Separately, for synthetic `malware` and `protection_missing`, record whether the known critical gate signal is observed. These two scenarios are explicitly generated with `threat_risk >= 0.90` and `security_coverage <= 0.15`, respectively.
- Within each stratum, unsafe-ALLOW rate = `unsafe AND ALLOW / unsafe`; safe-DENY rate = `safe AND DENY / safe`; safe-STEP_UP rate = `safe AND STEP_UP / safe`. A rate is `null` if the relevant label denominator is zero, not zero percent. Preserve counts alongside rates. No confidence intervals are reported for these deterministic, scenario-constructed observations.

## Missingness taxonomy correction

The structured mask multiplies a *column-specific* dropout probability for `threat_risk`, `security_coverage`, and `identity_assurance`. It does **not** condition dropout on the realized signal value, an unobserved attack state, or an adversary's action. Therefore, it is **not an empirical MNAR or adversarial-missingness experiment**. It is a stylized heterogeneous-by-signal dropout stress test. A genuine value-dependent/MNAR study requires an explicitly specified mechanism and sensitivity analysis, and still cannot establish real-world missingness frequencies without authorized observations.

Methodological context checked 2026-10-29: Buczak, Chen, and Pauly (2023), *Analyzing the Effect of Imputation on Classification Performance under MCAR and MAR Missing Mechanisms*, *Entropy* 25(3), 521, DOI `10.3390/e25030521` (publisher: https://www.mdpi.com/1099-4300/25/3/521); Franc, Prusa, and Voracek (2023), *Optimal Strategies for Reject Option Classifiers*, *JMLR* 24(11):1–49 (journal: https://www.jmlr.org/papers/v24/21-0048.html). Neither validates the trust model or its weights.

## Reproduction

From the repository root:

```bash
python src/generate_synthetic_data.py --rows 50000 --seed 20260903 --output data/synthetic_endpoints.csv
python src/audit_missingness_by_coverage.py --input data/synthetic_endpoints.csv --missing-rate 0.25 --seed 20260904 --output results/coverage_strata_mcar.json
python src/audit_missingness_by_coverage.py --input data/synthetic_endpoints.csv --missing-rate 0.25 --structured --seed 20260904 --output results/coverage_strata_critical_signal_biased.json
python -m unittest discover -s tests -p 'test_*missing*py'
```

The output JSON is a generated local artifact, not required to be committed. Verify aggregate counts against the existing `results/paired_missing_telemetry_*.json` files. No confidential employer data is used.

## Claim boundary

The scenario generator deterministically assigns safety labels from scenario names; observations are not independent adjudications. Conditional rates can vary with the synthetic scenario mix, default weights, thresholds, and missingness design. The stratification is exploratory and should not be interpreted as a causal effect of missingness or an enterprise false-allow probability.
