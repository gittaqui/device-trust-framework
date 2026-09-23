"""Compare the hand-weighted trust policy with a learned linear baseline.

The experiment uses disjoint synthetic train, calibration, and test samples.
Both models select an ALLOW threshold on calibration data to maximize ordinary-
access coverage subject to <=1% empirical unsafe-ALLOW risk. Results therefore
measure behavior under the authored generator, not production effectiveness.
"""
from __future__ import annotations

import argparse
import numpy as np
from sklearn.linear_model import LogisticRegression

from evaluate_overlap_dependence import overlap_signals
from generate_synthetic_data import SCENARIOS, SCENARIO_WEIGHTS
from trust_model import calculate_trust
import random

SIGNALS = tuple(next(iter(SCENARIOS.values()))["ranges"])
CONDITIONS = ((0.0, 0.0), (0.6, 0.0), (0.6, 0.25), (0.6, 0.50), (0.6, 0.75))


def sample(rows: int, seed: int, rho: float, overlap: float):
    rng = random.Random(seed)
    names = [n for n, _ in SCENARIO_WEIGHTS]
    weights = [w for _, w in SCENARIO_WEIGHTS]
    x, y = [], []
    for _ in range(rows):
        scenario = rng.choices(names, weights=weights, k=1)[0]
        values = overlap_signals(rng, scenario, rho, overlap)
        x.append([values[s] for s in SIGNALS])
        y.append(int(SCENARIOS[scenario]["safe"]))
    return np.asarray(x), np.asarray(y)


def unsafe_risk(allow: np.ndarray, y: np.ndarray) -> float:
    return float(np.sum(allow & (y == 0)) / np.sum(allow)) if np.sum(allow) else 0.0


def metrics(allow: np.ndarray, y: np.ndarray) -> tuple[float, float, float]:
    return float(np.mean(allow)), unsafe_risk(allow, y), float(np.sum(allow & (y == 1)) / np.sum(y == 1))


def calibrate_threshold(score_fn, y: np.ndarray, thresholds, risk_limit: float = 0.01):
    best = None
    for threshold in thresholds:
        allow = score_fn(float(threshold))
        if np.sum(allow) and unsafe_risk(allow, y) <= risk_limit:
            candidate = (float(np.mean(allow)), float(threshold))
            if best is None or candidate[0] > best[0]:
                best = candidate
    if best is None:
        return 1.0
    return best[1]


def trust_allow(x: np.ndarray, threshold: float) -> np.ndarray:
    return np.asarray([
        calculate_trust(dict(zip(SIGNALS, row)), allow_threshold=threshold).decision == "ALLOW"
        for row in x
    ])


def evaluate_condition(rho: float, overlap: float, train_rows=30_000, calibration_rows=10_000, test_rows=30_000):
    offset = int(rho * 10) + int(overlap * 100)
    x_train, y_train = sample(train_rows, 100 + offset, rho, overlap)
    x_cal, y_cal = sample(calibration_rows, 200 + offset, rho, overlap)
    x_test, y_test = sample(test_rows, 300 + offset, rho, overlap)

    model = LogisticRegression(C=100.0, max_iter=1000, random_state=0)
    model.fit(x_train, y_train)
    p_cal = model.predict_proba(x_cal)[:, 1]
    p_test = model.predict_proba(x_test)[:, 1]

    trust_threshold = calibrate_threshold(
        lambda t: trust_allow(x_cal, t), y_cal, np.linspace(0.50, 0.999, 500)
    )
    probability_thresholds = np.unique(np.quantile(p_cal, np.linspace(0.0, 1.0, 501)))
    learned_threshold = calibrate_threshold(lambda t: p_cal >= t, y_cal, probability_thresholds)

    trust = metrics(trust_allow(x_test, trust_threshold), y_test)
    learned = metrics(p_test >= learned_threshold, y_test)
    return {
        "rho": rho, "overlap": overlap,
        "trust_threshold": trust_threshold, "trust": trust,
        "learned_threshold": learned_threshold, "learned": learned,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args()
    sizes = (3_000, 1_000, 3_000) if args.quick else (30_000, 10_000, 30_000)
    for rho, overlap in CONDITIONS:
        r = evaluate_condition(rho, overlap, *sizes)
        print(r)


if __name__ == "__main__":
    main()
