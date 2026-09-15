# Leave-one-signal-out ablation

Date: 2026-09-14

## Scope

This is a **synthetic sensitivity experiment**, not real-world evidence and not a causal feature-importance analysis. It uses the existing 50,000-row seeded synthetic population (`seed=20260903`), the additive 0.75 ALLOW threshold, and the 0.55 STEP_UP threshold. For each ablation, one weighted factor is removed and the remaining weights are renormalized to sum to one. Existing hard gates remain active.

## Results

| Removed factor | Unsafe false ALLOW | Delta vs full | Safe STEP_UP | Delta vs full |
|---|---:|---:|---:|---:|
| None (full model) | 12.50% | — | 5.40% | — |
| compliance | 1.98% | -10.52 pp | 0.00% | -5.40 pp |
| endpoint_health | 8.25% | -4.25 pp | 8.80% | +3.40 pp |
| identity_assurance | 25.33% | +12.82 pp | 11.04% | +5.64 pp |
| patch_posture | 9.18% | -3.32 pp | 5.92% | +0.52 pp |
| security_coverage | 2.34% | -10.16 pp | 11.04% | +5.64 pp |
| freshness | 15.10% | +2.60 pp | 7.90% | +2.50 pp |
| threat_safety | 16.91% | +4.41 pp | 8.30% | +2.90 pp |
| anomaly_safety | 23.71% | +11.21 pp | 7.57% | +2.17 pp |

## Interpretation

Within the current generator, removing `identity_assurance` or `anomaly_safety` produces the largest increases in unsafe ordinary access, followed by `threat_safety` and `freshness`. This is consistent with the generator's identity-risk and adversarially-compliant scenarios, but must not be interpreted as a real-world ranking of signal importance.

The counterintuitive result for `compliance` is especially informative: removing it *reduces* synthetic false ALLOW and safe STEP_UP. Because the remaining weights are renormalized, mass moves from compliance toward the other factors. In this generator, several unsafe scenarios deliberately retain high compliance while the safe `policy_drift` scenario has low compliance. The ablation therefore exposes an intentional construct choice: binary compliance is partly anti-informative for the specific controlled failure modes used to test the paper's hypothesis.

Similarly, removing `security_coverage` from the weighted sum does not remove the separate critical-security-coverage hard gate. Its ablation result therefore measures the incremental value of its weighted contribution **conditional on retaining the gate**, not the total importance of security coverage.

## Limitation

Ablation effects are conditional on scenario prevalence, feature ranges, labels, fixed thresholds, weight renormalization, and retained hard gates. They are useful for diagnosing model/generator behavior and identifying where conclusions depend on particular dimensions. They do not establish causality, production importance, or external generalization. External temporally held-out telemetry remains required.
