"""Paired conditional unsafe-device bootstrap. Synthetic research only."""
import random

def paired_effect_conditional_unsafe(rows, replicates=2000, seed=20261109):
    rows = list(rows)
    if type(replicates) is not int or replicates < 2 or type(seed) is not int:
        raise ValueError("invalid replicates or seed")
    ids = []
    for r in rows:
        ids.append(r["device_id"])
        n = r["intervals"]
        if type(r["unsafe"]) is not bool or type(n) is not int or n < 1:
            raise ValueError("invalid label or intervals")
        for key in ("arm0_allow_count", "arm1_allow_count"):
            v = r[key]
            if type(v) is not int or not 0 <= v <= n:
                raise ValueError("invalid ALLOW count")
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate device identifiers")
    unsafe = [r for r in rows if r["unsafe"]]
    if len(unsafe) < 2:
        raise ValueError("need at least two unsafe devices")
    def effect(sample):
        return sum(r["arm1_allow_count"]-r["arm0_allow_count"] for r in sample) / sum(r["intervals"] for r in sample)
    rng = random.Random(seed)
    k = len(unsafe)
    draws = sorted(effect(rng.choices(unsafe, k=k)) for _ in range(replicates))
    def percentile(p):
        pos = p*(replicates-1)
        i = int(pos)
        frac = pos-i
        return draws[i]*(1-frac)+draws[min(i+1,replicates-1)]*frac
    return {"paired_difference":effect(unsafe), "ci_95_percentile":[percentile(.025),percentile(.975)],
            "devices":len(rows), "unsafe_devices":k, "defined_replicates":replicates,
            "undefined_replicates":0, "replicates":replicates, "seed":seed,
            "resampling_unit":"unsafe_device",
            "estimand":"interval_weighted_conditional_unsafe_allow_difference"}
