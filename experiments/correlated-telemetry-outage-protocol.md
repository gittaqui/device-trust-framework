# Correlated telemetry-outage stress test — 2026-11-01

**Evidence class:** exploratory simulation on the existing frozen synthetic endpoint generator. Not preregistered, not tenant-derived, and not a measured outage model. No employer data.

## Question and controlled comparison

Do cross-signal dependencies in telemetry availability change ordinary-ALLOW risk and safe-user friction when every signal retains the same 25% *marginal* probability of missingness? This extends the 2026-10-31 single-signal value-dependent ablation; here dropout is **independent of signal values** but correlated **between** missingness indicators. It is MCAR by construction relative to the fixed observations, not MNAR.

Use the same fixed 50,000 generated observations (seed `20260903`; 29,033 scenario-labeled safe, 20,967 unsafe), existing eight signal weights, hard gates, thresholds and `decide_partial` implementation. Four policies: `renormalize`, `neutral`, `pessimistic`, `step_up`. Three paired mask seeds: `20260904`, `20260905`, `20260906`. Do not retune model or thresholds after observing outcomes.

## Missingness arms

For each observation draw eight independent U(0,1) variates, one shared U(0,1), and one common-mode selector V~U(0,1). A signal is missing if its selected uniform is less than p=0.25. All arms reuse the same random draws per observation.

- `independent`: all eight use independent draws.
- `endpoint_rho_half`: five endpoint-origin signals (`endpoint_health`, `patch_posture`, `security_coverage`, `threat_risk`, `anomaly_risk`) use the shared draw when V<0.5, otherwise their independent draws; identity, compliance, and freshness always use independent draws. Endpoint-pair missingness correlation is 0.5 in expectation.
- `endpoint_rho_one`: those five signals always use the shared draw; other three are unchanged. Endpoint-pair missingness correlation is 1 in expectation.
- `global_rho_one`: all eight signals use the shared draw, producing either full evidence or zero evidence for a row.

For each signal and arm, P(missing)=0.25 in expectation. Thus comparisons change the **joint pattern**, not marginal dropout probabilities. Group selection is an assumption to stress-test possible shared telemetry sources, not a measured Intune/Defender architecture dependency. Rows are independent: this does **not** simulate persistent outages across time or across devices.

## Endpoints and checks

Primary endpoint: scenario-labeled unsafe ordinary-ALLOW count / all unsafe observations. Secondary: safe ordinary ALLOW, DENY, STEP_UP; per-scenario unsafe ALLOW; realized missing fraction; fraction with all eight signals missing/observed; empirical phi correlation of `endpoint_health` and `security_coverage` missingness; paired ALLOW flips against independent arm. Reconcile all denominators and score-coverage invariants. Summaries across three fixed mask seeds are descriptive sensitivity ranges, **not population confidence intervals**.

Run:

```bash
python src/generate_synthetic_data.py --rows 50000 --seed 20260903 --output data/synthetic_endpoints.csv
python src/evaluate_correlated_missingness.py --input data/synthetic_endpoints.csv --output results/correlated_missingness_2026-11-01.json
python -m unittest discover -s tests -p 'test_correlated_missingness.py'
```

## Literature and inference boundary

- Ian H. Dinwoodie (2019), *Missing sensor network data*, **Communications in Statistics: Case Studies, Data Analysis and Applications**, 5(2), 146–152. DOI `10.1080/23737484.2018.1563513`; publisher metadata checked 2026-11-01: https://www.tandfonline.com/doi/full/10.1080/23737484.2018.1563513. This peer-reviewed paper discusses intervals of sensor downtime and correlated observations; it does not estimate endpoint outage correlations or validate this model.
- Rose et al. (2020), NIST SP 800-207, DOI `10.6028/NIST.SP.800-207`: device posture and dynamic access context, not a prescribed dropout model.

The generated safety labels are scenario-defined, and the same generator informed prior policy development. Masks do not depend on values, but synthetic scenario prevalence, signal distributions, chosen group membership, lack of temporal/device clustering, and post-hoc arm design limit generalizability. Report no empirical enterprise effectiveness or statistical significance. A credible follow-up requires authorized non-production endpoint observations, measured co-outage structure, and independently adjudicated outcomes.
