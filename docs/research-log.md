# Research Log

## Day 1 — 2026-09-03

Completed:
- Defined primary research question and three subquestions.
- Established a cautious, non-inflated research gap.
- Reviewed foundational NIST guidance and selected IEEE/ACM literature.
- Designed the first synthetic experiment and evaluation metrics.
- Implemented an explainable trust model with non-compensatory safety gates.
- Implemented reproducible synthetic scenario generation.
- Implemented baseline comparison and unit tests.
- Created an IEEEtran manuscript shell and initial bibliography.

Next:
1. Expand literature matrix to 30+ peer-reviewed papers.
2. Run weight and threshold sensitivity analysis.
3. Add missing-telemetry experiments.
4. Add per-scenario confusion analysis.
5. Identify the best-fit IEEE venue after the contribution becomes clearer.

## Day 2 — 2026-09-04

Completed:
- Verified that IEEE 3409-2026 is now an active Zero Trust Security standard and adjusted the research positioning accordingly: the novelty claim must be empirical and endpoint-specific, not simply "device-aware Zero Trust."
- Identified LANL enterprise Windows telemetry as the highest-value public external validation source.
- Added `experiments/external-telemetry-validation-plan.md` describing a hybrid real-enterprise, controlled-lab, and synthetic validation architecture.
- Defined careful mappings from LANL authentication/process behavior to abstract trust dimensions while explicitly avoiding false equivalence with Intune, Entra, or Defender scores.
- Added a streaming `src/lanl_auth_adapter.py` suitable for very large LANL authentication streams.
- Added unit tests for parsing, user-host novelty, and failure-history effects.
- Confirmed IEEE Transactions on Network and Service Management as a plausible eventual venue because it welcomes management frameworks, reliability/policy work, applications/case studies, emerging technologies, performance evaluation, and scalability analysis. Regular submissions are currently open continuously.

Limitations:
- No LANL raw dataset has yet been downloaded or processed in this repository.
- The new LANL features are transparent research proxies, not validated identity or endpoint-risk scores.
- External telemetry does not contain actual Intune compliance, patch posture, or security-coverage fields; those dimensions require a controlled endpoint lab or an explicitly missing-data strategy.
- Publication-grade claims require sensitivity analysis, stronger baselines, per-scenario evaluation, and independent validation.

Next:
1. Obtain an official LANL dataset subset and record source/checksum metadata.
2. Run the adapter on a bounded sample before scaling to the full corpus.
3. Join red-team labels to authentication-derived features without leakage.
4. Implement explicit missing-signal confidence penalties.
5. Expand the literature review around dynamic trust scoring published in 2025-2026 and differentiate the proposed contribution from recent context-aware device-trust models.

## Day 3 — 2026-09-04 — Missing-telemetry robustness

Completed:
- Reviewed current repository state before modifying the experiment design.
- Verified two additional peer-reviewed references relevant to runtime/continuous trust: Dimitrakos et al., IEEE TrustCom 2020, DOI `10.1109/TRUSTCOM50675.2020.00247`, and Jha et al., IEEE Transactions on Cloud Computing, vol. 13(1), pp. 61–74, DOI `10.1109/TCC.2024.3503358`.
- Added `src/evaluate_missing_telemetry.py`, a deterministic synthetic experiment comparing five explicit missing-evidence policies: renormalization, neutral imputation, pessimistic imputation, confidence penalty, and policy abstention via `STEP_UP`.
- Added MCAR and critical-signal-biased structured outage models at 10%, 25%, and 40% nominal missingness.
- Added unit tests covering missing critical signals, low observed-weight coverage, hard-gate preservation, and conservative score ordering.
- Recorded full reproducible results in `results/missing-telemetry-results.md`.
- Expanded the literature review, matrix, and BibTeX database around continuous authorization, runtime state verification, missing evidence, and scalability.

Key synthetic findings:
- Renormalizing only the observed factors increased false allows as telemetry disappeared: under structured missingness, false allows rose from 15.40% at 10% nominal missingness to 26.47% at 40%.
- Pessimistic/confidence penalties sharply reduced false allows but created severe false-denial/friction costs at high missingness; at structured 40% missingness, false-denial rates exceeded 61%.
- Explicit `STEP_UP` behaved as a useful abstention mechanism in this synthetic design: structured false allows fell to 0.90% at 40% nominal missingness with zero synthetic false denials, but 96.41% of safe sessions required step-up.

Interpretation:
- Missing telemetry must not be silently treated as benign evidence.
- The current results do not establish an optimal strategy because both the population and missingness distributions are synthetic.
- The high step-up rate demonstrates a security/usability trade-off that must be calibrated against external telemetry rather than optimized on the current generator.

Limitations:
- Missingness models are hypothetical and not estimated from production telemetry.
- `STEP_UP` is modeled as an abstention/verification outcome, not as a measured MFA or access-control user experience.
- The same synthetic scenario generator supplies the underlying safe/unsafe labels, so results are methodological rather than evidence of production effectiveness.
- No external LANL telemetry has yet been processed.

Next:
1. Validate the missing-evidence policy on a bounded LANL authentication sample where several endpoint dimensions are genuinely unavailable.
2. Add threshold and minimum-coverage sensitivity analysis to determine whether the step-up trade-off is stable.
3. Add per-scenario error analysis, especially for adversarially compliant and identity-risk cases.
4. Expand the literature search around abstention/selective prediction and risk-aware access decisions without overstating domain equivalence.

## Day 4 — 2026-09-05 — Threshold sensitivity and per-scenario errors

Completed:
- Inspected the current model, generator, missing-telemetry experiment, literature review, bibliography, and research log before adding new work.
- Added `src/evaluate_threshold_sensitivity.py` to sweep the `ALLOW` threshold from 0.60 through 0.90 and emit aggregate plus per-scenario decision metrics.
- Added `tests/test_threshold_sensitivity.py` covering monotonic false-allow behavior under a higher allow threshold and per-scenario decision-rate accounting.
- Reproduced the 50,000-row seeded synthetic threshold sweep and recorded the results in `results/threshold-sensitivity-results.md`.
- Added `research/threshold-selection-literature.md` to distinguish methodological necessity from research novelty.
- Verified and added two directly relevant references: Bradatsch et al., IEEE TrustCom 2023, DOI `10.1109/TrustCom60117.2023.00194`, and Jeong & Yang, Applied Sciences 2025, DOI `10.3390/app15179551`.
- Updated the manuscript BibTeX database with the verified publication metadata.

Key synthetic findings:
- The model is strongly threshold-sensitive. At `ALLOW >= 0.75`, the false-allow rate is 12.50%; at 0.80 it falls to 0.34%; at 0.83 it reaches 0% on this synthetic population.
- The security gain has an operational cost. Safe `STEP_UP` rises from 5.40% at threshold 0.75 to 13.58% at 0.80 and approximately 14.18% at 0.83.
- Aggregate metrics conceal a concentrated weakness: at threshold 0.75, 58.3% of the synthetic `identity_risk` scenario is still allowed, while 7.4% of `adversarial_compliant` and 2.8% of `stale` scenarios are allowed.
- At threshold 0.80, `identity_risk` false allows fall to 1.8% and the other listed unsafe scenario families fall to 0%, but 95.7% of benign `policy_drift` cases require `STEP_UP`.
- The current malware and missing-protection scenarios remain denied because of existing non-compensatory safety gates.

Interpretation:
- The original 0.75 threshold cannot be defended as a universal operating point from the current evidence.
- Choosing 0.83 because it eliminates false allows on the same synthetic generator would be in-sample tuning, not external validation.
- Identity risk exposes a compensation problem in the additive model: favorable endpoint signals can offset weak identity assurance and high anomaly risk. This is a stronger design question than simply tuning the global threshold.
- Prior research already covers dynamic risk-based thresholds, weighted trust-score sensitivity, and large-scale throughput evaluation. Threshold sensitivity is therefore necessary methodology, not the manuscript's novelty claim.

Limitations:
- The population, scenario labels, and signal distributions are synthetic and project-designed.
- The experiment varies the allow threshold while keeping the step-up threshold and weights fixed.
- `STEP_UP` cost is represented as a rate, not measured user or administrator burden.
- Unit tests were added to the repository; external CI execution should be added so every research commit is independently reproducible from GitHub.
- No external enterprise telemetry has yet been used to calibrate or test a threshold.

Next:
1. Add a dynamic/risk-dependent threshold baseline based on clearly specified resource sensitivity, without claiming the concept as novel.
2. Test a non-compensatory identity-risk constraint separately from global threshold changes and quantify its security/friction trade-off.
3. Add joint weight-and-threshold sensitivity rather than one-dimensional tuning.
4. Prioritize a bounded LANL experiment so threshold behavior can be evaluated on independently sourced enterprise telemetry.
