from src.evaluate_risk_coverage import evaluate_risk_coverage


def test_risk_coverage_is_deterministic():
    first = evaluate_risk_coverage(rows=2_000, seed=17)
    second = evaluate_risk_coverage(rows=2_000, seed=17)
    assert first == second


def test_higher_threshold_does_not_increase_coverage():
    results = evaluate_risk_coverage(rows=5_000, seed=19)
    coverages = [float(row["ordinary_access_coverage"]) for row in results]
    assert coverages == sorted(coverages, reverse=True)


def test_metrics_are_probabilities():
    for row in evaluate_risk_coverage(rows=1_000, seed=23):
        assert 0.0 <= float(row["ordinary_access_coverage"]) <= 1.0
        assert 0.0 <= float(row["unsafe_allow_risk"]) <= 1.0
        assert 0.0 <= float(row["safe_session_allow_recall"]) <= 1.0
