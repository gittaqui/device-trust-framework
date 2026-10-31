"""Calibrated value-dependent (MNAR-by-construction) telemetry dropout audit.

Research-only synthetic sensitivity experiment. The mask probability depends on
its own potentially unobserved signal value; it is NOT an estimated enterprise
outage model. A shared uniform draw pairs the strength arms within each seed.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import random
from collections import Counter
from pathlib import Path

from evaluate_missing_telemetry import SIGNAL_TO_FACTOR, decide_partial
from evaluate_missing_telemetry_paired import _validate_row
from trust_model import DEFAULT_WEIGHTS

SIGNALS = tuple(SIGNAL_TO_FACTOR)
POLICIES = ("renormalize", "neutral", "pessimistic", "step_up")
STRENGTHS = (0.0, 2.0, 4.0)
PROBE_SIGNALS = ("identity_assurance", "threat_risk", "security_coverage")


def risk_value(signal: str, value: float) -> float:
    """High risk is always a high number, regardless of raw signal direction."""
    if signal not in SIGNAL_TO_FACTOR or not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError("invalid signal or value")
    return value if signal.endswith("_risk") else 1.0 - value


def sigmoid(value: float) -> float:
    if value >= 0:
        return 1.0 / (1.0 + math.exp(-value))
    e = math.exp(value)
    return e / (1.0 + e)


def calibrated_intercept(risks: list[float], rate: float, beta: float) -> float:
    """Match mean expected dropout to rate, separately for each signal column."""
    if not risks or not math.isfinite(rate) or not 0 < rate < 1:
        raise ValueError("risks must be nonempty and 0 < rate < 1")
    if not math.isfinite(beta) or beta < 0 or any(not math.isfinite(x) or not 0 <= x <= 1 for x in risks):
        raise ValueError("beta and risks must be finite; beta nonnegative; risks in [0,1]")
    if beta == 0:
        return math.log(rate / (1.0 - rate))
    lo, hi = -40.0 - beta, 40.0 + beta
    for _ in range(45):
        mid = (lo + hi) / 2.0
        mean = sum(sigmoid(mid + beta * (risk - 0.5)) for risk in risks) / len(risks)
        if mean < rate:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def load_rows(path: Path) -> list[tuple[bool, str, dict[str, float]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = [_validate_row(row) for row in csv.DictReader(handle)]
    if not rows or not any(safe for safe, _, _ in rows) or not any(not safe for safe, _, _ in rows):
        raise ValueError("input requires at least one safe and one unsafe observation")
    return rows


def calibrate(rows: list[tuple[bool, str, dict[str, float]]], rate: float,
              strengths: tuple[float, ...]) -> dict[float, dict[str, float]]:
    columns = {name: [risk_value(name, values[name]) for _, _, values in rows] for name in SIGNALS}
    return {
        beta: {name: calibrated_intercept(columns[name], rate, beta) for name in SIGNALS}
        for beta in strengths
    }


def run_seed(rows: list[tuple[bool, str, dict[str, float]]], *, seed: int,
             intercepts: dict[float, dict[str, float]]) -> dict[float, dict]:
    """Evaluate all strengths on shared uniform draws and all policies on shared masks."""
    rng = random.Random(seed)
    unsafe_scenarios = Counter(scenario for safe, scenario, _ in rows if not safe)
    states = {
        beta: {
            "counts": {policy: Counter() for policy in POLICIES},
            "missing": Counter(), "probe": {name: Counter() for name in PROBE_SIGNALS},
        }
        for beta in intercepts
    }
    for safe, scenario, signals in rows:
        uniforms = {name: rng.random() for name in SIGNALS}
        for beta, alpha in intercepts.items():
            state = states[beta]
            masked = {}
            for name in SIGNALS:
                risk = risk_value(name, signals[name])
                p = sigmoid(alpha[name] + beta * (risk - 0.5))
                missing = uniforms[name] < p
                if not missing:
                    masked[name] = signals[name]
                else:
                    state["missing"][name] += 1
                if name in PROBE_SIGNALS:
                    # Extreme bins are predeclared and need not cover all rows.
                    band = "high" if risk >= 0.70 else "low" if risk <= 0.30 else None
                    if band:
                        state["probe"][name][f"{band}_n"] += 1
                        state["probe"][name][f"{band}_missing"] += int(missing)
            for policy in POLICIES:
                _, decision, coverage = decide_partial(masked, policy)
                expected_coverage = sum(DEFAULT_WEIGHTS[SIGNAL_TO_FACTOR[name]] for name in masked)
                if not math.isclose(coverage, expected_coverage, abs_tol=1e-12):
                    raise AssertionError("coverage mismatch")
                c = state["counts"][policy]
                c[decision] += 1
                if not safe and decision == "ALLOW":
                    c["unsafe_allow"] += 1
                    c[f"scenario_allow:{scenario}"] += 1
                if safe and decision == "DENY":
                    c["safe_deny"] += 1
                if safe and decision == "STEP_UP":
                    c["safe_step_up"] += 1
                if safe and decision == "ALLOW":
                    c["safe_allow"] += 1
                if scenario == "identity_risk" and decision == "ALLOW":
                    c["identity_risk_allow"] += 1
    n_safe = sum(safe for safe, _, _ in rows)
    n_unsafe = len(rows) - n_safe
    out = {}
    for beta, state in states.items():
        out[beta] = {
            "seed": seed,
            "rows": len(rows), "safe_rows": n_safe, "unsafe_rows": n_unsafe,
            "observed_missing_fraction": sum(state["missing"].values()) / (len(rows) * len(SIGNALS)),
            "missing_by_signal": {name: state["missing"][name] / len(rows) for name in SIGNALS},
            "risk_conditioned_missingness": {
                name: {
                    band: {
                        "n": state["probe"][name][f"{band}_n"],
                        "missing": state["probe"][name][f"{band}_missing"],
                        "rate": state["probe"][name][f"{band}_missing"] / state["probe"][name][f"{band}_n"]
                        if state["probe"][name][f"{band}_n"] else None,
                    }
                    for band in ("low", "high")
                }
                for name in PROBE_SIGNALS
            },
            "policies": {
                policy: {
                    "unsafe_allow_count": state["counts"][policy]["unsafe_allow"],
                    "unsafe_allow_rate": state["counts"][policy]["unsafe_allow"] / n_unsafe,
                    "safe_deny_count": state["counts"][policy]["safe_deny"],
                    "safe_deny_rate": state["counts"][policy]["safe_deny"] / n_safe,
                    "safe_step_up_count": state["counts"][policy]["safe_step_up"],
                    "safe_step_up_rate": state["counts"][policy]["safe_step_up"] / n_safe,
                    "safe_allow_count": state["counts"][policy]["safe_allow"],
                    "safe_allow_rate": state["counts"][policy]["safe_allow"] / n_safe,
                    "identity_risk_allow_count": state["counts"][policy]["identity_risk_allow"],
                    "unsafe_allow_by_scenario": {
                        scenario: {
                            "unsafe_rows": denominator,
                            "allow_count": state["counts"][policy][f"scenario_allow:{scenario}"],
                            "allow_rate": state["counts"][policy][f"scenario_allow:{scenario}"] / denominator,
                        }
                        for scenario, denominator in sorted(unsafe_scenarios.items())
                    },
                    "decisions": {d: state["counts"][policy][d] for d in ("ALLOW", "STEP_UP", "DENY")},
                }
                for policy in POLICIES
            },
        }
    return out


def evaluate(input_path: Path, *, rate: float = .25,
             strengths: tuple[float, ...] = STRENGTHS,
             seeds: tuple[int, ...] = (20260904, 20260905, 20260906)) -> dict:
    if not seeds or len(set(seeds)) != len(seeds) or not strengths or len(set(strengths)) != len(strengths):
        raise ValueError("seeds and strengths must be nonempty and unique")
    rows = load_rows(input_path)
    intercepts = calibrate(rows, rate, strengths)
    per_seed = {str(seed): run_seed(rows, seed=seed, intercepts=intercepts) for seed in seeds}
    result = {
        "evidence_type": "synthetic-only; MNAR by stipulated value-dependent masking",
        "nominal_missing_rate_per_signal": rate,
        "strengths_log_odds_per_unit_risk": list(strengths),
        "seeds": list(seeds),
        "rows": len(rows),
        "calibrated_intercepts": {str(beta): intercepts[beta] for beta in strengths},
        "by_strength": {},
    }
    for beta in strengths:
        runs = [per_seed[str(seed)][beta] for seed in seeds]
        result["by_strength"][str(beta)] = {
            "mean_observed_missing_fraction": sum(r["observed_missing_fraction"] for r in runs) / len(runs),
            "seed_results": runs,
            "policy_rate_ranges": {
                policy: {
                    key: [min(r["policies"][policy][key] for r in runs),
                          max(r["policies"][policy][key] for r in runs)]
                    for key in ("unsafe_allow_rate", "safe_deny_rate", "safe_step_up_rate", "safe_allow_rate")
                }
                for policy in POLICIES
            },
        }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--rate", type=float, default=.25)
    parser.add_argument("--seeds", type=int, nargs="+", default=[20260904, 20260905, 20260906])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = evaluate(args.input, rate=args.rate, seeds=tuple(args.seeds))
    output = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output, end="")


if __name__ == "__main__":
    main()
