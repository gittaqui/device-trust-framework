"""Paired whole-device bootstrap for unsafe ordinary-ALLOW rates.

Records contain device_id, unsafe (bool), intervals, arm0_allow_count,
arm1_allow_count. Rates are interval-weighted among unsafe devices.
Only synthetic fixtures have been used for verification.
"""
import random


def paired_effect(rows, replicates=2000, seed=20261107):
    rows = list(rows)
    if len(rows) < 2 or type(replicates) is not int or replicates < 2:
        raise ValueError("need two devices and two bootstrap replicates")
    if len({r["device_id"] for r in rows}) != len(rows):
        raise ValueError("duplicate device identifiers")
    for r in rows:
        n = r["intervals"]
        if type(n) is not int or n < 1 or type(r["unsafe"]) is not bool:
            raise ValueError("invalid interval count or label")
        for k in ("arm0_allow_count", "arm1_allow_count"):
            if type(r[k]) is not int or not 0 <= r[k] <= n:
                raise ValueError("invalid ordinary-ALLOW count")
    unsafe = [r for r in rows if r["unsafe"]]
    if len(unsafe) < 2:
        raise ValueError("need two independently sampled unsafe devices")

    def difference(sample):
        eligible = [r for r in sample if r["unsafe"]]
        denominator = sum(r["intervals"] for r in eligible)
        if not denominator:
            return None
        return (sum(r["arm1_allow_count"] - r["arm0_allow_count"]
                    for r in eligible) / denominator)

    point = difference(rows)
    rng = random.Random(seed)
    draws = [difference(rng.choices(rows, k=len(rows)))
             for _ in range(replicates)]
    defined = sorted(x for x in draws if x is not None)
    if len(defined) < 2:
        raise ValueError("insufficient defined bootstrap replicates")

    def percentile(p):
        pos = p * (len(defined) - 1)
        lo = int(pos)
        frac = pos - lo
        return defined[lo] * (1 - frac) + defined[min(lo + 1, len(defined) - 1)] * frac

    return {"paired_difference": point,
            "ci_95_percentile": [percentile(.025), percentile(.975)],
            "devices": len(rows), "unsafe_devices": len(unsafe),
            "defined_replicates": len(defined),
            "undefined_replicates": len(draws) - len(defined),
            "replicates": replicates, "seed": seed}
