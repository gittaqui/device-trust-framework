# Paired Policy Statistical Analysis

Date: 2026-09-08

## Scope

This experiment adds uncertainty estimates and paired statistical comparisons to the existing synthetic policy evaluation. It does **not** provide real-world effectiveness evidence. All values below are conditional on the repository's synthetic scenario generator, its scenario prevalence assumptions, the fixed seed `20260903`, and 50,000 generated endpoint sessions.

The policies compared on the **same rows** are:

1. `binary`: compliance >= 0.5 => ALLOW, otherwise DENY.
2. `additive_075`: multidimensional weighted model with ALLOW threshold 0.75.
3. `additive_080`: the same model with ALLOW threshold 0.80.
4. `guarded_075`: threshold 0.75 plus the experimental identity/behavior STEP_UP guard.

For ordinary-access correctness, ALLOW is treated as correct for rows labeled safe for ordinary access; STEP_UP or DENY is treated as correct for rows labeled unsafe. This binary correctness definition is used only for paired McNemar comparisons. Because STEP_UP and DENY have different operational consequences, policy selection must also consider the component metrics separately.

## Population

- Total rows: 50,000
- Safe rows: 29,033
- Unsafe rows: 20,967
- Seed: 20260903

## Results

| Policy | False-ALLOW rate on unsafe rows | Safe STEP_UP rate | Ordinary-access accuracy |
|---|---:|---:|---:|
| Binary compliance | 93.74% (95% CI 93.40%-94.06%) | 0.00% (95% CI 0.00%-0.01%) | 52.45% (95% CI 52.01%-52.89%) |
| Additive 0.75 | 12.50% (95% CI 12.06%-12.96%) | 5.40% (95% CI 5.15%-5.67%) | 91.62% (95% CI 91.38%-91.86%) |
| Additive 0.80 | 0.34% (95% CI 0.27%-0.43%) | 13.58% (95% CI 13.19%-13.98%) | 91.97% (95% CI 91.73%-92.20%) |
| Guarded 0.75 | 1.24% (95% CI 1.10%-1.40%) | 5.40% (95% CI 5.15%-5.67%) | 96.34% (95% CI 96.18%-96.50%) |

The Wilson score interval is used for the individual binomial rates.

## Paired comparisons

Continuity-corrected McNemar tests compare row-level ordinary-access correctness for two policies evaluated on the identical synthetic sessions.

| Comparison | First only correct | Second only correct | chi-square (cc) | p-value |
|---|---:|---:|---:|---:|
| Binary vs additive 0.75 | 0 | 19,585 | 19,583.000 | <1e-300 |
| Binary vs additive 0.80 | 0 | 19,759 | 19,757.000 | <1e-300 |
| Binary vs guarded 0.75 | 0 | 21,946 | 21,944.000 | <1e-300 |
| Additive 0.75 vs additive 0.80 | 2,375 | 2,549 | 6.078 | 0.0137 |
| Additive 0.75 vs guarded 0.75 | 0 | 2,361 | 2,359.000 | <1e-300 |
| Additive 0.80 vs guarded 0.75 | 260 | 2,447 | 1,765.274 | <1e-300 |

These p-values are **not evidence of real-world superiority**. With a large synthetic sample, very small differences can become statistically detectable, and the observations are generated from assumptions chosen by this project. Effect sizes and operational trade-offs are therefore more important than significance alone.

## Interpretation

### Binary compliance is an intentionally weak baseline

The binary baseline false-allows 93.74% of unsafe synthetic cases because many unsafe scenarios were deliberately constructed to remain nominally compliant. This establishes that the generator contains the intended "compliant-but-risky" condition, but it must not be presented as evidence that real compliance systems have a 93.74% false-allow rate.

### Raising the threshold sharply reduces unsafe ALLOW decisions but increases friction

Moving the additive threshold from 0.75 to 0.80 reduces synthetic false ALLOW from 12.50% to 0.34%, while safe STEP_UP increases from 5.40% to 13.58%. The paired ordinary-access difference is statistically detectable (`p=0.0137`), but the more important result is the security/friction trade-off.

### The targeted guard changes a different part of the policy surface

The guarded 0.75 policy produces 1.24% synthetic false ALLOW while retaining the 5.40% safe STEP_UP rate observed for additive 0.75. In this generator, this yields higher ordinary-access accuracy than either global-threshold policy. However, the current safe scenarios do not substantially overlap the guard's identity-risk region, so the apparent friction advantage is partly a property of the synthetic data design. External or more adversarially overlapping benign distributions are required before making a policy recommendation.

## Statistical methodology rationale

Dietterich's analysis of paired classifier comparisons found McNemar's test to have acceptable Type-I error for a single fixed evaluation set. We use it here because every policy evaluates the exact same synthetic rows. This use is diagnostic rather than confirmatory: the policies were developed iteratively on the same synthetic design, so the p-values must not be interpreted as if they came from a preregistered independent test set.

## Limitations

1. Scenario labels, feature ranges, and prevalence are synthetic design choices.
2. The same synthetic framework informed policy development, creating design-overfitting risk.
3. Wilson intervals quantify sampling variability under the generator, not uncertainty about whether the generator represents enterprise reality.
4. McNemar correctness collapses STEP_UP and DENY into the same ordinary-access-blocked class; operational analysis must keep them separate.
5. Multiple pairwise comparisons are exploratory and are not used to make a single confirmatory hypothesis claim.
6. No confidential employer data or production endpoint telemetry was used.
7. No LANL external-telemetry effectiveness result is claimed here.

## Reproduction

```bash
python src/evaluate_policy_statistics.py --rows 50000 --seed 20260903
```

Run the test suite after changes:

```bash
pytest -q
```

## Next step

Run the same reporting framework on a temporally held-out external telemetry experiment once the LANL data are obtained. Before external evaluation, freeze the proxy definitions, safety-label construction, and primary policy comparison so the external run functions as a genuine holdout rather than another tuning dataset.
