# Baseline Results — Day 1

**Synthetic experiment only. These results do not demonstrate production effectiveness.**

Generated 50,000 endpoint sessions with fixed random seed `20260903`.

```text
Device Trust Baseline Evaluation
==================================
Rows: 50,000
Safe sessions: 29,033
Unsafe sessions: 20,967

Binary compliance
  False-allow rate: 93.74%
  False-deny rate:  14.19%

Multidimensional trust
  False-allow rate: 12.50%
  False-deny rate:  0.00%
  ALLOW:   30,086
  STEP_UP: 11,052
  DENY:    8,862

Evaluation time: 0.5049s
Throughput: 99,037 rows/s
```

Unit tests:

```text
test_binary_baseline_only_uses_compliance ... ok
test_critical_threat_is_hard_denied ... ok
test_healthy_device_is_allowed ... ok
test_missing_security_coverage_is_hard_denied ... ok

----------------------------------------------------------------------
Ran 4 tests

OK
```

## Interpretation

This first run is a **logic-validation baseline**, not a publishable result. The
synthetic generator was intentionally constructed to include nominally compliant but
unsafe scenarios, so a compliance-only baseline is expected to perform poorly on
false allows.

Before using these numbers in a manuscript, the project must add:
- independent scenario calibration;
- threshold/weight sensitivity analysis;
- missing-signal behavior;
- per-scenario error analysis;
- alternative baseline models;
- stronger adversarial generation;
- external or independently sourced data where feasible.
