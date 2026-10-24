# Paired missing-telemetry audit — 2026-10-23

**Evidence category: deterministic synthetic experiment.** Not an Intune deployment, not externally labeled endpoint evidence, and not a production policy evaluation.

## Why this audit was necessary

The repository's existing `src/evaluate_missing_telemetry.py` offsets its RNG seed by `STRATEGY_IDS[strategy]`. The five policies are therefore compared under *different missing-data masks*, although they use the same 50,000-row source population. The resulting differences mix policy behavior with mask sampling variability. Further, `confidence` calculates `(weighted_observed / observed_weight) * observed_weight`, which is algebraically identical to the `pessimistic` score `weighted_observed` for positive observed weight; both share hard gates and the zero-observation behavior. They are not distinct algorithmic baselines.

## Corrected protocol

`src/evaluate_missing_telemetry_paired.py` creates **one mask per endpoint observation per regime/rate**, then evaluates every policy on that exact masked observation. It validates complete synthetic inputs before masking, reports numerator/denominator counts and realized missingness, and tracks paired decision disagreements against `renormalize`. The underlying policy implementation and original historical results remain unchanged for provenance.

Generator: `src/generate_synthetic_data.py` (50,000 synthetic rows, seed `20260903`). Mask seed: `20260904`. Nominal missingness: 25%. Masking models: MCAR and the existing critical-signal-biased outage model. The latter is **not** asserted to be an empirically validated missing-not-at-random mechanism. The two regimes are not compared as matched masks to each other; pairing applies to strategies within each regime.

## Recomputed descriptive results

| Mask model | Strategy | Unsafe ordinary ALLOW | Safe STEP_UP | Safe DENY |
|---|---|---:|---:|---:|
| MCAR | renormalize | 17.31% | 7.56% | 0.09% |
| MCAR | neutral | 4.74% | 25.80% | 0.26% |
| MCAR | pessimistic | 1.62% | 43.17% | 21.22% |
| MCAR | confidence | 1.62% | 43.17% | 21.22% |
| MCAR | step_up | 6.10% | 63.98% | 0.00% |
| Critical-signal-biased | renormalize | 20.33% | 9.70% | 0.18% |
| Critical-signal-biased | neutral | 5.15% | 29.55% | 0.56% |
| Critical-signal-biased | pessimistic | 1.03% | 44.77% | 25.50% |
| Critical-signal-biased | confidence | 1.03% | 44.77% | 25.50% |
| Critical-signal-biased | step_up | 4.31% | 78.60% | 0.00% |

The realized masked-cell fractions were 24.89% (MCAR) and 26.27% (critical-signal-biased), rather than exactly 25%. See the two accompanying JSON files for unrounded rates, counts, scenario distribution and paired disagreements. `confidence` and `pessimistic` yielded identical decisions across all 50,000 rows in each regime.

## Limitations and claim boundary

- The generator itself defines the safe/unsafe labels and feature distributions; reported percentages **cannot** be used as field estimates of security effectiveness or friction.
- Paired masks remove one avoidable confound but do not correct the generator's construct-validity limitations or substitute for independent endpoint evidence.
- The audit compares the existing five named implementations, but there are only **four unique policy decision rules** under their present definitions.
- The existing `decide_partial` hard-gate return reports coverage `1.0` even if telemetry is partial; this audit deliberately does not use that coverage value. Fix separately if reporting per-decision coverage.
- The legacy `confidence` and `pessimistic` columns in `results/missing-telemetry-results.md` should not be interpreted as evidence of an algorithmic difference. Preserve the original table as historical exploratory output and point readers to this correction.
- No independent lab or real-world device-trust validation was performed.

## Reproduce

```bash
python src/generate_synthetic_data.py --rows 50000 --output data/synthetic_endpoints.csv --seed 20260903
python src/evaluate_missing_telemetry_paired.py --input data/synthetic_endpoints.csv --missing-rate 0.25 --output results/paired_missing_telemetry_mcar.json
python src/evaluate_missing_telemetry_paired.py --input data/synthetic_endpoints.csv --missing-rate 0.25 --structured --output results/paired_missing_telemetry_critical_signal_biased.json
python -m unittest discover -s tests -p 'test_missing_telemetry_paired.py' -v
```

## Verified methodological references (metadata checked 2026-10-23)

- Thomas G. Dietterich, “Approximate Statistical Tests for Comparing Supervised Classification Learning Algorithms,” *Neural Computation*, 10(7), 1895–1923 (1998), DOI: `10.1162/089976698300017197`. Source: https://pubmed.ncbi.nlm.nih.gov/9744903/. Supports paired evaluation reasoning; **not** a claim of statistical significance for this synthetic experiment.
- Ricardo Cardoso Pereira, Pedro Henriques Abreu, Pedro Pereira Rodrigues, and Mário A. T. Figueiredo, “Imputation of data Missing Not at Random: Artificial generation and benchmark analysis,” *Expert Systems with Applications*, 249, article 123654 (2024), DOI: `10.1016/j.eswa.2024.123654`. Publisher: https://doi.org/10.1016/j.eswa.2024.123654. Motivates explicit missingness-mechanism stress tests; does **not** validate this project's outage model.
