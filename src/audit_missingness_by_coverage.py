"""Coverage- and scenario-stratified paired missing-telemetry audit.

Research-only synthetic experiment. The generator's scenario labels are not
independently adjudicated security outcomes. No production policy is changed.

Reuses the frozen paired experiment's row validation, mask stream, and decision
functions. All strategies see the same masked observation; subgroup rates use
subgroup-specific label denominators and return null for absent labels.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path

from evaluate_missing_telemetry import STRATEGY_IDS, decide_partial, mask_signals
from evaluate_missing_telemetry_paired import _validate_row

COVERAGE_BINS = ("[0,0.50)", "[0.50,0.75)", "[0.75,1)", "1.00")
STRATEGIES = tuple(STRATEGY_IDS)


def coverage_bin(coverage: float) -> str:
    """Bins are left-closed, right-open except the singleton full-coverage bin."""
    if not math.isfinite(coverage) or not -1e-12 <= coverage <= 1 + 1e-12:
        raise ValueError("Coverage outside [0,1]")
    if coverage < 0.5:
        return COVERAGE_BINS[0]
    if coverage < 0.75:
        return COVERAGE_BINS[1]
    if coverage < 1 - 1e-12:
        return COVERAGE_BINS[2]
    return COVERAGE_BINS[3]


def _ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def _summarize(counter: Counter[str]) -> dict:
    n = counter["rows"]
    safe, unsafe = counter["safe"], counter["unsafe"]
    if n != safe + unsafe:
        raise AssertionError("Inconsistent label counts")
    result = {"rows": n, "safe": safe, "unsafe": unsafe, "strategies": {}}
    for strategy in STRATEGIES:
        d = counter
        allow = d[f"{strategy}:ALLOW"]
        deny = d[f"{strategy}:DENY"]
        step_up = d[f"{strategy}:STEP_UP"]
        if allow + deny + step_up != n:
            raise AssertionError("Decision totals do not reconcile")
        result["strategies"][strategy] = {
            "allow": allow,
            "deny": deny,
            "step_up": step_up,
            "false_allow": d[f"{strategy}:false_allow"],
            "false_deny": d[f"{strategy}:false_deny"],
            "safe_step_up": d[f"{strategy}:safe_step_up"],
            "false_allow_rate_unsafe": _ratio(d[f"{strategy}:false_allow"], unsafe),
            "false_deny_rate_safe": _ratio(d[f"{strategy}:false_deny"], safe),
            "safe_step_up_rate_safe": _ratio(d[f"{strategy}:safe_step_up"], safe),
        }
    return result


def audit_strata(
    input_path: Path, *, missing_rate: float = 0.25,
    structured: bool = True, seed: int = 20260904,
) -> dict:
    if not math.isfinite(missing_rate) or not 0 <= missing_rate <= 1:
        raise ValueError("missing_rate must be finite and within [0,1]")
    rng = random.Random(
        seed + round(missing_rate * 1_000_000) * 17
        + (1_000_000_000 if structured else 0)
    )
    groups: dict[str, dict[str, Counter[str]]] = defaultdict(lambda: defaultdict(Counter))
    observed_cells = total_cells = n = 0
    with input_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            safe, scenario, signals = _validate_row(row)
            masked = mask_signals(signals, rng, missing_rate, structured=structured)
            n += 1
            observed_cells += len(masked)
            total_cells += len(signals)
            decisions: dict[str, str] = {}
            coverages = []
            for strategy in STRATEGIES:
                _, decision, coverage = decide_partial(masked, strategy)
                decisions[strategy] = decision
                coverages.append(coverage)
            if not all(math.isclose(c, coverages[0], abs_tol=1e-12) for c in coverages):
                raise AssertionError("Telemetry coverage depends on strategy")
            bin_name = coverage_bin(coverages[0])
            group_keys = [
                ("overall", "all"),
                ("by_coverage", bin_name),
                ("by_scenario", scenario),
                ("by_scenario_coverage", f"{scenario}|{bin_name}"),
            ]
            # These synthetic scenarios have deterministic critical hard gates.
            # Gate presence is descriptive, not a randomized causal treatment.
            gate_signal = {
                "malware": "threat_risk",
                "protection_missing": "security_coverage",
            }.get(scenario)
            if gate_signal:
                presence = "observed" if gate_signal in masked else "missing"
                group_keys.append(("by_gate_presence", f"{scenario}|{presence}"))
            for dimension, key in group_keys:
                c = groups[dimension][key]
                c["rows"] += 1
                c["safe" if safe else "unsafe"] += 1
                for strategy, decision in decisions.items():
                    c[f"{strategy}:{decision}"] += 1
                    if not safe and decision == "ALLOW":
                        c[f"{strategy}:false_allow"] += 1
                    if safe and decision == "DENY":
                        c[f"{strategy}:false_deny"] += 1
                    if safe and decision == "STEP_UP":
                        c[f"{strategy}:safe_step_up"] += 1
    if not total_cells or not groups["overall"]["all"]["safe"] or not groups["overall"]["all"]["unsafe"]:
        raise ValueError("Evaluation needs at least one safe and one unsafe row")
    output = {
        "evidence_type": "synthetic-only",
        "input_rows": n,
        "mask_model": "critical_signal_biased" if structured else "mcar",
        "nominal_missing_rate": missing_rate,
        "observed_missing_fraction": (total_cells - observed_cells) / total_cells,
        "seed": seed,
        "coverage_bins": list(COVERAGE_BINS),
        "groups": {
            dimension: {key: _summarize(c) for key, c in sorted(items.items())}
            for dimension, items in sorted(groups.items())
        },
    }
    overall = output["groups"]["overall"]["all"]
    for dimension in ("by_coverage", "by_scenario", "by_scenario_coverage"):
        if sum(x["rows"] for x in output["groups"][dimension].values()) != overall["rows"]:
            raise AssertionError(f"Non-partitioning group: {dimension}")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--missing-rate", type=float, default=0.25)
    parser.add_argument("--structured", action="store_true")
    parser.add_argument("--seed", type=int, default=20260904)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit_strata(args.input, missing_rate=args.missing_rate,
                          structured=args.structured, seed=args.seed)
    serialized = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8")
    else:
        print(serialized, end="")


if __name__ == "__main__":
    main()
