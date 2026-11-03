# Temporal telemetry-outage experiment protocol — 2026-11-02

## Research objective
Extend the November 1 correlated-missingness study to *persistent* outages without changing the eight-factor trust model. This is a **preregistered protocol**, not a completed experiment. No results are claimed.

## Hypothesis
H1: Holding marginal missingness constant, increasing within-device temporal persistence increases the duration of intervals with insufficient evidence, and may alter unsafe-ALLOW and safe-friction rates. This is a directional hypothesis for outage duration, **not** a guaranteed monotonic prediction for unsafe-ALLOW.

## Generative mechanism
For each device and selected telemetry group, let M[t] = 1 indicate unavailable telemetry. Generate a stationary two-state Markov chain with marginal missing probability p and lag-one autocorrelation rho:

P(M[t]=1 | M[t-1]=0) = p(1-rho)
P(M[t]=1 | M[t-1]=1) = p + rho(1-p).

Initialize M[0] ~ Bernoulli(p). These transitions preserve stationary P(M[t]=1)=p and autocorrelation rho for 0<=rho<1. Expected missing-run duration is 1/[(1-p)(1-rho)] time steps. At p=.25, this is 1.333 steps for rho=0, 6.667 for rho=.8, and 26.667 for rho=.95. These are **analytical expectations**, not measured experimental results.

## Design and controls
- Reuse the frozen 50,000 synthetic observations and the unchanged decision engine from the November 1 study. Do not describe these observations as longitudinal endpoint measurements.
- Generate 100 time steps per synthetic device. Freeze each device's underlying eight signals across time in the first experiment; label this an artificial stress test. A subsequent study must model changing posture.
- Compare rho in {0, 0.5, 0.8, 0.95}, with p=.25, paired seeds {20260904,20260905,20260906}. Keep all other signals and policy thresholds unchanged.
- First apply one shared Markov mask to the predeclared endpoint-signal group per device; non-endpoint signals retain the prior independently masked mechanism. Separate follow-up arm: a single shared cross-device Markov chain, representing common infrastructure failure. Do not conflate within-device persistence with cross-device correlation.
- Apply each mask to all four existing partial-telemetry policies; preserve the same observations and random streams across policy comparisons.
- Log realized missingness, lag-one autocorrelation, transition counts, outage-length distribution, observed-weight coverage, empty-evidence intervals, per-scenario unsafe ALLOW, safe DENY, safe STEP_UP, and paired decision flips.
- Report rates with both per-observation and per-device denominators. Do **not** calculate confidence intervals as if repeated time steps from the same device were independent; use device-cluster bootstrap, with common-cause outage episodes as the resampling unit where appropriate.
- Predefine sensitivity analyses for 20, 50, 100 steps; 25%, 50% and 75% missingness; and nonstationary onset/recovery. Report empirical transition estimates and check stationary identities before interpreting any decision metrics.

## Validity and interpretation
These masks are independent of the *value* of a security signal and therefore do not simulate MNAR. The simulated time series reuses static scenario labels, which exaggerates sample size if treated as independent observations. The groupings and Markov dynamics are stipulated, not calibrated to an Intune tenant. Outcomes cannot validate real-world attack detection, endpoint availability, or access decisions. No confidential employer telemetry is required.

## Acceptance gates
1. Deterministic reproduction from fixed seeds; validate p and rho within prespecified Monte Carlo tolerances.
2. Unit tests for transition formulas, edge cases, deterministic seeds, and no accidental transitions across device boundaries.
3. Paired decision-count reconciliation and zero change to the scoring implementation.
4. Compare independent-mask arm against the November 1 baseline where observation-level assumptions are equivalent.
5. Full repository tests, manuscript build, and evidence checksums before publishing numerical claims.

## Literature and source check (2026-11-02)
- Rose, S., Borchert, O., Mitchell, S., and Connelly, S. (2020), *Zero Trust Architecture*, NIST SP 800-207, DOI: 10.6028/NIST.SP.800-207. Verified against the NIST publication record on 2026-11-02. It motivates dynamic policy and posture evaluation; it does **not** prescribe Markov outages.
- *State Estimation Over Sensor Networks With Correlated Wireless Fading Channels*, IEEE Transactions on Automatic Control, 58(3), 581–593 (2013), DOI: 10.1109/TAC.2012.2212515. Verified against the IEEE Xplore record on 2026-11-02. Its (semi-)Markov channel-state treatment motivates modeling temporal correlation; it does **not** validate endpoint-trust scoring. Authors intentionally omitted pending separate metadata verification.
No new bibliography entry should be added until all metadata is checked.

## Dated research log
**Date:** 2026-11-02.
**Starting state:** Reviewed existing repository README and 2026-11-01 research log. The prior experiment models within-observation correlated missingness but not temporal persistence.
**Completed:** Specified a stationary Markov outage process, analytic stationarity and expected-run-length identities, paired experimental controls, clustering requirements, acceptance criteria, and limitations. Freshly checked the NIST and IEEE publication records.
**Results:** Analytical expected missing-run durations only; no executed synthetic experiment, empirical effect estimate, CI, or production result.
**Limitations:** No independent endpoint labels, no measured outage dynamics, static synthetic posture, no executed repository-wide verification.
**Next step:** Implement the generator and tests; run paired evaluation and cluster-aware uncertainty estimates; integrate only verified output into the manuscript. **Not IEEE submission-ready.**
