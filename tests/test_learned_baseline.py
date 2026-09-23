import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
from evaluate_learned_baseline import metrics, unsafe_risk


def test_unsafe_risk_counts_only_allowed_sessions():
    allow = np.array([True, True, False, False])
    y = np.array([1, 0, 0, 1])
    assert unsafe_risk(allow, y) == 0.5


def test_metrics_reports_coverage_risk_and_safe_recall():
    allow = np.array([True, False, True, False])
    y = np.array([1, 1, 0, 0])
    coverage, risk, recall = metrics(allow, y)
    assert coverage == 0.5
    assert risk == 0.5
    assert recall == 0.5
