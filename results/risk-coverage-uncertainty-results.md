# Risk–coverage uncertainty results

Date: 2026-09-19  
Population: 50,000 **synthetic** endpoint sessions  
Generator seed: `20260903`  
Intervals: two-sided 95% Wilson score intervals

These intervals quantify finite-sample uncertainty under the authored synthetic generator. They are **not** confidence intervals for production security performance and do not address model misspecification, dataset shift, or external validity.

| ALLOW threshold | ALLOW n | Unsafe ALLOW n | Unsafe risk | 95% Wilson CI | Safe-session ALLOW recall | 95% Wilson CI |
|---:|---:|---:|---:|---:|---:|---:|
| 0.60 | 40,146 | 11,113 | 27.681% | 27.246–28.121% | 100.000% | 99.987–100.000% |
| 0.65 | 39,793 | 10,760 | 27.040% | 26.606–27.479% | 100.000% | 99.987–100.000% |
| 0.70 | 36,839 | 7,824 | 21.238% | 20.824–21.659% | 99.938% | 99.902–99.961% |
| 0.75 | 30,086 | 2,621 | 8.712% | 8.398–9.036% | 94.599% | 94.333–94.853% |
| 0.80 | 25,162 | 72 | 0.286% | 0.227–0.360% | 86.419% | 86.020–86.808% |
| 0.85 | 24,913 | 0 | 0.000% | 0.000–0.015% | 85.809% | 85.403–86.206% |
| 0.90 | 23,201 | 0 | 0.000% | 0.000–0.017% | 79.913% | 79.448–80.369% |
| 0.95 | 1,600 | 0 | 0.000% | 0.000–0.240% | 5.511% | 5.254–5.779% |

## Interpretation

The earlier point-estimate result at threshold 0.85 observed zero unsafe ALLOW decisions. The uncertainty analysis shows why that must not be written as evidence of zero risk: with 24,913 synthetic ALLOW decisions and no observed unsafe events, the two-sided 95% Wilson interval still permits an unsafe-ALLOW probability up to approximately 0.015% **under this generator**.

The distinction becomes even clearer at threshold 0.95. Zero unsafe events among only 1,600 ALLOW decisions corresponds to an upper bound of roughly 0.240%, much wider than at 0.85. A zero count therefore becomes less informative as ordinary-access coverage collapses.

At threshold 0.80, the estimated unsafe risk is 0.286% (95% Wilson CI 0.227–0.360%) while safe-session ALLOW recall is 86.419% (86.020–86.808%). At 0.75, estimated unsafe risk is 8.712% (8.398–9.036%) with 94.599% (94.333–94.853%) safe-session ALLOW recall. The sharp 0.75→0.80 transition remains large relative to finite-sample interval widths in this synthetic draw.

## Statistical limitation

The 50,000 rows are generated from fixed authored scenario distributions. Wilson intervals address binomial sampling uncertainty conditional on that data-generating process; they do not quantify uncertainty about whether the generator resembles real enterprise endpoint populations. External telemetry validation remains necessary.
