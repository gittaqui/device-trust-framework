# Independent full-model validation protocol (design freeze candidate)
Date authored: 2026-10-08. Status: **protocol draft; no full-model external experiment has been run.**

## Motivation and evidence boundary
The weighted model in `src/trust_model.py` consumes eight inputs:
`compliance`, `endpoint_health`, `identity_assurance`,
`patch_posture`, `security_coverage`, `freshness`,
`threat_risk`, and `anomaly_risk`.
LA​NL-2015 provides real de-identified enterprise authentication/process/DNS/flow
events and red-team authentication labels, but not native endpoint MDM policy,
patch, EDR-control or endpoint-health measurements. It cannot provide an
independent eight-input ground-truth test set by itself.

## Evidence availability and experimental provenance

| Model input | LANL-2015 support | Required independently observed lab measurement | Invalid shortcut |
|---|---|---|---|
| compliance | None | Exported policy-state verdict plus timestamp from consenting test-device management | Assume non-red-team = compliant |
| endpoint_health | None | Direct system health diagnostics and service state recorded before policy outcome | Set healthy for all records |
| identity_assurance | Partial authentication context only; no MFA assurance | Dedicated test-IdP authentication assurance/verification records | Label every login strong |
| patch_posture | None | OS/build/KB inventory compared to a predeclared patch policy | Derive patch status from process counts |
| security_coverage | None | Defender or lab security-agent enabled/running/tamper status, captured independently | Treat missing EDR as enabled |
| freshness | Timestamps available; no native MDM check-in freshness | Logged recency since prior authenticated attestation | Use nearest red-team event distance as device freshness |
| threat_risk | Explicit red-team authentication labels only, no endpoint risk score | Independent incident/adversary exercise observation with published injection timeline | Rename red-team label as threat-risk input (label leakage) |
| anomaly_risk | Process/flow can support descriptive novelty proxies, not calibrated risk | Prespecified training-only anomaly estimator, temporal train/test separation | Train anomaly threshold on held-out attack episodes |

Missing evidence is represented as unavailable and sent to the predeclared
missing-evidence policy (`STEP_UP`/abstention); it is not filled as healthy.

## Proposed independent evaluation: isolated, authorized endpoint lab
All endpoints and accounts must be owned/consented, with no employer logs
or corporate tenant access. Use dedicated test Windows VMs, a lab MDM/IdP
(or direct locally captured posture evidence where management infrastructure
is unavailable), a defensive telemetry collector, and independently
timestamped operator-manipulated conditions.

**Preregister before running**: endpoint count and diversity, randomized
episode order, event/observation windows, reference enforcement policy,
weight/threshold settings, primary endpoint-outcome labels, de-duplication
unit, and exclusion criteria. Identity/session events should be grouped by
device and exercise day to avoid near-duplicate train/test leakage.

A minimally informative challenge set includes legitimate healthy activity,
benign delayed check-in, benign policy drift, identity verification uncertainty,
compliant endpoint with independently observed security-agent failure,
missing/unknown patches, expired telemetry, and explicit threat-control
failure. Record each state from observable service/policy/patch facts rather
than model features derived from its ground-truth label. Exercise labels
must be independently adjudicated against an **a priori** lab access policy,
not assigned by the weighted model being evaluated.

## Fixed comparator suite on common evidence
- **B0**: binary *observed* device-compliance verdict only. If the verdict
  is unavailable, B0 must abstain; do not manufacture a compliance proxy.
- **B1**: frozen additive multidimensional trust score from
  `src/trust_model.py`, fixed weights and decision thresholds.
- **B2**: additive score with critical-threat/security-coverage hard gates
  (if separating policy ablations) on the identical observation set.
- **B3**: a predefined conservative missing-evidence `STEP_UP` policy,
  with explicit minimum observed-weight coverage.
- **B4**: attribute-quorum rule using thresholds fixed *before* lab testing.

Do not evaluate B0–B4 under different available inputs and claim a fair
head-to-head superiority result. Report *coverage* (fraction of sessions
scorable under each policy) alongside all decisions.

## Outcomes, analysis and stopping rule
Predeclare: (a) ordinary-access ALLOW among independently adjudicated unsafe
episodes, (b) STEP_UP among safe episodes, (c) DENY among safe episodes,
(d) abstention rate from missing evidence, (e) per-category outcomes, and
(f) end-to-end time including collection, normalization, joins and
enforcement (distinct from CPU-only microbenchmarks). Publish denominators
and Wilson confidence intervals for descriptive proportions; use paired
comparisons where the same episode is passed to each model. When episodes
are correlated within device/day, a device/day-level cluster bootstrap
or similarly justified grouped inference is required; IID binomial
intervals alone understate uncertainty. Avoid asymptotic tests on tiny
clusters.

No threshold selection or model-fitting on the final held-out lab episodes.
Report failures and inconclusive findings. No cherry-picked subset of
episodes counts as a successful independent validation. Check whether the
a priori evaluation policy labels actually measure access suitability
rather than simply echoing the source compliance policy.

## Two-day feasibility gate
This protocol and the existing synthetic/partial LANL studies can be made
reproducible rapidly, but **full-model external effectiveness cannot be
validated in two days unless an authorized instrumented endpoint lab,
independent labels and adequate held-out sample already exist**.
If unavailable, report it as an unmet publication criterion rather than
simulating endpoint posture in LANL data.

## Verified primary sources
- Alexander D. Kent, *Comprehensive, Multi-Source Cyber-Security Events*,
  Los Alamos National Laboratory (2015), DOI 10.17021/1179829:
  https://csr.lanl.gov/data/cyber1/
- Scott Rose, Oliver Borchert, Stuart Mitchell, Sean Connelly,
  *Zero Trust Architecture*, NIST SP 800-207 (2020),
  DOI 10.6028/NIST.SP.800-207:
  https://csrc.nist.gov/pubs/sp/800/207/final
