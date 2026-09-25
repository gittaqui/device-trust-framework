from src.microsoft_cloud_health_adapter import CrashPoint, causal_robust_scores, roc_auc


def test_causal_scoring_does_not_use_current_label():
    history = [CrashPoint(str(i), 1.0, 0) for i in range(5)]
    a = history + [CrashPoint("5", 10.0, 0)]
    b = history + [CrashPoint("5", 10.0, 1)]
    score_a = causal_robust_scores(a, window=5)[0]
    score_b = causal_robust_scores(b, window=5)[0]
    assert score_a.anomaly_risk == score_b.anomaly_risk
    assert score_a.endpoint_health == score_b.endpoint_health


def test_spike_reduces_endpoint_health():
    points = [CrashPoint(str(i), 1.0, 0) for i in range(5)]
    points.append(CrashPoint("5", 10.0, 1))
    scored = causal_robust_scores(points, window=5)
    assert len(scored) == 1
    assert scored[0].anomaly_risk > 0.9
    assert scored[0].endpoint_health < 0.1


def test_auc_perfect_ranking():
    assert roc_auc([0, 0, 1, 1], [0.1, 0.2, 0.8, 0.9]) == 1.0
