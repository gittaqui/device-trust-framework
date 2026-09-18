# Correlated-Signal Dependence Stress Test

Date: 2026-09-17

## Purpose

The original synthetic generator samples telemetry dimensions independently within each scenario. This experiment tests whether the comparative policy conclusions survive when safety-oriented signals co-move. It is a **synthetic structural-sensitivity study**, not evidence of real-world endpoint performance.

## Method

A one-factor Gaussian copula induces dependence while preserving every scenario's existing marginal ranges, scenario prevalence, labels, policy weights, thresholds, and hard gates. For posture/identity signals, a high shared latent state produces higher values. For `threat_risk` and `anomaly_risk`, the quantile direction is reversed so their corresponding safety factors co-move positively with the other safety factors.

Tested latent Gaussian dependence parameters: `rho = 0.0, 0.3, 0.6, 0.8`. Each condition contains 50,000 synthetic sessions using seed `20260917`. Because marginal transformations are nonlinear, `rho` is a copula parameter rather than a claim about the observed Pearson correlation of every signal pair.

## Results

| rho | Additive false ALLOW | Guarded false ALLOW | Quorum false ALLOW | Additive safe STEP_UP | Guarded safe STEP_UP | Quorum safe STEP_UP |
|---:|---:|---:|---:|---:|---:|---:|
| 0.0 | 12.71% | 1.40% | 0.00% | 5.29% | 5.29% | 6.49% |
| 0.3 | 16.18% | 5.22% | 0.00% | 5.86% | 5.86% | 6.43% |
| 0.6 | 18.85% | 8.15% | 0.00% | 6.15% | 6.15% | 6.36% |
| 0.8 | 19.96% | 9.67% | 0.00% | 6.20% | 6.20% | 6.25% |

## Interpretation

Dependence materially changes the synthetic conclusions. As the shared safety factor strengthens, unsafe cases are more likely to receive several simultaneously favorable signals. The additive model's false-ALLOW rate rises from 12.71% at independence to 19.96% at `rho=0.8`. More importantly, the identity/behavior guard's false-ALLOW rate rises from 1.40% to 9.67%. Thus, the guard's advantage over ordinary additive scoring persists in this experiment, but its apparent protection is substantially weaker once signals are correlated.

The quorum comparator remains at 0% false ALLOW in these authored scenarios. This should **not** be interpreted as production superiority: the quorum rule is structurally aligned with the synthetic scenario design, and no external telemetry validates the result.

The principal research implication is that independent marginal sampling can make a multidimensional policy appear more robust than it is. Dependence among telemetry dimensions must therefore be treated as an explicit threat to synthetic-study validity rather than assuming that eight inputs provide eight independent pieces of evidence.

## Limitations

- The Gaussian one-factor copula is deliberately simple and imposes symmetric latent dependence; real endpoint telemetry may exhibit heterogeneous, nonlinear, or tail dependence.
- The experiment preserves the authored scenario marginals and labels, so it does not address concept shift or novel attacks.
- `rho` is not estimated from production data.
- Results are synthetic and must not be described as real-world security effectiveness.
- The experiment does not establish that the selected dependence levels are representative of Intune, Entra, EDR, or other enterprise telemetry.

## Reproducibility

Run:

```bash
python src/evaluate_signal_dependence.py
```

The implementation is deterministic for the recorded seed.
