"""Monte Carlo coverage audit for conditional unsafe-device bootstrap.

Run: python -m experiments.conditional_bootstrap_coverage_2026_11_10
Synthetic methodological fixture; not endpoint telemetry.
"""
import json
import random
from src.conditional_unsafe_bootstrap import paired_effect_conditional_unsafe

def run(k, outer=300, inner=399, seed=20261110, variable=False):
    rng = random.Random(seed + k + int(variable)*1000)
    covered = 0
    widths = []
    estimates = []
    for trial in range(outer):
        rows = []
        for i in range(k):
            n = rng.choice((10, 20, 40)) if variable else 20
            difference = n if rng.random() < .3 else 0
            rows.append(dict(device_id=str(i), unsafe=True, intervals=n,
                             arm0_allow_count=0, arm1_allow_count=difference))
        result = paired_effect_conditional_unsafe(rows, replicates=inner, seed=seed+trial)
        lo, hi = result["ci_95_percentile"]
        covered += lo <= .3 <= hi
        widths.append(hi-lo)
        estimates.append(result["paired_difference"])
    coverage = covered / outer
    return dict(unsafe_devices=k, variable_intervals=variable, outer=outer,
                inner=inner, coverage=coverage, mean_width=sum(widths)/outer,
                mean_estimate=sum(estimates)/outer,
                mc_se=(coverage*(1-coverage)/outer)**.5)

if __name__ == "__main__":
    print(json.dumps({"design":"Synthetic two-point device effect; true effect 0.3; fixed 20 or independent variable 10/20/40 intervals",
                      "results":[run(k, variable=v) for k in (2,5,20,100) for v in (False,True)]}, indent=2))
