# Benign identity-overlap sensitivity analysis

Date: 2026-09-09

## Purpose

The earlier identity non-compensation experiment showed that a guard on low identity assurance or high anomaly risk can sharply reduce synthetic false ALLOW decisions without increasing benign STEP_UP in the original generator. That apparent low-friction result depends on a strong labeling assumption: every `identity_risk` scenario is treated as unsafe.

This experiment stress-tests that assumption by progressively reinterpreting a nested subset of the same synthetic `identity_risk` rows as legitimate sessions that should receive ordinary access. This is a **label-sensitivity analysis**, not an estimate of real-world benign-risk prevalence.

## Design

- Population: 50,000 seeded synthetic rows generated with `data_seed=20260903`.
- Identity-risk rows: 3,912.
- Overlap assignment: stable pseudo-random score with `overlap_seed=20260909`.
- Fractions tested: 0%, 10%, 25%, 50%, and 100% of `identity_risk` rows relabeled safe.
- Policies compared:
  - additive score, ALLOW threshold 0.75;
  - additive score, ALLOW threshold 0.80;
  - additive 0.75 plus identity/anomaly STEP_UP guard.
- Policy outputs are held fixed. Only the evaluation labels change.

The nested relabeling design ensures that increasing overlap adds cases to the previously relabeled set rather than drawing an unrelated sample.

## Results

| Identity-risk rows reinterpreted as benign | Actual relabeled rows | Additive .75 false ALLOW | Additive .75 safe STEP_UP | Additive .80 false ALLOW | Additive .80 safe STEP_UP | Guarded .75 false ALLOW | Guarded .75 safe STEP_UP |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0% | 0 | 12.50% | 5.40% | 0.34% | 13.58% | 1.24% | 5.40% |
| 10% | 368 | 11.66% | 5.84% | 0.32% | 14.64% | 1.26% | 6.58% |
| 25% | 995 | 10.20% | 6.59% | 0.29% | 16.39% | 1.30% | 8.54% |
| 50% | 1,965 | 7.89% | 7.78% | 0.20% | 18.95% | 1.37% | 11.40% |
| 100% | 3,912 | 1.99% | 9.71% | 0.00% | 23.62% | 1.52% | 16.63% |

No policy produced a safe DENY in this sensitivity run.

## Interpretation

The earlier conclusion that the identity guard imposes essentially no benign friction is not robust to benign/unsafe overlap in the identity-risk region. When 25% of the synthetic identity-risk rows are treated as legitimate, guarded safe STEP_UP rises from 5.40% to 8.54%. At 50% overlap it rises to 11.40%, and at full overlap to 16.63%.

The stricter global threshold shows an even larger abstention cost under the same relabeling, rising from 13.58% safe STEP_UP at zero overlap to 23.62% at full overlap. The additive 0.75 policy is less sensitive in friction but retains higher false-ALLOW rates while unsafe identity-risk examples remain.

These results do **not** establish an optimal policy. They demonstrate that the apparent superiority of any guard depends materially on the prevalence and labeling of benign sessions with weak or anomalous identity evidence.

## Relation to reject-option literature

The `STEP_UP` state is best framed as an abstention/reject action rather than as a third semantic class. Chow's classic IEEE analysis formalized the recognition-error versus rejection trade-off, and later reject-option work explicitly treats withholding a classification as appropriate for uncertain observations. This literature supports analyzing STEP_UP as a cost/error trade-off rather than presenting higher abstention as automatically better or worse.

## Limitations

1. All endpoint features remain synthetic.
2. Relabeling is hypothetical and does not estimate real-world prevalence.
3. The same feature vectors are reused; only their evaluation labels change.
4. The experiment does not model the cost or success probability of MFA, remediation, or analyst review after STEP_UP.
5. Because the original synthetic `identity_risk` distribution was intentionally risky, relabeling all such rows as benign is an extreme stress condition, not a realistic operating assumption.

## Manuscript consequence

The manuscript should no longer describe the identity guard as low-friction without qualification. A defensible claim is narrower: **non-compensatory guards can reduce false ordinary-access decisions, but their operational cost depends on overlap between benign and unsafe identity-risk states; therefore guard thresholds require external calibration and should be evaluated jointly with abstention cost.**

## Reproduction

```bash
python src/evaluate_benign_identity_overlap.py --rows 50000 --data-seed 20260903 --overlap-seed 20260909
```
