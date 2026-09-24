"""Evaluate frozen device-trust policies under synthetic distribution shift.

Both the hand policy threshold and an L2-logistic baseline are calibrated once
on the nominal synthetic population (rho=0, overlap=0). Model parameters and
thresholds are then frozen and transported unchanged to stressed populations.
This isolates deployment shift from condition-specific recalibration.
"""
from __future__ import annotations

import argparse
import numpy as np
from sklearn.linear_model import LogisticRegression

from evaluate_learned_baseline import (
    SIGNALS, calibrate_threshold, metrics, sample, trust_allow,
)

TARGET_CONDITIONS = ((0.0, 0.0), (0.6, 0.0), (0.6, 0.25), (0.6, 0.50), (0.6, 0.75))


def fit_nominal(train_rows=30_000, calibration_rows=10_000):
    """Fit/calibrate once on nominal synthetic data and return frozen policy."""
    x_train, y_train = sample(train_rows, 100, 0.0, 0.0)
    x_cal, y_cal = sample(calibration_rows, 200, 0.0, 0.0)

    model = LogisticRegression(C=100.0, max_iter=1000, random_state=0)
    model.fit(x_train, y_train)
    p_cal = model.predict_proba(x_cal)[:, 1]

    trust_threshold = calibrate_threshold(
        lambda t: trust_allow(x_cal, t), y_cal, np.linspace(0.50, 0.999, 500)
    )
    learned_threshold = calibrate_threshold(
        lambda t: p_cal >= t,
        y_cal,
        np.unique(np.quantile(p_cal, np.linspace(0.0, 1.0, 501))),
    )
    return model, trust_threshold, learned_threshold


def evaluate_transport(train_rows=30_000, calibration_rows=10_000, test_rows=30_000):
    model, trust_threshold, learned_threshold = fit_nominal(train_rows, calibration_rows)
    results = []
    for index, (rho, overlap) in enumerate(TARGET_CONDITIONS):
        x_test, y_test = sample(test_rows, 300 + index, rho, overlap)
        trust = metrics(trust_allow(x_test, trust_threshold), y_test)
        learned = metrics(model.predict_proba(x_test)[:, 1] >= learned_threshold, y_test)
        results.append({
            "rho": rho,
            "overlap": overlap,
            "trust": trust,
            "learned": learned,
        })
    return {
        "trust_threshold": trust_threshold,
        "learned_threshold": learned_threshold,
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args()
    sizes = (3_000, 1_000, 3_000) if args.quick else (30_000, 10_000, 30_000)
    result = evaluate_transport(*sizes)
    print(f"frozen trust threshold={result['trust_threshold']:.6f}")
    print(f"frozen logistic threshold={result['learned_threshold']:.6f}")
    for row in result["results"]:
        print(row)


if __name__ == "__main__":
    main()
