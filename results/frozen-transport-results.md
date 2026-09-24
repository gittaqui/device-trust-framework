# Frozen-policy transport under synthetic distribution shift

Date: 2026-09-23

## Question

If thresholds and a learned comparator are calibrated only on the nominal authored synthetic population, do they retain the calibration target when transported unchanged to populations with correlated and increasingly overlapping endpoint evidence?

## Protocol

- Synthetic train: 30,000 nominal sessions (`rho=0`, `overlap=0`, seed 100).
- Synthetic calibration: 10,000 nominal sessions (seed 200).
- Calibration objective: maximize ALLOW coverage subject to <=1% empirical unsafe-ALLOW risk.
- Frozen hand-policy ALLOW threshold: **0.789**.
- Frozen logistic probability threshold: **0.004426**.
- Synthetic target test sets: 30,000 sessions per condition, independent seeds 300-304.
- Neither model parameters nor thresholds are updated after nominal calibration.

## Results

| rho | overlap | model | coverage | unsafe risk among ALLOW | safe ALLOW recall |
|---:|---:|---|---:|---:|---:|
| 0.0 | 0.00 | Hand policy | 51.38% | 0.89% | 87.86% |
| 0.0 | 0.00 | Logistic | 58.49% | 0.91% | 100.00% |
| 0.6 | 0.00 | Hand policy | 55.11% | 5.77% | 90.33% |
| 0.6 | 0.00 | Logistic | 60.46% | 4.91% | 100.00% |
| 0.6 | 0.25 | Hand policy | 37.50% | 8.86% | 58.77% |
| 0.6 | 0.25 | Logistic | 61.91% | 8.36% | 97.54% |
| 0.6 | 0.50 | Hand policy | 22.33% | 19.12% | 31.04% |
| 0.6 | 0.50 | Logistic | 43.35% | 18.46% | 60.74% |
| 0.6 | 0.75 | Hand policy | 16.38% | 31.45% | 19.48% |
| 0.6 | 0.75 | Logistic | 32.44% | 30.90% | 38.90% |

## Interpretation

Condition-specific recalibration in the prior learned-baseline experiment hid a deployment-relevant failure mode. Once nominal thresholds are frozen, the <=1% calibration target does not transport. Positive dependence alone raises unsafe-ALLOW risk to 5.77% for the hand policy and 4.91% for logistic regression. Under strong overlap plus dependence, both exceed 30% unsafe risk among ALLOW decisions.

The learned linear comparator preserves substantially more ordinary-access coverage and safe-session recall, but it does **not** preserve the safety constraint. This suggests that the dominant problem under this stress design is distribution shift in the evidence, not merely poor hand-selected weights.

## Limitations

All populations, labels, shifts, and scenario prevalences are authored and synthetic. The overlap parameter and Gaussian dependence mechanism are stress-test constructions, not estimates of enterprise endpoint telemetry. These results therefore demonstrate failure under specified synthetic shifts; they do not estimate production risk. The single-run values also do not quantify repeated-seed uncertainty. External telemetry validation remains necessary.

## Reproduction

```bash
python src/evaluate_frozen_transport.py
pytest -q tests/test_frozen_transport.py
```
