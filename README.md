# Device Trust Framework

**Working research project — not yet submitted or peer reviewed**

A reproducible research project investigating whether a transparent, multi-signal
device trust model can improve enterprise access decisions compared with binary
endpoint compliance.

## Working title

**Beyond Binary Compliance: An Explainable Multidimensional Device Trust Framework
for Enterprise Access Decisions**

## Research motivation

Zero Trust guidance requires access decisions to consider device state alongside
identity and other contextual signals. Existing research has proposed trust scoring
for Zero Trust systems, but recent literature still reports fragmentation,
non-standardized metrics, limited real-world validation, limited adversarial
evaluation, and scalability concerns.

This project narrows the problem to **enterprise-managed endpoints** and asks whether
a transparent trust score built from endpoint, identity, security, and freshness
signals can outperform a binary compliance decision in controlled experiments.

## Repository structure

```text
research/
  research-question.md
  literature-review.md
  research-gap.md
  literature-matrix.csv

experiments/
  design.md

src/
  trust_model.py
  generate_synthetic_data.py
  evaluate.py

tests/
  test_trust_model.py

data/
  sample_scenarios.csv

results/
  baseline-results.md

paper/
  main.tex
  references.bib

docs/
  research-log.md
```

## Reproduce the baseline experiment

Python 3.10+ is sufficient; the baseline uses only the standard library.

```bash
python src/generate_synthetic_data.py --rows 50000 --output data/synthetic_endpoints.csv
python src/evaluate.py --input data/synthetic_endpoints.csv
python -m unittest discover -s tests -v
```

## Research integrity

- No employer-confidential telemetry is used.
- Current experiments use synthetic data and are labeled as such.
- Results are not presented as production effectiveness.
- All publication, citation, and performance claims must be independently verifiable.
- Generative-AI assistance must be disclosed as required by the eventual publication venue.

## Current status

Day 1 establishes the research question, literature gap, experimental design,
baseline implementation, synthetic-data generator, tests, and IEEE manuscript shell.
