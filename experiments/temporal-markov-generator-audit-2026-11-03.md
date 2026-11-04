# Temporal outage generator implementation audit — 2026-11-03

## Starting point
Inspected the existing 2026-11-02 temporal outage protocol in this repository. The earlier document specifies stationary two-state Markov missingness but reports no executed simulation.

## Work completed
Implemented and locally tested a standard-library Python prototype of the Markov mask generator. This audit records the exact algorithm and results. The generator is not yet integrated with the repository's trust decision engine.

For each device, independently initialize missing state M[0] as Bernoulli(p). For each subsequent time step, sample M[t+1] using:
- P(1|0) = p(1-rho)
- P(1|1) = p + rho(1-p)

Use an independently initialized chain for every device; never count a transition between devices. Record 00, 01, 10, and 11 transitions. Compute empirical missingness and conditional transition probabilities. A fixed pseudorandom seed ensures deterministic reproduction.

## Local executable prototype
```python
import random
from collections import Counter

def generate(devices=3000, steps=100, p=0.25, rho=0.8, seed=20260904):
    if devices < 1 or steps < 2 or not (0 < p < 1 and 0 <= rho < 1):
        raise ValueError("invalid parameters")
    rng = random.Random(seed)
    counts = Counter()
    missing = 0
    for _ in range(devices):
        state = int(rng.random() < p)
        for t in range(steps):
            missing += state
            if t + 1 < steps:
                next_state = int(rng.random() < (p + rho*(1-p) if state else p*(1-rho)))
                counts[(state, next_state)] += 1
                state = next_state
    return {
        "missing_fraction": missing/(devices*steps),
        "p01": counts[(0,1)]/(counts[(0,0)]+counts[(0,1)]),
        "p11": counts[(1,1)]/(counts[(1,0)]+counts[(1,1)]),
        "transitions": dict((str(k),v) for k,v in counts.items())
    }

if __name__ == "__main__":
    print(generate())
```

## Results — synthetic generator verification only
3000 independent simulated devices, 100 steps each, p=0.25, rho=0.8, seed=20260904:
- Realized missing fraction: 0.24758 (target 0.25).
- Estimated P(1|0): 0.0498852210 (theoretical 0.05).
- Estimated P(1|1): 0.8479742136 (theoretical 0.85).
- Transition counts: 00=212325, 01=11148, 10=11178, 11=62349. Sum=297000=3000*(100-1).
- Theoretical complete missing-run duration: 6.6667 steps. The prototype's observed *terminated-run* mean was 6.1763 steps; this is biased downward by finite-window boundary truncation/censoring and must not be presented as an unbiased duration estimate.

## Deterministic verification
Five local Python unittest cases passed after fixing an initial command-line argument-name mismatch. Tests covered stationary probability identities, invalid parameters, deterministic seeds, transition estimates for rho=0,0.5,0.8,0.95, and prevention of cross-device transitions. A second local run of the CLI completed successfully. The first CLI invocation failed because it passed 'devices' to a function expecting 'n_devices'; this was corrected and rerun. Full repository CI and manuscript compilation were **not** run.

## Literature context
Fresh source check: IEEE Transactions on Power Systems (2016), *A Continuous Time Markov Chain Based Sequential Analytical Approach for Composite Power System Reliability Assessment*, DOI 10.1109/TPWRS.2015.2392103. Its publisher record supports Markov modeling for outage frequency and duration, but not the validity of this discrete-time endpoint telemetry model. Do not import bibliographic metadata or claim domain validation without further verification.

## Limitations and next step
All data are synthetic. The prototype generates only missingness masks; it has not been connected to the existing eight-factor decision model. It does not estimate access-control error, and its artificial device sequences do not represent real endpoint histories. Next: integrate the generator with the frozen synthetic observations and four decision policies, explicitly handle right/left censoring for outage duration, then perform device-cluster-aware paired inference. No employer telemetry was accessed.
