# LANL-2015 bounded context extraction — first 25 red-team labels

**Status:** Descriptive external enterprise telemetry analysis. This is **not** a model-performance result and does not establish production security effectiveness.

## Provenance

- Dataset: LANL Comprehensive Multi-Source Cyber-Security Events (2015)
- Authoritative DOI: `10.17021/1179829`
- Operational mirror: `Taqui/lanl-cyber-datasets`
- GitHub Actions run: `36767838236`
- Extraction code: `src/extract_lanl_context_remote.py`
- Label source: `lanl-2015/redteam.txt`
- Selected cohort: first 25 of 749 red-team authentication labels
- Context window: ±600 seconds
- Merged temporal windows: 8

The red-team file identifies specific known malicious authentication events. Process, DNS, and flow records surrounding those events are retained only as contextual telemetry and are **not** relabeled as malicious.

## Bounded extraction results

| Source | Remote size (bytes) | Events scanned in selected windows | Retained focus-entity events | Selected labels with matching context | Median retained rows per selected label | Median nearest-event distance |
|---|---:|---:|---:|---:|---:|---:|
| Process | 15,397,551,964 | 1,048,339 | 4,561 | 25/25 | 38 | 2 s |
| DNS | 812,736,592 | 10,602 | 129 | 3/25 | 0 overall; 5 among covered labels | 11 s among covered labels |
| Flow | 5,237,189,507 | 1,452,153 | 9,333 | 22/25 | 135 | 1.5 s among covered labels |

For labels with matching telemetry, the maximum nearest-event distance was 222 seconds for process, 77 seconds for DNS, and 4 seconds for flow.

## Integrity checks

- Every retained process/DNS/flow row has `context_only=1`.
- No retained row falls outside the eight predefined merged time windows.
- No exact duplicate rows were found in the three bounded CSV outputs.
- The extraction uses byte-range reads and does not download the full 444-GB mirror into the runner.
- The available mirror inventory contained 60 files total and 8 under `lanl-2015/`.
- As of this run, `lanl-2015/auth.txt` was not yet present, so no authentication-derived empirical result was produced.

## Interpretation

The available external telemetry shows that process and network-flow context is temporally dense around most of the first 25 known red-team authentication events for the implicated entities. DNS context is substantially sparser in this small selected cohort.

This observation is descriptive only. The cohort was selected around known red-team events and implicated entities, so these counts cannot be interpreted as detection accuracy, causal evidence, attack prevalence, or representative enterprise behavior.

## Limitations

1. Only the first 25 of 749 red-team labels were used.
2. The cohort is conditioned on known red-team labels and focus entities; matched benign controls have not yet been constructed.
3. Process, DNS, and flow records have no attack ground-truth labels in this analysis.
4. `auth.txt` is not yet available in the mirror, preventing the planned authentication baseline and exact authentication-event feature extraction.
5. LANL does not provide MDM compliance, EDR health, patch posture, or proprietary identity-risk signals. These sources remain enterprise-telemetry proxies only.

## Next step

Freeze and implement a matched benign-control protocol using pre-outcome information only, then derive transparent process/flow/DNS context features under identical windows. Authentication-derived features should be added only after `auth.txt` becomes available. Model thresholds must remain frozen during this external-validation stage.
