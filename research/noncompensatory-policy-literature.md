# Non-Compensatory Policy Constraints — Literature Context

_Last reviewed: 2026-09-06_

## Why this experiment is necessary

The current device-trust baseline uses a weighted sum. Weighted sums are intentionally compensatory: a low value in one factor can be offset by high values in others. That property is mathematically simple and explainable, but it is not automatically appropriate for authorization.

NIST SP 800-207 treats user identity, requesting-system state, and behavioral attributes as separate policy inputs and states that access policy can depend on resource sensitivity and acceptable risk. This supports testing whether certain evidence should be handled as explicit policy constraints rather than merely another weighted contribution.

NIST reference:
- S. Rose, O. Borchert, S. Mitchell, and S. Connelly, *Zero Trust Architecture*, NIST SP 800-207, 2020. DOI: `10.6028/NIST.SP.800-207`.

## Relevant score-plus-policy precedent

Ameer et al. develop a formally defined Zero Trust score-based authorization framework for IoT in ACM Transactions on Privacy and Security. Their architecture combines a contextual authorization policy model with dynamically calculated score/threshold values and ongoing authorization.

Verified publication metadata:
- Safwa Ameer, Lopamudra Praharaj, Ravi Sandhu, Smriti Bhatt, and Maanak Gupta.
- “ZTA-IoT: A Novel Architecture for Zero-Trust in IoT Systems and an Ensuing Usage Control Model.”
- *ACM Transactions on Privacy and Security*, vol. 27, no. 3, 2024.
- DOI: `10.1145/3671147`.

## Consequence for novelty

The project must **not** claim that combining a trust score with explicit policy constraints is itself novel. Prior work already separates contextual policy from dynamic scores in Zero Trust authorization.

The narrower research opportunity is empirical and endpoint-specific:

1. quantify compensation failure modes in enterprise endpoint trust scoring;
2. distinguish globally stricter thresholds from domain-specific non-compensatory constraints;
3. use `STEP_UP` as an explicit abstention outcome rather than silently granting or denying under uncertain evidence;
4. evaluate the resulting security/friction trade-off under missing telemetry and independently sourced enterprise authentication behavior;
5. preserve explainable factor-level reasons for each policy intervention.

## Current evidence status

The 2026-09-06 identity non-compensation experiment is a **synthetic mechanism study**. It demonstrates that the current additive formula can authorize very weak identity evidence when other endpoint signals are strong. It does not establish that the proposed identity guard is correctly calibrated for real enterprise populations.

External validation remains required before publication-grade effectiveness claims.
