"""Paired correlated-telemetry-outage stress test on fixed synthetic observations.

No production telemetry. Missingness is MCAR marginally and jointly independent
of the underlying signal values, but dependent *between* signal indicators.
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
from trust_model import DEFAULT_WEIGHTS

SIGNALS = tuple(SIGNAL_TO_FACTOR)
POLICIES = ("renormalize", "neutral", "pessimistic", "step_up")
ENDPOINT = frozenset(("endpoint_health", "patch_posture", "security_coverage", "threat_risk", "anomaly_risk"))
ARMS = ("independent", "endpoint_rho_half", "endpoint_rho_one", "global_rho_one")


def load_rows(path: Path):
    rows = []
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("safe_for_ordinary_access") not in ("0", "1"):
                raise ValueError("safe_for_ordinary_access must be 0 or 1")
            vals = {}
            for name in SIGNALS:
                value = float(row[name])
                if not math.isfinite(value) or not 0 <= value <= 1:
                    raise ValueError(f"invalid signal {name}")
                vals[name] = value
            rows.append((row["safe_for_ordinary_access"] == "1", row.get("scenario", "unclassified"), vals))
    if not rows or not any(x[0] for x in rows) or all(x[0] for x in rows):
        raise ValueError("need both safe and unsafe rows")
    return rows


def make_masks(signals, independent_uniforms, shared_uniform, selector_uniform, rate):
    """Use identical base uniforms for all arms; common-mode switch is per row.

    For endpoint_rho_half, the endpoint group is common-mode with probability
    1/2 and otherwise independent. Thus pairwise mask correlation = 1/2 in
    expectation (not estimated from observations). Marginals remain rate.
    """
    if set(signals) != set(SIGNALS) or set(independent_uniforms) != set(SIGNALS):
        raise ValueError("expected exactly eight signals and draws")
    if not math.isfinite(rate) or not 0 < rate < 1:
        raise ValueError("rate must be finite and in (0,1)")
    if any(not math.isfinite(u) or not 0 <= u < 1 for u in (*independent_uniforms.values(), shared_uniform, selector_uniform)):
        raise ValueError("uniforms must be finite in [0,1)")
    def select(name, arm):
        if arm == "global_rho_one":
            return shared_uniform
        if name in ENDPOINT and (arm == "endpoint_rho_one" or
                                 (arm == "endpoint_rho_half" and selector_uniform < .5)):
            return shared_uniform
        return independent_uniforms[name]
    return {arm: {name: signals[name] for name in SIGNALS if select(name, arm) >= rate}
            for arm in ARMS}


def run_seed(rows, *, seed: int, rate: float):
    rng = random.Random(seed)
    n_safe = sum(safe for safe, _, _ in rows)
    n_unsafe = len(rows) - n_safe
    scenario_denoms = Counter(scenario for safe, scenario, _ in rows if not safe)
    states = {arm: {"decisions": {p: Counter() for p in POLICIES},
                    "missing": Counter(), "joint": Counter(),
                    "pair": Counter(), "flips": {p: Counter() for p in POLICIES}}
              for arm in ARMS}
    for safe, scenario, signals in rows:
        uniforms = {name: rng.random() for name in SIGNALS}
        shared = rng.random()
        selector = rng.random()
        masks = make_masks(signals, uniforms, shared, selector, rate)
        base = {}
        for arm in ARMS:
            mask = masks[arm]
            s = states[arm]
            missing = set(SIGNALS) - set(mask)
            s["missing"].update(missing)
            s["joint"]["all_missing"] += int(len(missing) == 8)
            s["joint"]["all_observed"] += int(not missing)
            s["joint"]["partial"] += int(0 < len(missing) < 8)
            s["pair"]["endpoint_joint"] += int("endpoint_health" in missing and "security_coverage" in missing)
            s["pair"]["endpoint_first"] += int("endpoint_health" in missing)
            s["pair"]["endpoint_second"] += int("security_coverage" in missing)
            for policy in POLICIES:
                _, decision, coverage = decide_partial(mask, policy)
                expected_coverage = sum(DEFAULT_WEIGHTS[SIGNAL_TO_FACTOR[name]] for name in mask)
                if not math.isclose(coverage, expected_coverage, abs_tol=1e-12):
                    raise AssertionError("coverage mismatch")
                c = s["decisions"][policy]
                c[decision] += 1
                if safe:
                    c["safe_" + decision.lower()] += 1
                elif decision == "ALLOW":
                    c["unsafe_allow"] += 1
                    c["scenario:" + scenario] += 1
                if arm == "independent":
                    base[policy] = decision
                else:
                    if base[policy] == "ALLOW" and decision != "ALLOW":
                        s["flips"][policy]["safe_allow_to_not" if safe else "unsafe_allow_to_not"] += 1
                    if base[policy] != "ALLOW" and decision == "ALLOW":
                        s["flips"][policy]["safe_not_to_allow" if safe else "unsafe_not_to_allow"] += 1
    out = {"seed": seed, "rows": len(rows), "safe_rows": n_safe, "unsafe_rows": n_unsafe, "arms": {}}
    for arm, s in states.items():
        p1 = s["pair"]["endpoint_first"] / len(rows)
        p2 = s["pair"]["endpoint_second"] / len(rows)
        joint = s["pair"]["endpoint_joint"] / len(rows)
        denom = math.sqrt(p1 * (1-p1) * p2 * (1-p2))
        arm_out = {"missing_fraction": sum(s["missing"].values()) / (len(rows)*len(SIGNALS)),
                   "missing_by_signal": {name: s["missing"][name] / len(rows) for name in SIGNALS},
                   "all_missing_fraction": s["joint"]["all_missing"] / len(rows),
                   "all_observed_fraction": s["joint"]["all_observed"] / len(rows),
                   "partial_fraction": s["joint"]["partial"] / len(rows),
                   "endpoint_pair_missing_phi": (joint-p1*p2)/denom if denom else None,
                   "policies": {}}
        for policy, c in s["decisions"].items():
            result = {"unsafe_allow_count": c["unsafe_allow"], "unsafe_allow_rate": c["unsafe_allow"]/n_unsafe,
                      "safe_allow_count": c["safe_allow"], "safe_allow_rate": c["safe_allow"]/n_safe,
                      "safe_deny_count": c["safe_deny"], "safe_deny_rate": c["safe_deny"]/n_safe,
                      "safe_step_up_count": c["safe_step_up"], "safe_step_up_rate": c["safe_step_up"]/n_safe,
                      "decisions": {d:c[d] for d in ("ALLOW","STEP_UP","DENY")},
                      "unsafe_allow_by_scenario": {name:{"unsafe_rows":denom,"allow_count":c["scenario:"+name],
                                                        "allow_rate":c["scenario:"+name]/denom}
                                                   for name,denom in sorted(scenario_denoms.items())}}
            if arm != "independent":
                flips = {k:s["flips"][policy][k] for k in ("unsafe_allow_to_not","unsafe_not_to_allow","safe_allow_to_not","safe_not_to_allow")}
                result["paired_allow_flips_vs_independent"] = flips
                baseline = states["independent"]["decisions"][policy]
                if c["unsafe_allow"]-baseline["unsafe_allow"] != flips["unsafe_not_to_allow"]-flips["unsafe_allow_to_not"]:
                    raise AssertionError("unsafe flip mismatch")
                if c["safe_allow"]-baseline["safe_allow"] != flips["safe_not_to_allow"]-flips["safe_allow_to_not"]:
                    raise AssertionError("safe flip mismatch")
            arm_out["policies"][policy] = result
        out["arms"][arm] = arm_out
    return out


def evaluate(path: Path, *, rate: float = .25, seeds=(20260904,20260905,20260906)):
    if not seeds or len(seeds) != len(set(seeds)):
        raise ValueError("seeds must be nonempty and unique")
    if not math.isfinite(rate) or not 0 < rate < 1:
        raise ValueError("rate must be in (0,1)")
    rows = load_rows(path)
    runs = [run_seed(rows, seed=seed, rate=rate) for seed in seeds]
    metrics = ("missing_fraction","all_missing_fraction","all_observed_fraction","endpoint_pair_missing_phi")
    outcome_metrics = ("unsafe_allow_rate","safe_allow_rate","safe_deny_rate","safe_step_up_rate")
    return {"evidence_type":"synthetic-only; correlated within-row MCAR masks", "input_rows":len(rows),
            "safe_rows":runs[0]["safe_rows"], "unsafe_rows":runs[0]["unsafe_rows"],
            "rate":rate, "seeds":list(seeds), "endpoint_group":sorted(ENDPOINT), "arms":list(ARMS),
            "summary":{arm:{**{m:sum(r["arms"][arm][m] for r in runs)/len(runs) for m in metrics},
                            "policies":{p:{m:sum(r["arms"][arm]["policies"][p][m] for r in runs)/len(runs)
                                           for m in outcome_metrics} for p in POLICIES}}
                       for arm in ARMS},
            "seed_results":runs}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input",type=Path,required=True)
    parser.add_argument("--rate",type=float,default=.25)
    parser.add_argument("--seeds",type=int,nargs="+",default=[20260904,20260905,20260906])
    parser.add_argument("--output",type=Path)
    args = parser.parse_args()
    result = evaluate(args.input,rate=args.rate,seeds=tuple(args.seeds))
    serialized = json.dumps(result,sort_keys=True,indent=2)+"\n"
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(serialized,encoding="utf-8")
    else:
        print(serialized,end="")

if __name__ == "__main__":
    main()
