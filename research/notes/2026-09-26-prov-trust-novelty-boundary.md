# Research note — 2026-09-26

## Step completed

Fresh literature review identified a 2026 comparator that materially narrows the manuscript's contribution boundary:

Xingchen Li, Lifeng Cao, Jinlong Bai, Hengyi Lv, and Xuehui Du, “Prov-Trust: Zero-trust dynamic access control technology based on anomaly detection of provenance graph,” *Journal of King Saud University Computer and Information Sciences*, vol. 38, article 333, 2026. DOI: 10.1007/s44443-026-00731-5. Publisher metadata reports publication on 16 April 2026 and version of record on 17 July 2026.

## Why it matters

Prov-Trust already combines provenance-based behavioral anomaly evidence with multidimensional dynamic trust, historical penalties, adaptive privilege thresholds, and long-horizon behavior handling. It therefore strengthens the conclusion that this project's novelty cannot rest on weighted trust scoring, dynamic thresholds, temporal risk accumulation, or stealthy-behavior handling alone.

The useful unresolved boundary is narrower and more enterprise-endpoint specific: decision robustness when endpoint evidence is missing, stale, partially observable, or mutually compensatory; explicit STEP_UP/abstention behavior under uncertainty; and validation on independently sourced enterprise telemetry.

The paper itself identifies dependence on audit-log integrity/completeness and remaining challenges for very large distributed enterprise deployments. Those limitations directly motivate this project's planned missing-telemetry and stale-evidence experiments, but they do not prove that our proposed framework solves them.

## Evidence classification

This note records **external peer-reviewed evidence** about prior work. It records no new empirical result for the Device Trust Framework. Existing synthetic results remain synthetic. LANL-derived results, when run under the frozen protocol, must be labeled independently sourced telemetry/proxy evidence rather than MDM/EDR posture evidence.

## Consequence for experimental design

Add Prov-Trust to the comparator discussion, but do not attempt to reproduce its TGAT/provenance detector unless the manuscript later makes a direct detection-performance claim. The higher-value next experiment remains the frozen missing/stale-evidence study under identical evidence availability for binary compliance, a conventional weighted score, and the proposed explainable policy.

A specific stress case should preserve apparently healthy observable dimensions while withholding or aging one security-relevant dimension. Primary reporting should include unsafe-ALLOW rate, STEP_UP coverage, safe-user challenge burden, and confidence intervals. Missing evidence must never be silently imputed as healthy.

## Limitations

Prov-Trust evaluates provenance-oriented system behavior, not enterprise MDM compliance. Its reported results are not transferable to this framework. This review does not establish superiority of either approach.

## Next step

Complete the LANL ingest/provenance checks, then run the already-frozen external-validation protocol without retuning thresholds after outcome inspection. After that, add a controlled missing/stale-evidence perturbation layer and per-scenario error analysis.
