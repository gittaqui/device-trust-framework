# Reproducing the frozen LANL second-cohort manuscript evidence

Status: **bounded descriptive study, not validation of the eight-factor device-trust model**. Updated 2026-10-26.

## Provenance and evidence boundary

The two frozen inputs are derived from the **public, de-identified** LANL *Comprehensive, Multi-Source Cyber-Security Events* dataset (Alexander D. Kent, 2015; DOI: 10.17021/1179829; https://csr.lanl.gov/data/cyber1/). LANL's red-team file identifies selected red-team authentication events; the temporal comparison windows are **unlabeled** and must not be called verified benign. The original LANL collection does not contain the eight managed-device posture inputs required to test the proposed access policy.

The inputs are retained in the dated October 25 research handoff archive rather than committed as a raw evidence extract. Their cryptographic checksums are:

| Input under `evidence/lanl-2015-second-cohort/` | SHA-256 |
| --- | --- |
| `replication-paired-features.csv` | `6dfe2e18ed65d2f54d6a73ce5cb8b9848b0ecdf78e3fd36bbf469a52396f14db` |
| `replication-control-manifest.json` | `190190ac1b75495fdfb18422da8b727bdac88553852edba8d236fb3d544957ff` |

**Limitation:** These hashes establish that an analysis used the frozen handoff inputs; they do not independently prove the correctness of the upstream extraction from the original LANL event files. A separate raw-to-derived extraction audit is required for full end-to-end provenance.

## Reproduction

Copy the two frozen files from the October 25 handoff into the indicated `evidence/` directory of a local checkout, then run from repository root:

```bash
python -m unittest discover -s tests -p 'test_*lanl*.py' -v
python scripts/render_lanl_replication_results.py \
  --pairs evidence/lanl-2015-second-cohort/replication-paired-features.csv \
  --manifest evidence/lanl-2015-second-cohort/replication-control-manifest.json \
  --output /tmp/lanl-second-cohort-auto.tex
cmp paper/lanl-second-cohort-auto.tex /tmp/lanl-second-cohort-auto.tex

python scripts/audit_lanl_group_influence.py \
  --pairs evidence/lanl-2015-second-cohort/replication-paired-features.csv \
  --manifest evidence/lanl-2015-second-cohort/replication-control-manifest.json \
  --output /tmp/lanl-group-influence.json
```

The audit's JSON should match the archived `results/lanl-group-influence-2026-10-20.json` byte-for-byte. The manuscript integration helper is deliberately idempotent for the current two-path LaTeX include, and fails closed if the manuscript has an unknown structure.

## Interpretation and inference

The 25 prespecified red-team targets yield 18 matched comparisons and seven without controls. The matched observations come from only four users and two source computers, with 14/18 pairs from one source computer. Group leave-one-out fractions change their denominators and are **influence diagnostics, not confidence intervals**. See A. Colin Cameron and Douglas L. Miller, *A Practitioner's Guide to Cluster-Robust Inference*, *Journal of Human Resources* 50(2), 317–372 (2015), DOI: 10.3368/jhr.50.2.317 (https://doi.org/10.3368/jhr.50.2.317), for the methodological reason not to treat repeated observations as independent.

Do not infer attack-detection accuracy, causal effects, security false-allow rates, or external validation of the eight-factor access model from these process-activity comparisons.
