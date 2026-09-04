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
