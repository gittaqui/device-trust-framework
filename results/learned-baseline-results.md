# Learned linear baseline under overlap and dependence

Date: 2026-09-22

## Question

Is the hand-weighted trust policy's degradation under ambiguous/correlated telemetry mainly a consequence of fixed expert weights, or does a simple learned linear comparator face the same coverage-risk trade-off?

## Protocol

All data are synthetic. For each condition, independently generate 30,000 training, 10,000 calibration, and 30,000 test sessions. Train an L2 logistic-regression classifier on the eight raw signals. On calibration data, choose the ALLOW threshold for each model that maximizes coverage subject to <=1% empirical unsafe-ALLOW risk. Evaluate once on the disjoint test sample. The hand model retains its catastrophic threat/security-coverage gates.

The 1% target is an experimental constraint, not a recommended production risk tolerance. Calibration and test samples come from the same authored condition; this is not external validation.

## Results

| rho | overlap | model | calibrated threshold | test coverage | test unsafe risk | safe ALLOW recall |
|---:|---:|---|---:|---:|---:|---:|
| 0.0 | 0.00 | hand-weighted | 0.789 | 51.38% | 0.89% | 87.86% |
| 0.0 | 0.00 | logistic | 0.120 | 58.55% | 1.00% | 100.00% |
| 0.6 | 0.00 | hand-weighted | 0.826 | 51.69% | 1.10% | 87.64% |
| 0.6 | 0.00 | logistic | 0.254 | 58.92% | 1.01% | 100.00% |
| 0.6 | 0.25 | hand-weighted | 0.865 | 17.41% | 0.90% | 29.48% |
| 0.6 | 0.25 | logistic | 0.788 | 49.54% | 1.10% | 83.73% |
| 0.6 | 0.50 | hand-weighted | 0.910 | 4.24% | 1.02% | 7.27% |
| 0.6 | 0.50 | logistic | 0.956 | 7.06% | 0.76% | 12.16% |
| 0.6 | 0.75 | hand-weighted | 0.954 | 0.78% | 0.85% | 1.33% |
| 0.6 | 0.75 | logistic | 0.934 | 0.007% | 0.00% observed | 0.011% |

## Interpretation

The learned linear comparator substantially improves coverage at moderate overlap, especially at rho=0.6/overlap=0.25 (49.54% versus 17.41%), showing that the original fixed weights are not optimal for the authored synthetic distribution. At severe overlap, however, both approaches preserve low empirical unsafe risk only by withholding ordinary access from most sessions. The logistic model becomes particularly conservative at overlap=0.75.

The test risk can slightly exceed the 1% calibration constraint because threshold selection is finite-sample. This is expected and reinforces that a calibration-set constraint is not a guarantee.

These results narrow the contribution claim: the framework should not claim superior predictive discrimination from hand-selected weights. Its potentially defensible contribution is the explainable multidimensional decision structure, explicit hard gates/abstention, and a reproducible robustness-evaluation methodology. A learned score can be a stronger predictive baseline while still requiring calibration, uncertainty handling, and stress testing.

## Limitations

* Synthetic scenario labels and ranges encode the authors' assumptions.
* Training/calibration/test data share the same condition; no cross-condition transport test is performed here.
* Only one learned model family and one split per condition are reported.
* Zero observed unsafe events at extreme abstention is not proof of zero underlying risk.
* No enterprise telemetry or confidential employer data are used.

## Next step

Repeat across seeds and, more importantly, train/calibrate on the nominal condition and test on shifted overlap/dependence conditions. That prospective transport experiment is a harder test of whether learned calibration survives distribution shift.
