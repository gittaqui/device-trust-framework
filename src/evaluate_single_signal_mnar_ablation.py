"""Paired single-signal MNAR ablations on the existing synthetic device-trust dataset.

This is an exploratory *simulation*, not evidence of real enterprise outages.
The baseline and all-eight arms reproduce evaluate_value_dependent_missingness.
"""
from __future__ import annotations

import argparse
import json
import math
import random
from collections import Counter
from pathlib import Path

from evaluate_missing_telemetry import decide_partial
from evaluate_value_dependent_missingness import (
    POLICIES, PROBE_SIGNALS, SIGNALS, calibrated_intercept, load_rows,
    risk_value, sigmoid,
)

ARMS = ("mcar", *PROBE_SIGNALS, "all_eight")


def calibrate_probe_intercepts(rows, *, rate: float, beta: float) -> dict[str, float]:
    if not math.isfinite(beta) or beta <= 0:
        raise ValueError("beta must be positive and finite")
    return {
        name: calibrated_intercept(
            [risk_value(name, signals[name]) for _, _, signals in rows], rate, beta
        )
        for name in SIGNALS
    }


def masks_for_arms(signals: dict[str, float], uniforms: dict[str, float],
                   *, rate: float, beta: float, intercepts: dict[str, float]) -> dict[str, dict[str, float]]:
    """Use one shared draw per signal; non-target signals retain identical masks."""
    if set(signals) != set(SIGNALS) or set(uniforms) != set(SIGNALS) or set(intercepts) != set(SIGNALS):
        raise ValueError("signals, uniforms and intercepts must contain exactly eight known signals")
    if not math.isfinite(rate) or not 0 < rate < 1 or not math.isfinite(beta) or beta <= 0:
        raise ValueError("invalid rate or beta")
    if any(not math.isfinite(u) or not 0 <= u < 1 for u in uniforms.values()):
        raise ValueError("uniform draws must lie in [0,1)")
    mcar = {name: signals[name] for name in SIGNALS if uniforms[name] >= rate}
    mnar = {
        name: signals[name] for name in SIGNALS
        if uniforms[name] >= sigmoid(intercepts[name] + beta * (risk_value(name, signals[name]) - .5))
    }
    arms = {"mcar": mcar}
    for target in PROBE_SIGNALS:
        arms[target] = {
            name: signals[name] for name in SIGNALS
            if (name in mnar if name == target else name in mcar)
        }
    arms["all_eight"] = mnar
    return arms


def run_seed(rows, *, seed: int, rate: float, beta: float,
             intercepts: dict[str, float]) -> dict:
    rng = random.Random(seed)
    n_safe = sum(safe for safe, _, _ in rows)
    n_unsafe = len(rows) - n_safe
    if not n_safe or not n_unsafe:
        raise ValueError("need both safe and unsafe synthetic observations")
    scenario_denominators = Counter(scenario for safe, scenario, _ in rows if not safe)
    counts = {arm: {policy: Counter() for policy in POLICIES} for arm in ARMS}
    missing = {arm: Counter() for arm in ARMS}
    probes = {arm: {signal: Counter() for signal in PROBE_SIGNALS} for arm in ARMS}
    flips = {arm: {policy: Counter() for policy in POLICIES} for arm in ARMS if arm != "mcar"}
    for safe, scenario, signals in rows:
        uniforms = {name: rng.random() for name in SIGNALS}
        masks = masks_for_arms(signals, uniforms, rate=rate, beta=beta, intercepts=intercepts)
        baseline = {}
        for arm in ARMS:
            masked = masks[arm]
            for name in SIGNALS:
                missing[arm][name] += int(name not in masked)
            for name in PROBE_SIGNALS:
                risk = risk_value(name, signals[name])
                band = "high" if risk >= .70 else "low" if risk <= .30 else None
                if band:
                    probes[arm][name][f"{band}_n"] += 1
                    probes[arm][name][f"{band}_missing"] += int(name not in masked)
            for policy in POLICIES:
                _, decision, _ = decide_partial(masked, policy)
                c = counts[arm][policy]
                c[decision] += 1
                if safe:
                    c[f"safe_{decision.lower()}"] += 1
                elif decision == "ALLOW":
                    c["unsafe_allow"] += 1
                    c[f"scenario:{scenario}"] += 1
                if arm == "mcar":
                    baseline[policy] = decision
                else:
                    b = baseline[policy] == "ALLOW"
                    a = decision == "ALLOW"
                    if b and not a:
                        flips[arm][policy]["safe_allow_to_not" if safe else "unsafe_allow_to_not"] += 1
                    if not b and a:
                        flips[arm][policy]["safe_not_to_allow" if safe else "unsafe_not_to_allow"] += 1
    out = {"seed": seed, "rows": len(rows), "safe_rows": n_safe, "unsafe_rows": n_unsafe, "arms": {}}
    for arm in ARMS:
        out_arm = {
            "missing_fraction": sum(missing[arm].values()) / (len(rows) * len(SIGNALS)),
            "missing_by_signal": {name: missing[arm][name] / len(rows) for name in SIGNALS},
            "risk_conditioned_missingness": {
                name: {
                    band: {"n": probes[arm][name][f"{band}_n"],
                           "missing": probes[arm][name][f"{band}_missing"],
                           "rate": (probes[arm][name][f"{band}_missing"] /
                                    probes[arm][name][f"{band}_n"]
                                    if probes[arm][name][f"{band}_n"] else None)}
                    for band in ("low", "high")
                }
                for name in PROBE_SIGNALS
            },
            "policies": {},
        }
        for policy in POLICIES:
            c = counts[arm][policy]
            p = {
                "unsafe_allow_count": c["unsafe_allow"],
                "unsafe_allow_rate": c["unsafe_allow"] / n_unsafe,
                "safe_allow_count": c["safe_allow"],
                "safe_allow_rate": c["safe_allow"] / n_safe,
                "safe_deny_count": c["safe_deny"],
                "safe_deny_rate": c["safe_deny"] / n_safe,
                "safe_step_up_count": c["safe_step_up"],
                "safe_step_up_rate": c["safe_step_up"] / n_safe,
                "decisions": {decision: c[decision] for decision in ("ALLOW", "STEP_UP", "DENY")},
                "unsafe_allow_by_scenario": {
                    scenario: {"unsafe_rows": denominator,
                               "allow_count": c[f"scenario:{scenario}"],
                               "allow_rate": c[f"scenario:{scenario}"] / denominator}
                    for scenario, denominator in sorted(scenario_denominators.items())
                },
            }
            if arm != "mcar":
                f = flips[arm][policy]
                p["paired_allow_flips_vs_mcar"] = {
                    key: f[key] for key in (
                        "unsafe_allow_to_not", "unsafe_not_to_allow",
                        "safe_allow_to_not", "safe_not_to_allow")
                }
                if c["unsafe_allow"] - counts["mcar"][policy]["unsafe_allow"] != (
                    f["unsafe_not_to_allow"] - f["unsafe_allow_to_not"]
                ):
                    raise AssertionError("paired unsafe-ALLOW flips do not reconcile")
            out_arm["policies"][policy] = p
        out["arms"][arm] = out_arm
    return out


def evaluate(input_path: Path, *, rate: float = .25, beta: float = 4.,
             seeds: tuple[int, ...] = (20260904, 20260905, 20260906)) -> dict:
    if not seeds or len(set(seeds)) != len(seeds):
        raise ValueError("seeds must be nonempty and unique")
    rows = load_rows(input_path)
    intercepts = calibrate_probe_intercepts(rows, rate=rate, beta=beta)
    runs = [run_seed(rows, seed=seed, rate=rate, beta=beta, intercepts=intercepts)
            for seed in seeds]
    summary = {}
    for arm in ARMS:
        summary[arm] = {
            "mean_observed_missing_fraction": sum(r["arms"][arm]["missing_fraction"] for r in runs) / len(runs),
            "policies": {
                policy: {
                    metric: {
                        "mean": sum(r["arms"][arm]["policies"][policy][metric] for r in runs) / len(runs),
                        "min": min(r["arms"][arm]["policies"][policy][metric] for r in runs),
                        "max": max(r["arms"][arm]["policies"][policy][metric] for r in runs),
                    }
                    for metric in ("unsafe_allow_rate", "safe_deny_rate", "safe_step_up_rate", "safe_allow_rate")
                }
                for policy in POLICIES
            },
        }
    return {
        "evidence_type": "synthetic-only; exploratory value-dependent masking ablation",
        "input_rows": len(rows), "safe_rows": runs[0]["safe_rows"], "unsafe_rows": runs[0]["unsafe_rows"],
        "nominal_expected_missing_fraction_per_column": rate,
        "beta_log_odds_per_unit_risk": beta,
        "seeds": list(seeds), "arms": list(ARMS),
        "calibrated_intercepts": intercepts,
        "summary": summary, "seed_results": runs,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--rate", type=float, default=.25)
    parser.add_argument("--beta", type=float, default=4.)
    parser.add_argument("--seeds", nargs="+", type=int, default=[20260904, 20260905, 20260906])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = evaluate(args.input, rate=args.rate, beta=args.beta, seeds=tuple(args.seeds))
    output = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output, end="")


if __name__ == "__main__":
    main()
