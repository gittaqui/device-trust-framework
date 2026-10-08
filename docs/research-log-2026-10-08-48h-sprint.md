# Research sprint log — 2026-10-08 (Pacific)

## Working manuscript
**Beyond Binary Compliance: An Explainable Multidimensional Device Trust Framework for Enterprise Access Decisions**

## Work completed in this session
- Inspected live repository content: LANL paired extractor, second-cohort freeze, control selector, tests, first-cohort summary, paper and Actions workflow.
- Verified LANL dataset provenance against Los Alamos National Laboratory's authoritative documentation: Alexander D. Kent, *Comprehensive, Multi-Source Cyber-Security Events* (2015), DOI `10.17021/1179829`, https://csr.lanl.gov/data/cyber1/.
- Verified NIST SP 800-207, *Zero Trust Architecture* (2020), DOI `10.6028/NIST.SP.800-207`, https://csrc.nist.gov/pubs/sp/800/207/final. NIST describes subject/device attributes as access-policy inputs; this is not evidence that any particular weighted trust policy is optimal.
- Created five public GitHub issues (#1–#5) defining the 48-hour data, validation, statistics, manuscript and QA deliverables. These are owner-role work tickets, **not** active, separately connected agents.
- Added `src/run_lanl2015_replication.py`: fail-closed target selection of original rows 26–50, consistent full-label red-team exclusions, manifest preflight, 13 frozen features, complete label SHA-256 provenance.
- Added `tests/test_run_lanl2015_replication.py`: synthetic-fixture-only unit tests for 25:50 indexing, offsets, too-short label files, preflight gating, feature-schema and provenance checks.
- Added `src/analyze_lanl2015_replication.py`: exact two-sided sign tests, Wilson 95% intervals, target/control medians, within-pair differences, ties, and explicit caveats on correlated primary process features.
- Added `tests/test_analyze_lanl2015_replication.py`: deterministic unit tests for sign-test tails, Wilson bounds, ties, 25-label CSV invariant and malformed input failure.
- Added `.github/workflows/lanl-second-cohort-replication.yml` to execute full repository tests before processing frozen second-cohort telemetry, and upload reproducibility artifacts even on failure.
- Added verified LANL dataset BibTeX reference to `paper/references.bib`, updated `paper/main.tex` to report existing first-cohort descriptive data and the preregistered second cohort without inventing outcomes.

## Results currently verified
- **Code commits succeeded**; the latest paper update was `9475ce0e074c2415ed98dd1b0d602ecd46951556`.
- GitHub Actions frozen second-cohort run: https://github.com/gittaqui/device-trust-framework/actions/runs/37830049114 — **in progress at last check**. No second-cohort outcome, p-value or successful test claim is made before artifacts become available.
- Prior first-cohort repository summary reports 24 matched of 25 targets, process-event medians 37.5 target vs 9.0 control, median paired difference 21.5, 21/24 target higher; unique-process medians 13.0 vs 4.5, paired median difference 7.0, 22/24 target higher. These are descriptive matched-context counts, **not classifier accuracy**.

## Limitations / critical publication gaps
- The LA​NL red-team file labels specific authentication events. Controls are non-red-team *unlabeled times*, not verified benign sessions. No ROC/AUC, sensitivity, specificity or false-positive rate can be computed from this comparator without valid labels.
- LANL lacks actual MDM compliance, patch posture, EDR presence and proprietary device-risk measures. **The full multidimensional device-trust model is not externally validated by this study.**
- Model optimization on a synthetic generator can overfit its engineered scenario geometry. Synthetic p-values/intervals do not measure enterprise deployment uncertainty.
- Second-cohort temporal controls preserve weekday but may differ in workload, host activity and data coverage; all failures or null outcomes must be retained.
- The GitHub Action and existing end-to-end pipeline must finish before asserting CI success or publication readiness.
- No employer-confidential telemetry used.

## Workstream tickets, target 2026-10-10
1. https://github.com/gittaqui/device-trust-framework/issues/1 — replication and artifacts.
2. https://github.com/gittaqui/device-trust-framework/issues/2 — defendable model/baseline validation.
3. https://github.com/gittaqui/device-trust-framework/issues/3 — preregistered statistics.
4. https://github.com/gittaqui/device-trust-framework/issues/4 — manuscript and references.
5. https://github.com/gittaqui/device-trust-framework/issues/5 — CI and reproducibility.

## Next step
Read the GitHub workflow's exact completed steps and artifacts, correct any test or execution failures, and analyze the *pre-frozen* second cohort regardless of the direction or statistical significance of results. Separately state whether a controlled endpoint lab with independently observed posture and verified enforcement outcomes is available. Do not declare IEEE-journal readiness until full-model validation and reproducibility exist.
