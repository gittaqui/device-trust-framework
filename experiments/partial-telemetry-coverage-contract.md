# Partial-telemetry coverage contract (2026-10-28)

**Scope:** Research-only missing-telemetry evaluation. This contract does not specify a deployable access-control policy.

## Two distinct meanings of coverage

1. **Observed-weight telemetry coverage** for a single decision is
   \(C_{\mathrm{telemetry}}(x)=\sum_{j\in O(x)}w_j\), where \(O(x)\) is the set of observed factors and the eight default nonnegative weights sum to one. Missing values contribute zero *to coverage*, not to the policy score under every strategy. This is a measurement of available weighted evidence, **not** a calibrated confidence, trust probability, or claim that a decision is correct.
2. **Ordinary-ALLOW coverage** over an evaluation set is \(C_{\mathrm{allow}}=\#\mathrm{ALLOW}/N\). It measures the fraction of sessions granted ordinary access. It is distinct from telemetry coverage, selective-classification coverage, and security effectiveness.

## Invariant and hard-gate precedence

For every partial input and every missingness policy, the third value returned by `decide_partial` must equal the sum of the default weights for the observed signals. This invariant applies even when an observed critical threat or critical security-coverage signal triggers an immediate DENY. Hard-gate precedence and the resulting score/decision remain unchanged.

Example: if `threat_risk=0.95` is the **only** observed signal, the hard gate returns `(score=0, decision=DENY, observed_weight_coverage=0.08)`, **not** coverage `1.0`. With only `security_coverage=0.10`, the corresponding coverage is `0.16`. Both observed signals yield `0.24`. All eight observed signals yield `1.0` even if a hard gate denies access. With no signals, the model returns `STEP_UP` and coverage `0.0`.

A gate can be decisive with sparse evidence; decisiveness does not imply full observability. Reporting `1.0` on a partial gate-triggered decision masks telemetry gaps and could invalidate analyses that stratify decisions by evidence completeness. This correction does **not** change any previously published frozen policy-decision counts because those experiments did not use the coverage return value for decision-making.

## Verification boundary

The accompanying exhaustive regression checks all 256 observation masks for each of two critical-gate fixtures across all five implemented policies. A separate seeded local differential audit compared 50,000 strategy decisions against the exact pre-fix implementation, finding **zero score/decision differences** and **7,855 corrected coverage reports**. These are deterministic synthetic/software checks, not measurements of real endpoint outcomes. Existing frozen paired-mask JSON and manuscript policy rates are unchanged.

## External methodological context

NIST SP 800-207 (Rose et al., 2020; DOI `10.6028/NIST.SP.800-207`) describes dynamic access decisions informed by policy and supporting information sources. This supports explicitly recording evidence availability, but does not prescribe this eight-factor score or its weights. Franc, Prusa, and Voracek, *Optimal Strategies for Reject Option Classifiers*, *JMLR* 24(11), 2023 (journal page: https://www.jmlr.org/papers/v24/21-0048.html; no DOI shown) distinguish selective coverage and risk. Their theory does **not** equate telemetry completeness with classification coverage or validate this device-trust policy.

## Next validation

Record observed-weight coverage, hard-gate reason, and independent adjudication provenance in the authorized non-production endpoint evaluation; stratify per-scenario errors by coverage. Do not treat missing critical telemetry as benign, and do not extrapolate synthetic results to enterprise effectiveness.
