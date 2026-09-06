# Threshold Selection and Sensitivity — Focused Literature Note

_Last reviewed: 2026-09-05_

## Why this note exists

The project initially used a fixed `ALLOW` threshold of `0.75`. A threshold sweep now
shows that aggregate error rates and verification friction change materially as the
threshold moves. Threshold selection therefore needs explicit methodological treatment
and cannot be presented as an arbitrary implementation constant.

## Bradatsch et al. — dynamic, risk-based enterprise thresholds

Bradatsch, Miroshkin, Trkulja, and Kargl presented *Zero Trust Score-based
Network-level Access Control in Enterprise Networks* at IEEE TrustCom 2023. The work
identifies 29 trust attributes, describes a dynamic risk-based method for determining
the trust threshold required for access, and evaluates a Subjective Logic-based trust
algorithm against a lightweight additive approach.

Publication metadata:
- 2023 IEEE 22nd International Conference on Trust, Security and Privacy in Computing
  and Communications (TrustCom)
- pp. 1422–1429
- DOI: `10.1109/TrustCom60117.2023.00194`

**Implication for this project:** a dynamic threshold is established prior art in the
enterprise Zero Trust domain. We should not claim novelty for merely replacing a
static threshold with a risk-dependent threshold. Instead, dynamic thresholding is an
important baseline or extension to compare against.

## Jeong and Yang — sensitivity analysis and large-scale evaluation

Jeong and Yang published *A Trust Score-Based Access Control Model for Zero Trust
Architecture: Design, Sensitivity Analysis, and Real-World Performance Evaluation* in
*Applied Sciences* in 2025. Their model uses four major factors—user behavior,
network environment, device status, and threat history—with 20 sub-metrics. The paper
performs weight sensitivity analysis and evaluates computational scalability using the
UNSW-NB15 dataset, including a one-million-record test.

Publication metadata:
- *Applied Sciences*, vol. 15, no. 17, article 9551, 2025
- Authors: Eunsu Jeong and Daeheon Yang
- DOI: `10.3390/app15179551`

**Implication for this project:** weighted trust scoring, sensitivity analysis, and
large-scale throughput evaluation are also established contributions. Our manuscript
must go beyond reproducing these elements.

## Research-positioning consequence

The threshold sweep in this repository is methodologically necessary, but it is not
itself a novel contribution. The more defensible research gap is the interaction
among:

1. enterprise endpoint-specific trust evidence;
2. intentionally missing or unavailable telemetry;
3. non-compensatory critical-signal constraints;
4. explicit abstention / `STEP_UP` decisions rather than forced allow/deny output;
5. adversarially compliant endpoints where nominal compliance remains high while
   identity or behavioral evidence becomes unsafe; and
6. validation using independently sourced enterprise telemetry rather than only
   simulation.

## Next literature questions

- How do risk-adaptive access-control systems calibrate thresholds without leaking
  labels or tuning on the evaluation set?
- Which security decision systems use selective prediction, abstention, or explicit
  uncertainty when evidence is incomplete?
- What methods quantify the operational cost of additional authentication or manual
  verification?
- How should non-compensatory constraints be justified statistically rather than set
  by intuition?

## References

- L. Bradatsch, O. Miroshkin, N. Trkulja, and F. Kargl, “Zero Trust Score-based
  Network-level Access Control in Enterprise Networks,” 2023 IEEE 22nd International
  Conference on Trust, Security and Privacy in Computing and Communications
  (TrustCom), pp. 1422–1429. DOI: `10.1109/TrustCom60117.2023.00194`.
- E. Jeong and D. Yang, “A Trust Score-Based Access Control Model for Zero Trust
  Architecture: Design, Sensitivity Analysis, and Real-World Performance Evaluation,”
  *Applied Sciences*, vol. 15, no. 17, 9551, 2025.
  DOI: `10.3390/app15179551`.
