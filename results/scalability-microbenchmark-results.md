# Scalability microbenchmark results

## Scope

This experiment measures only the in-memory `calculate_trust` decision path. It excludes telemetry collection, event parsing, network calls, persistence, identity-provider latency, and enforcement. The numbers below therefore characterize core policy-computation cost in one execution environment; they are **not** production throughput claims.

## Method

- Python 3.13.5
- Linux 6.18.44 x86_64, glibc 2.41
- CPU reported by the runtime host: AMD EPYC 9V74
- Single Python process
- Eight fixed representative signal profiles spanning ALLOW, STEP_UP, and DENY paths
- 20,000 warm-up decisions before each measured size
- 7 repeated wall-clock measurements per size using `time.perf_counter()`
- 95% Student-t confidence intervals over repeated elapsed-time measurements
- No file or network I/O inside the timed region

The repeated-measurement design follows the general benchmarking principle that performance results should quantify run-to-run variability rather than rely on a single timing observation.

## Results

| Decisions | Mean elapsed (s) | 95% CI (s) | Throughput (decisions/s) | Mean latency (µs/decision) | CV |
|---:|---:|---:|---:|---:|---:|
| 10,000 | 0.055379 | 0.054750–0.056008 | 180,574 | 5.538 | 1.23% |
| 100,000 | 0.564405 | 0.541296–0.587513 | 177,178 | 5.644 | 4.43% |
| 500,000 | 2.749543 | 2.699639–2.799448 | 181,848 | 5.499 | 1.96% |

Outcome-count checksums were stable and proportional across sizes:

- 10,000: 3,750 ALLOW / 2,500 STEP_UP / 3,750 DENY
- 100,000: 37,500 / 25,000 / 37,500
- 500,000: 187,500 / 125,000 / 187,500

## Interpretation

Across the tested sizes, throughput remained between about 177k and 182k decisions/s and mean per-decision time remained between 5.50 and 5.64 µs. Increasing work from 10,000 to 500,000 decisions increased elapsed time by roughly 49.65× for 50× more decisions, which is consistent with approximately linear scaling for this isolated single-process computation.

This result supports only a narrow claim: the current transparent weighted decision function is computationally lightweight in this runtime environment. It does **not** establish end-to-end enterprise scalability, because real systems must also ingest telemetry, join identity/device state, handle storage and network delays, enforce policy, and operate under concurrency and failure.

## Reproducibility

Run:

```bash
PYTHONPATH=src python src/evaluate_scalability.py
```

Targeted tests:

```bash
PYTHONPATH=src pytest -q tests/test_scalability.py
```

The targeted test module passed 3/3 tests in the execution environment used for this result.

## Limitations

- The benchmark ran on a shared/virtualized execution environment and CPU scheduling was not pinned.
- Only one Python/runtime/OS environment was measured.
- The benchmark uses fixed in-memory signal dictionaries and intentionally excludes I/O.
- It measures a single process and does not evaluate contention or horizontal scaling.
- The eight representative profiles exercise multiple decision paths but do not represent a production traffic distribution.
- These performance measurements are independent of the synthetic effectiveness experiments and provide no evidence of security effectiveness.
