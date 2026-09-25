# External Validation Matrix

_Last updated: 2026-09-25_

The Device Trust Framework must not manufacture a complete endpoint record by joining unrelated public datasets. Each source is used only for the trust component that it actually observes.

| Source | Environment | Ground truth / labels | Framework component(s) | Permitted claim | Main limitation |
|---|---|---|---|---|---|
| LANL Unified Host & Network (2017) | Real de-identified LANL enterprise Windows host/network telemetry, ~90 days | No complete attack ground truth | identity assurance proxy, anomaly risk, freshness, host behavior | component plausibility on real enterprise Windows telemetry | no native Intune compliance, Defender risk, patch posture, or security-control state |
| LANL Comprehensive Multi-Source (2015) | Real LANL enterprise auth/process/DNS/flow telemetry, 58 days | Known red-team authentication events | identity/anomaly/threat component evaluation | component-level discrimination around independently supplied red-team events | red-team labels cover specific malicious events, not full multidimensional trust ground truth |
| Microsoft Cloud Monitoring Dataset | Real Microsoft production service/client time series | Expert-labeled anomaly points | endpoint-health / reliability component | reliability signal behavior on real production telemetry | aggregate time series, not per-device endpoint state |
| Microsoft GUIDE | Real security incidents/evidence with analyst triage labels | True positive / benign positive / false positive incident triage | threat/risk/triage component | component-level risk/triage evaluation | incident evidence is not device posture and must not be converted into compliance/patch state |
| DARPA OpTC | Instrumented Windows 10 test environment; approximately 500 collected hosts | Red-team ground truth | threat/anomaly behavior, adversarial endpoint scenarios | adversarial Windows endpoint component evaluation | generated benign activity and controlled testbed are not a natural enterprise population |
| Loghub Windows | Windows CBS/event logs from a lab environment | No device-trust outcome labels | servicing/update feature extraction | narrow feasibility of deriving servicing signals from Windows logs | lab-scale/single-system provenance is insufficient for fleet-wide patch-posture validation |

## Claim firewall

Evidence levels remain separate:

1. **Synthetic experiments:** mechanism, sensitivity, ablation, robustness stress tests.
2. **Unlabeled real enterprise telemetry:** feature plausibility, distribution behavior, operational feasibility.
3. **Independently labeled component datasets:** component-level discrimination or anomaly/triage evaluation.
4. **Jointly observed multidimensional endpoint state + access outcomes:** required before claiming full-model effectiveness.

No source in the current public stack satisfies level 4 by itself.

## Current status

- LANL adapters/protocol: implemented; provider download flow still requires user-supplied research email/use declaration before protected files can be obtained.
- Microsoft Cloud Monitoring: **first full component-level pilot completed on all 19 Windows application-crash series**.
- GUIDE: verified as a suitable threat/triage source; full dataset is multi-gigabyte and should be sampled with a frozen protocol before download.
- OpTC: suitable for adversarial Windows endpoint validation; raw corpus is roughly terabyte-scale, so only a bounded host/time slice should be used.
- Loghub Windows: suitable only for servicing-feature feasibility, not fleet effectiveness.

## Rule for manuscript wording

Use phrases such as **component-level external validation**, **real production telemetry**, **real enterprise telemetry**, and **controlled adversarial testbed** precisely.

Do not write **externally validated Device Trust Framework** until a dataset contains jointly observed trust dimensions and an appropriate access-decision outcome or an equivalent independently defensible evaluation design.
