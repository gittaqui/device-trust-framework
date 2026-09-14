from evaluate_scalability import execute_batch, summarize


def test_execute_batch_counts_every_decision():
    counts = execute_batch(80)
    assert sum(counts.values()) == 80
    assert set(counts) == {"ALLOW", "STEP_UP", "DENY"}


def test_summarize_known_measurements():
    summary = summarize(100, [1.0, 1.1, 0.9, 1.0])
    assert summary.decisions == 100
    assert summary.repetitions == 4
    assert summary.throughput_per_second == 100.0
    assert summary.microseconds_per_decision == 10_000.0
    assert summary.ci95_low_seconds < summary.mean_seconds < summary.ci95_high_seconds


def test_summarize_rejects_too_few_repetitions():
    try:
        summarize(100, [1.0, 1.0, 1.0])
    except ValueError as exc:
        assert "four repetitions" in str(exc)
    else:
        raise AssertionError("expected ValueError")
