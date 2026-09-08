# LANL 2017 External Host-Event Validation Protocol

## Purpose

This protocol defines the first externally sourced telemetry path for the Device Trust Framework. It uses the Los Alamos National Laboratory (LANL) **Unified Host and Network Data Set** as an independent source of de-identified enterprise Windows host telemetry.

This is an ingestion and analysis protocol, **not a claim of real-world model effectiveness**. No LANL raw data are committed to this repository.

## Verified source and provenance

Official dataset page:

- https://csr.lanl.gov/data/2017/

The LANL page states that the dataset contains approximately 90 days of de-identified events from the LANL enterprise network. Host events originate from enterprise computers running Microsoft Windows. The release includes authentication and process-related Windows event IDs such as 4624, 4625, 4648, 4672, 4688, 4689, 4768, 4769, 4770, 4774, and 4776.

Required dataset citation:

Melissa J. M. Turcotte, Alexander D. Kent, and Curtis Hash, "Unified Host and Network Data Set," in *Data Science for Cyber-Security*, Chapter 1, pp. 1-22, World Scientific, 2018. DOI: `10.1142/9781786345646_001`.

LANL states that the dataset was approved for public release under LA-UR-17-20763 and provides the data under a CC0-style waiver.

## Why use the 2017 release

The earlier LANL multi-source dataset provides red-team labels but its authentication file is 7.2 GB compressed. The 2017 release is divided into daily files, which enables a bounded, auditable first experiment before any large-scale analysis.

The 2017 host dataset also exposes Windows Security Event IDs and process events directly, making the mapping to enterprise endpoint behavior more transparent than mapping generic network features to device trust.

## Feature mapping

`src/lanl_2017_host_adapter.py` derives only transparent research proxies:

| LANL observation | Derived proxy | Interpretation |
| --- | --- | --- |
| Prior failed authentication rate | `prior_failure_rate` | Historical authentication instability |
| First observed user-host relation | `new_user_host_edge` | Authentication novelty |
| Event 4648 | `explicit_credentials` | Explicit-credential use indicator |
| Event 4672 | `privileged_logon` | Privileged-logon indicator |
| First observed process on host | `new_process_on_host` | Process novelty |
| User/host event gap | `freshness` | Relative activity recency |
| Combination of above | `identity_assurance`, `anomaly_risk` | Explainable research proxies only |

These fields **must not** be described as Intune compliance, Microsoft Entra risk, Defender device risk, or validated production risk scores.

## Leakage controls

The first external experiment must preserve temporal causality:

1. Process events in timestamp order.
2. Compute novelty and prior failure history **before** updating state with the current event.
3. Do not use later observations to score earlier events.
4. If a downstream attack/anomaly label is introduced, do not incorporate the current or future label into feature construction.
5. Split calibration and evaluation by time, not random rows, when threshold calibration is eventually attempted.

The adapter implements rule 2 explicitly.

## Bounded first run

After obtaining the data directly from the official LANL source, begin with one host-event day and a bounded prefix:

```bash
python -m src.lanl_2017_host_adapter \
  --input data/external/lanl2017/wls_day-01.jsonl \
  --max-rows 100000
```

The LANL files are distributed as `.bz2`; decompression should preserve the original file and its checksum. Record:

- source URL,
- download date,
- original filename,
- SHA-256 checksum,
- decompressed filename,
- number of processed records,
- adapter commit SHA.

Do not commit the raw dataset.

## Pre-registered first descriptive outputs

Before viewing outcome-dependent results, record only:

- number of events processed,
- authentication-event count,
- process-start count,
- observed authentication failures,
- novel user-host edge count,
- explicit-credential event count,
- privileged-logon event count,
- novel process-start count,
- mean proxy identity assurance,
- mean proxy anomaly risk.

These are descriptive telemetry-distribution measurements, not security effectiveness metrics.

## Next evaluation after descriptive validation

Once the adapter is verified on real LANL data:

1. characterize benign overlap among novelty, failure, privilege, and process signals;
2. estimate how often the current synthetic identity guard would challenge ordinary externally observed activity;
3. use temporal holdout data for any threshold calibration;
4. separately integrate a dataset with independently defined malicious/red-team labels before reporting false-allow/false-denial claims;
5. compare additive, non-compensatory, and abstention policies without tuning and evaluating on the same interval.

## Current limitation

As of 2026-09-07, this repository contains the tested ingestion path but no downloaded LANL day and therefore **no real-world LANL results**. The official LANL site requests an email address and description of intended use before download. That user-controlled data-access step has not been automated or submitted on the researcher's behalf.
