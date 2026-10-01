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

## Day 5 — 2026-09-06 — Identity non-compensation diagnostic

Completed:
- Inspected the existing research log, trust model, generator, and bibliography before modifying the project.
- Used fresh literature research to verify that NIST SP 800-207 treats identity, requesting-system state, and behavioral attributes as distinct policy inputs rather than requiring one compensatory score.
- Verified Ameer et al., ACM Transactions on Privacy and Security 27(3), 2024, DOI `10.1145/3671147`, which combines contextual authorization policy with dynamic Zero Trust score/threshold evaluation. Added it to the bibliography to prevent an inflated novelty claim.
- Added `src/evaluate_identity_noncompensation.py` to compare the additive 0.75 model, a stricter additive 0.80 model, and an experimental targeted `STEP_UP` guard.
- Added a 21x21 identity-assurance/anomaly-risk policy-surface diagnostic while holding other endpoint evidence at the midpoint of the synthetic healthy ranges.
- Added `tests/test_identity_noncompensation.py`, including a regression case where `identity_assurance=0.20` and `anomaly_risk=0.90` are still `ALLOW` under the current additive 0.75 model when other endpoint signals are healthy.
- Recorded the complete synthetic interpretation and limitations in `results/identity-noncompensation-results.md` and `research/noncompensatory-policy-literature.md`.

Key synthetic findings:
- On the 50,000-row seeded population, false allows are 12.50% for additive 0.75, 0.34% for additive 0.80, and 1.24% for guarded 0.75.
- Safe STEP_UP is 5.40% for additive 0.75 and guarded 0.75, versus 13.58% for additive 0.80.
- The guarded policy eliminates `ALLOW` for the current synthetic `identity_risk` scenario while preserving the original treatment of benign `policy_drift`; additive 0.80 is stricter but pushes approximately 95.7% of `policy_drift` into STEP_UP.
- On the isolated 441-point identity/anomaly policy surface, additive 0.75 allows 94.56% of points, additive 0.80 allows 68.71%, and guarded 0.75 allows 47.17%.

Interpretation:
- Cross-domain compensation is a measurable property of the current additive model and can produce counterintuitive authorization decisions even when identity assurance is extremely weak.
- The particular identity guard thresholds are exploratory and must not be presented as optimal.
- The apparent absence of additional safe-user friction under the guard is structurally caused by the current generator: safe scenarios never enter the guard region. This prevents a fair estimate of false challenges and is now an explicit validity limitation.
- Score-plus-policy separation is not itself novel; prior ACM work already combines formal authorization policy with dynamic scores. The stronger contribution must be endpoint-specific empirical analysis, uncertainty/abstention behavior, missing telemetry, and independent validation.

Limitations:
- All labels and signal distributions remain synthetic.
- Guard thresholds are in-sample and uncalibrated.
- Safe identity uncertainty is underrepresented by design.
- No real MFA burden, user abandonment, or help-desk friction is measured.
- No external enterprise telemetry has yet been processed.

Next:
1. Stop tuning guard thresholds on the synthetic generator.
2. Run a bounded LANL authentication experiment to obtain independently sourced identity/behavior distributions.
3. Introduce a controlled benign-uncertainty lab experiment (e.g., legitimate authentication novelty or stale identity context) so guard-induced challenge burden can be measured rather than assumed.
4. Add a resource-sensitivity/dynamic-threshold baseline only after the external identity distribution is available.


## Day 6 — 2026-09-25 — Novelty boundary: score-based ZT access control

Completed:
- Re-inspected the repository before changing the research position.
- Verified NIST SP 800-207 (DOI `10.6028/NIST.SP.800-207`), which explicitly makes device state and other contextual inputs part of dynamic access decisions; this remains architectural guidance rather than evidence that one endpoint trust algorithm is optimal.
- Verified Junquera-Sánchez et al., *Security and Communication Networks* (2021), DOI `10.1155/2021/8146553`, a systematic review of continuous authentication. It reinforces that continuous confidence and multiple behavioral/data sources predate this project.
- Verified Alshomrani and Li, *Wireless Communications and Mobile Computing* (2022), DOI `10.1155/2022/6367579`, which evaluates static plus continuous device authentication for IoT using PUF/location evidence. This is device-authentication evidence, not enterprise endpoint-posture validation.
- Re-verified Ameer et al., *ACM Transactions on Privacy and Security* 27(3) (2024), DOI `10.1145/3671147`. Critically, that paper already proposes score-based Zero Trust authorization and explicitly leaves detailed score/threshold calculation algorithms for future work.
- Re-verified Jeong and Yang, *Applied Sciences* 15(17):9551 (2025), DOI `10.3390/app15179551`. Their model already combines behavior, network, device, and threat-history factors; includes ALLOW/MFA/BLOCK thresholds; performs factor-weight sensitivity analysis; and reports large-scale computational benchmarking using UNSW-NB15/CICIDS2017-derived experiments.

Research consequence:
- The manuscript must **not** claim novelty for multidimensional weighted trust scoring, three-way allow/challenge/block decisions, factor-weight sensitivity analysis, or scalability benchmarking by themselves.
- The strongest defensible contribution is now narrower: enterprise-managed endpoint decision robustness under **missing/stale evidence, cross-domain compensation, adversarially compliant states, abstention/STEP_UP behavior, and independent enterprise telemetry**, compared against both binary compliance and a published-style weighted trust-score baseline.
- The forthcoming LANL experiment is therefore a gating milestone. Synthetic improvements remain diagnostics and must not be described as evidence of production security effectiveness.

Limitations:
- Today’s work is literature/positioning work; no new empirical result was generated.
- LANL Windows authentication/logon telemetry cannot supply actual MDM compliance, patch, EDR coverage, or proprietary identity-risk scores. Any mapping must remain an explicit proxy, and genuinely unavailable dimensions must remain missing rather than imputed as healthy.
- IoT evidence is relevant to continuous/device trust concepts but is not direct evidence for enterprise-managed Windows endpoints.

Next:
1. Complete and checksum the bounded LANL WLS ingest already being prepared.
2. Freeze a preregistered external-validation protocol before examining labeled outcomes: fixed feature windows, temporal split, no future-event leakage, fixed baselines, and predefined primary metrics.
3. Compare binary compliance proxy, current explainable model, and a Jeong/Yang-style weighted score under identical evidence availability.
4. Report per-scenario/attack-family false-ALLOW, STEP_UP coverage, safe-user friction, confidence intervals, and missingness sensitivity.
5. Do not select an IEEE venue until external validation and the contribution boundary are stable.


## Day 7 — 2026-09-30 — Bounded LANL-2015 cohort preparation from Hugging Face

Completed:
- Inspected the current repository state and recent research commits before implementation.
- Re-verified the LANL Comprehensive Multi-Source Cyber-Security Events dataset description: 58 consecutive days, five aligned event sources, 1,648,275,307 total events, and a red-team file containing specific known malicious authentication events.
- Adopted the user-hosted Hugging Face mirror `Taqui/lanl-cyber-datasets` as the operational data source while retaining LANL as the authoritative provenance/citation source.
- Added `src/prepare_lanl2015_remote.py`. It inventories the mirror, downloads only the small `lanl-2015/redteam.txt` label file, validates its schema, records duplicate labels, and emits merged temporal windows plus implicated users/computers for bounded extraction.
- Added `tests/test_prepare_lanl2015_remote.py`.
- Locally ran the focused tests before committing: 4/4 passed. `py_compile` also passed.
- The code explicitly prevents a surrounding-window event from being relabeled as malicious merely because it is temporally close to a known red-team authentication.

Research consequence:
- The 444-GB extracted mirror does not need to fit in a local research sandbox. The next data pass can be driven by the cohort manifest and use remote/partitioned reads.
- Red-team events are limited ground truth for specific malicious authentication events. Surrounding authentication, process, DNS, or flow records are contextual evidence and must not be treated as attack labels without independent justification.
- The external experiment remains proxy validation on independently sourced enterprise telemetry; LANL does not contain actual MDM compliance, EDR health, patch posture, or proprietary identity-risk scores.

Limitations:
- This step prepares the cohort but does not yet report a model-performance result.
- The execution container could not resolve `github.com` or Hugging Face directly, so the live Hugging Face inventory/manifest generation could not be executed here. GitHub repository reads/writes were performed through the connected GitHub integration.
- Repository-wide tests were therefore not claimed; only the new focused module/tests were executed locally in isolation.
- Mirror upload is still in progress, so missing mirror files must be interpreted as upload state until the inventory confirms otherwise.

Next:
1. Run the cohort-preparation command where Hugging Face network access is available and commit the generated inventory/manifest metadata (not raw telemetry).
2. Use the resulting windows/entities to extract bounded authentication context first, preserving exact red-team labels.
3. Add matched benign temporal/entity controls without future-event leakage.
4. Derive transparent authentication novelty/failure/history proxy features and freeze the temporal split before evaluating outcomes.
5. Only then compare binary compliance proxy, published-style weighted trust, and the explainable framework under identical evidence availability.


## Day 8 — 2026-09-30 — Live bounded LANL-2015 external-context extraction

Completed:
- Added `src/extract_lanl_auth_remote.py`, which uses fail-closed HTTP byte-range reads plus timestamp-directed seeking so large time-sorted telemetry can be sampled without materializing the full file. Exact red-team tuples are the only authentication rows eligible for a red-team label.
- Added `src/extract_lanl_context_remote.py` for process, DNS, and flow context. These rows are explicitly emitted as `context_only=1`; temporal or entity proximity does not create an attack label.
- Added deterministic tests for range seeking, schema handling, exact-label semantics, context-only semantics, and bounded-window extraction. The focused LANL suite passed 10/10 in GitHub Actions.
- Added `.github/workflows/lanl-bounded-extract.yml` and executed it against the live Hugging Face mirror.
- Live mirror inventory contained 60 files total and 8 under `lanl-2015/`: process, DNS, flow, and red-team files in both plain-text and gzip form. `lanl-2015/auth.txt` was not yet present.
- Verified 749 red-team rows in the mirror. Selected the first 25 labels under a fixed ±600-second protocol, yielding eight merged temporal windows.
- Streamed the available remote telemetry via bounded byte ranges. Process extraction scanned 1,048,339 records and retained 4,561 focus-entity records; DNS scanned 10,602 and retained 129; flow scanned 1,452,153 and retained 9,333.
- Verified all retained process/DNS/flow rows remained `context_only=1`, fell inside the predefined temporal windows, and contained no exact duplicate output rows.
- Recorded the workflow summary in `results/lanl-2015-context-summary.json` and the descriptive analysis in `results/lanl-2015-context-coverage.md`.

Descriptive external-telemetry observations:
- The first 25 selected labels involved 5 unique users and 16 unique computers.
- Process context matched 25/25 selected labels; the median retained count was 38 rows per selected label, and the median nearest-event distance among covered labels was 2 seconds.
- Flow context matched 22/25 selected labels; the median retained count was 135 rows per selected label, and the median nearest-event distance among covered labels was 1.5 seconds.
- DNS context matched 3/25 selected labels; the overall median retained count was zero, while the median among covered labels was 5 rows and the median nearest-event distance was 11 seconds.
- These are descriptive observations about independently sourced enterprise telemetry. They are not classifier performance, causal evidence, or production security-effectiveness claims.

Limitations:
- The cohort is conditioned on the first 25 known red-team authentication events and implicated entities. It is not representative of the full 749-label set or ordinary enterprise traffic.
- Matched benign controls have not yet been constructed.
- Process, DNS, and flow records do not carry malicious ground truth in this experiment.
- `auth.txt` is still absent from the mirror, so the planned authentication-derived external baseline could not run.
- LANL does not provide actual MDM compliance, EDR health, patch posture, or proprietary identity-risk scores; this remains proxy evidence.
- No trust-model threshold or weight was tuned from these external outcomes.

Next:
1. Freeze and implement a matched benign-control protocol using only pre-outcome information and the same time-window geometry.
2. Derive transparent process/flow/DNS context features for red-team-centered and matched benign cohorts.
3. Keep model weights and thresholds frozen during external evaluation.
4. Add authentication-derived features only after `auth.txt` appears in the mirror.
5. Expand beyond the first 25 labels only after the control-selection and feature protocols are fixed, then report uncertainty and temporal-stratum results.


## Day 9 — 2026-09-30 — Frozen matched non-red-team control protocol

Completed:
- Inspected the existing external-validation freeze, live LANL-2015 context extraction, remote range readers, workflow, and prior research log before changing the study.
- Re-verified the authoritative LANL 2015 dataset semantics and DOI `10.17021/1179829`: red-team rows are specific known malicious authentication events; unlabeled surrounding telemetry is not independently established benign traffic.
- Froze `experiments/lanl-2015-matched-control-freeze.md` before comparative target/control feature analysis.
- Replaced the potentially misleading phrase "matched benign controls" with **matched non-red-team temporal controls**.
- Added `src/select_lanl2015_controls.py`, which deterministically tests fixed +/-1, 2, 3, and 7 day offsets, excludes windows overlapping any known red-team timestamp, prevents control/control overlap, and never consults process/DNS/flow outcomes.
- Added `tests/test_select_lanl2015_controls.py` covering deterministic first-choice behavior, red-team overlap exclusion, control/control separation, claim semantics, and fail-closed radius validation.
- Updated the bounded LANL workflow to generate and retain the frozen control manifest before subsequent extraction.

Research consequence:
- Comparative external analysis now has an auditable control-selection rule fixed before target/control feature differences are examined.
- A zero-event control is retained rather than replaced, preventing outcome-dependent sampling.
- Absence from `redteam.txt` is explicitly not treated as a benign label; therefore false-positive-rate claims remain prohibited at this stage.

Verification:
- GitHub writes completed successfully through the connected repository integration.
- The execution container could not resolve `github.com`, so an independent local clone/test run was not possible in this session.
- The workflow is configured to run the repository pytest suite on Python source/test changes and now generates the control manifest. No passing CI result is claimed here until GitHub reports one for the new commits.

Limitations:
- Time-shift matching approximately preserves time-of-day but does not guarantee equivalent weekday, workload, or entity activity.
- Controls remain unlabeled except for exclusion of known red-team timestamps.
- Authentication telemetry is still unavailable in the mirror according to the last completed live inventory; process/DNS/flow context alone cannot validate the full device-trust model.

Next:
1. Confirm CI for the frozen selector and inspect the generated control manifest.
2. Extract process/DNS/flow telemetry for the frozen control windows using the identical focus-entity filter.
3. Define context features without looking at target/control differences, then run paired descriptive comparisons with uncertainty reported by temporal stratum.
4. Add authentication-derived features only after `auth.txt` is present.


## Day 10 — 2026-09-30 — Paired LANL process/DNS/flow comparison

Completed:
- Confirmed the frozen matched non-red-team selector in GitHub Actions and generated 24 matched controls for the first 25 red-team targets; one target remained unmatched and was retained rather than replaced.
- Froze the first paired feature set in `experiments/lanl-2015-paired-feature-freeze.md` before computing target/control differences.
- Added `src/extract_lanl_paired_context_remote.py` and `tests/test_extract_lanl_paired_context_remote.py`.
- Changed the paired analysis to use each target's own user/source/destination-computer entity set instead of the union of all target entities.
- Ran the full repository suite in CI: 100 tests passed.
- Executed the live paired extraction against the Hugging Face LANL mirror and recorded `results/lanl-2015-paired-context-summary.json` plus `results/lanl-2015-paired-context-results.md`.
- Re-verified that `lanl-2015/auth.txt` is still absent from the mirror; authentication-derived external validation remains blocked.

Frozen paired descriptive findings:
- Process event count: target median 37.5 vs control 9.0; median paired difference +21.5; target higher in 21/24 matched pairs.
- Unique process count: 13.0 vs 4.5; median paired difference +7.0; target higher in 22/24 pairs.
- Process starts: 28.0 vs 7.5; median paired difference +16.5; target higher in 20/24 pairs.
- DNS remained sparse: median event count 0 on both sides; 22/24 pairs were tied on DNS event count.
- Flow event count: 179 vs 120; median paired difference +115.5; target higher in 17/24 pairs.
- Flow unique-port count: 176.5 vs 121.5; target higher in 17/24 pairs.
- Flow byte count: 105,462 vs 71,471; target higher in 17/24 pairs.

Exploratory temporal-stratum diagnostic:
- The process difference remained directionally positive across the populated offset strata.
- Flow differences were not stable across offsets. For the ten +1-day controls, median flow-event difference was only +8, while +2/+3-day strata were much larger and the two +7-day pairs were mixed.
- Because this stratum check was performed after the first paired results were observed, it is diagnostic only and cannot become a confirmatory claim on this cohort.

Fresh methodological context:
- A 2026 IEEE intrusion-detection dataset audit, DOI `10.1109/IMNS67862.2026.11655312`, identifies temporal concentration and node-identity leakage as mechanisms that can inflate evaluation results and recommends attack-aware chronological evaluation.
- A 2026 IEEE Access study, DOI `10.1109/ACCESS.2026.3688204`, shows that temporal NetFlow structure materially affects intrusion-detection behavior. This reinforces treating the offset-sensitive flow result cautiously.

Research consequence:
- Process activity is the strongest candidate external contextual signal from this first matched cohort.
- Flow-volume/diversity features remain secondary until tested under stricter temporal matching.
- DNS is not useful in this first pair-specific cohort.
- No trust-model threshold, weight, or classifier was tuned from these 24 pairs.

Limitations:
- Controls are unlabeled non-red-team times, not verified benign sessions.
- The first 25 labels form a small, early red-team cohort and are not representative of all 749 labels.
- Matching preserves approximate time-of-day but often changes day-of-week and workload context.
- The paired scan is currently range-seek heavy and should be optimized before scaling to hundreds of labels.
- No sensitivity, specificity, false-positive rate, AUC, causal effect, or production-effectiveness claim is supported.
- LANL process/DNS/flow data do not represent MDM compliance, patch posture, EDR health, or proprietary identity-risk ground truth.

Next:
1. Freeze an untouched second cohort (labels 26-50) before inspecting its telemetry.
2. Use same-weekday/time-of-day controls based on fixed 7-day multiples so the first-cohort workload/offset concern is directly tested.
3. Reuse the exact same 13 frozen features; make process activity the primary confirmation target and flow features secondary.
4. Optimize paired range extraction before scaling beyond the second cohort.
5. Add authentication-derived features only after `auth.txt` appears in the mirror.
