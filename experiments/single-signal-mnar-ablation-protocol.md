# Paired single-signal value-dependent missingness ablation — 2026-10-31

**Status:** exploratory synthetic sensitivity study, designed after inspecting the October 30 all-eight-signal experiment. **Not preregistered.** No employer or production telemetry is used.

## Question and frozen setup

Which of three security-relevant dimensions—identity assurance, threat risk, or security coverage—accounts for the greatest deterioration in ordinary-ALLOW decisions when its unfavorable values become more likely to be missing, holding each column's expected missing fraction constant?

Reuse the existing generator (50,000 observations, seed `20260903`), its scenario-defined labels, `decide_partial`, existing weights, thresholds, and hard gates. The policies are `renormalize`, `neutral`, `pessimistic`, and explicit `step_up`. The algebraically equivalent `confidence` policy is not counted as an independent comparator.

## Five paired masking arms

For each row i and signal j, define risk-oriented value r_ij = x_ij for risk fields, and 1-x_ij for assurance/safety fields. Missingness probability under value dependence is

    p_ij = sigmoid(alpha_j + 4 * (r_ij - 0.5))

The intercept alpha_j is calibrated on the **complete fixed synthetic dataset** to make the expected missing fraction for signal j exactly 0.25. In the MCAR arm, p_ij = 0.25. Compare:

1. `mcar`: beta=0 for all eight signals.
2. `identity_assurance`: beta=4 for identity assurance; beta=0 for other seven.
3. `threat_risk`: beta=4 for threat risk; beta=0 for other seven.
4. `security_coverage`: beta=4 for security coverage; beta=0 for other seven.
5. `all_eight`: beta=4 for all eight signals, to reproduce the October 30 arm.

Draw one uniform random value per observation/signal using each seed (`20260904`, `20260905`, `20260906`), and reuse the same uniform in **every** arm and policy. For a single-signal arm, the other seven masks must be **bitwise identical** to MCAR. The all-eight and MCAR arms must reproduce the prior experiment's counts exactly.

## Outcomes

Primary: scenario-labeled unsafe ordinary-ALLOW fraction (denominator: all unsafe observations). Secondary: safe DENY, safe STEP_UP, safe ordinary ALLOW (denominator: all safe observations); per-scenario unsafe ALLOW; realized missing-cell fraction; low-risk and high-risk conditional missingness for the three target signals; and paired ALLOW-to-not-ALLOW / not-ALLOW-to-ALLOW flips against MCAR. Record numerator and denominator. Summaries across three seeds are descriptive mask-RNG sensitivity, not confidence intervals.

The single-signal contrasts are **masking interventions in the fixed generator**, not population causal effects. The difference between all-eight and the three single-signal contrasts cannot be assigned to untested signals alone: nonlinear decision thresholds and interactions also matter.

## Verification and limits

Check exact MCAR/all-eight compatibility with `src/evaluate_value_dependent_missingness.py`; deterministic mask sharing; expected missingness calibration for each signal; paired-flip reconciliation; safe/unsafe denominator reconciliation; invalid-input rejection; repeatability. The generator-defined labels, outcome-informed selection of target signals, full-sample calibration, conditional independence of Bernoulli masks given signals, and lack of real-world outage data limit inference. No significance tests or generalizable performance claims are warranted.

### Peer-reviewed methodological context (metadata checked 2026-10-31)

- Roderick J. Little (2024), *Missing Data Analysis*, **Annual Review of Clinical Psychology**, 20:149–173, DOI `10.1146/annurev-clinpsy-080822-051727`. Publisher: https://www.annualreviews.org/content/journals/10.1146/annurev-clinpsy-080822-051727. Explains why missingness assumptions and sensitivity analyses must be explicit; it does not validate the proposed endpoint model.
- Brenna Gomer and Ke-Hai Yuan (2021), *Subtypes of the missing not at random missing data mechanism*, **Psychological Methods**, 26(5):559–598, DOI `10.1037/met0000377`. Bibliographic record: https://pubmed.ncbi.nlm.nih.gov/34180695/. Distinguishes missingness mechanisms; it does not supply evidence about enterprise endpoint telemetry.

## Reproduction

```bash
python src/generate_synthetic_data.py --rows 50000 --seed 20260903 --output data/synthetic_endpoints.csv
python src/evaluate_single_signal_mnar_ablation.py --input data/synthetic_endpoints.csv --rate 0.25 --beta 4 --seeds 20260904 20260905 20260906 --output results/single_signal_mnar_ablation_2026-10-31.json
python -m unittest discover -s tests -p 'test_single_signal_mnar_ablation.py'
```

Full JSON is distributed separately as a research handoff to avoid adding large generated evidence to GitHub. Compact findings: `results/single-signal-mnar-ablation-2026-10-31.md`.
