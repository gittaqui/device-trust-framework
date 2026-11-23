# Paired dependence-aware inference protocol — 2026-11-22

## Purpose and relation to prior work
Extends the 2026-11-18 through 2026-11-21 synthetic AR(1) interval-coverage audits. The previous studies show that neither naive Student-t, fixed-bandwidth HAC, basic stationary bootstrap nor a lag-one plug-in interval is uniformly calibrated under strong persistence. **No estimator has been selected.** This is a *preregistered experimental specification*, not an empirical result.

## Estimand and experimental unit
Primary estimand: population mean of a zero-mean stationary episode-level outcome. A simulation replicate is one independently generated **complete time series**, not an individual episode or endpoint. Each method receives identical replicate data (paired design). For a later device-by-episode panel, the estimand must be specified before selecting clustering or resampling units.

## Data-generating mechanisms
1. Benchmark: Gaussian AR(1), x_t = phi*x_(t-1) + sqrt(1-phi^2)*epsilon_t, with stationary initialization and epsilon_t iid N(0,1). n in {10,30,100}; phi in {0,0.3,0.6,0.9}; 2,000 independent series per cell. Fixed deterministic seed, with independent streams per condition.
2. Stress case (separate, not pooled): phi in {-0.3,0.95}, to examine negative dependence and near-unit-root behavior. Flag the latter as a difficult finite-sample regime, not proof of asymptotic validity.
3. Panel extension (future): crossed device random intercepts and episode shocks, serially correlated episode shocks, and missing-at-random versus outcome-dependent missingness. Clearly label missing-not-at-random assumptions as unidentifiable from observed data alone.

## Methods, specified before outcomes
A. Ordinary Student-t interval for the episode mean (negative control when phi != 0).
B. Sample-based Bartlett HAC interval, lag min(3,n-1) and min(8,n-1), normal critical value; reproduce existing code.
C. Feasible AR(1) generalized least squares: estimate phi and innovation variance *from the same series*, constrain phi to [-0.98,0.98], use stationary covariance, compute GLS intercept and its plug-in standard error; explicitly acknowledge estimated-parameter uncertainty.
D. Parametric AR(1) bootstrap for the mean: refit phi and innovation variance in each simulated series; evaluate percentile and studentized variants separately. Do not call this nonparametric or distribution-free.
E. Oracle using true phi and true marginal variance (diagnostic upper benchmark only, never a deployable baseline).

Do not silently optimize lag, block length, or interval critical values on the same evaluation replications. Any calibration must use separate development seeds and a held-out final evaluation.

## Outcomes and statistical reporting
Primary: two-sided nominal 95% interval coverage, with Wilson 95% Monte Carlo uncertainty interval for the coverage proportion. Secondary: median and 90th-percentile interval width; nonpositive or undefined variance fraction; empirical bias and RMSE of the mean estimator; computation time. Report **paired** coverage differences and uncertainty via independent replicate-level differences, not an unpaired test. At 2,000 replicates, worst-case coverage Monte Carlo SE <= 1.12 percentage points. Treat multiple comparisons as exploratory and report every prespecified condition, including failures.

## Implementation quality gates
- Assert exact AR(1) stationary variance and the finite-n oracle mean variance against independent mathematical formulas.
- Unit-test constant sequences, n=10, phi=0, phi near bounds, and reproducibility.
- Fail explicitly for nonfinite estimates and nonpositive estimated variance; count failures rather than silently dropping.
- Run a clean-checkout test suite and pin Python dependencies; archive seed, environment, command, and machine-readable outputs.
- Reproduce earlier 2026-11-20 paired coverage within Monte Carlo uncertainty before adding new methods.

## Scope and validity
All evidence is synthetic and concerns **uncertainty estimation**, not discrimination, attack detection, access control, or endpoint trust. A calibrated interval alone does not establish the manuscript's security contribution. Subsequent eight-factor experiments must compare binary compliance, simple weighted score, and multidimensional trust using adversarially compliant devices, telemetry dropout, threshold and weight perturbations, and explicitly defined false-allow / false-deny costs. Do not use confidential employer data.

## Peer-reviewed methodological context (publisher verified)
Kiefer, N. M., & Vogelsang, T. J. (2005). A new asymptotic theory for heteroskedasticity-autocorrelation robust tests. *Econometric Theory*, 21(6), 1130–1164. https://doi.org/10.1017/S0266466605050565 . Publisher: https://www.cambridge.org/core/journals/econometric-theory/article/abs/new-asymptotic-theory-for-heteroskedasticityautocorrelation-robust-tests/E4B23DC06C2508DDCFF148E04269AF28 . This paper motivates explicit sensitivity to bandwidth and critical-value theory; it does **not** validate the methods or Device Trust Framework.
