# Within-scenario signal-shift robustness

**Status:** synthetic stress test only; not real-world validation.  
**Population:** 50,000 sessions per condition; scenario prevalence frozen at the generator defaults.  
**Seed:** `20260916`.  
**Policies:** additive 0.75; identity/behavior-guarded 0.75; exploratory quorum q=0.70, 7/8.

This experiment complements the prior scenario-prevalence study. Instead of changing how often scenarios occur, it freezes labels and prevalence and applies pre-specified offsets to selected telemetry dimensions, clipping values to [0,1]. The perturbations model controlled adverse measurement/posture shifts; they are not estimates of production drift.

| Condition | Additive false ALLOW | Guarded false ALLOW | Quorum false ALLOW | Additive safe STEP_UP | Guarded safe STEP_UP | Quorum safe STEP_UP |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 12.87% | 1.42% | 0.00% | 5.19% | 5.19% | 6.40% |
| identity assurance -0.15 | 4.01% | 0.12% | 0.00% | 9.92% | 9.92% | 10.31% |
| anomaly risk +0.15 | 9.07% | 0.31% | 0.00% | 6.97% | 6.97% | 7.83% |
| posture erosion -0.10 | 0.56% | <0.01% | 0.00% | 12.76% | 12.76% | 13.02% |
| mixed adverse | 0.99% | <0.01% | 0.00% | 12.29% | 12.29% | 12.38% |

## Interpretation

The adverse shifts reduce unsafe ALLOW rates, but they do so by making the policies more conservative overall. The cost is visible in the safe-session verification burden: for example, uniform 0.10 erosion of compliance, endpoint health, and patch posture reduces additive false ALLOW from 12.87% to 0.56% while increasing safe STEP_UP from 5.19% to 12.76%. Thus, robustness cannot be summarized by false-ALLOW alone; security and friction must be reported jointly.

The identity/behavior guard retains a substantially lower false-ALLOW rate than the unguarded additive model in every tested perturbation. The quorum remains at 0% false ALLOW in these authored conditions, but this should not be interpreted as superiority: its favorable behavior remains strongly aligned with the synthetic scenario construction and it consistently incurs additional STEP_UP burden.

## Limitations

These are deterministic, researcher-chosen offsets applied to synthetic uniform ranges. They do not estimate real enterprise covariate drift, sensor calibration error, attacker adaptation, or concept shift. Labels are frozen even though sufficiently large real-world changes can alter the relationship between telemetry and access safety. The experiment therefore tests a narrow robustness property only. External telemetry remains necessary before effectiveness claims are warranted.
