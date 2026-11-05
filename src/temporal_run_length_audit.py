"""Right-censoring audit for stationary Markov missing-telemetry runs."""
import random

def simulate(n_devices=3000, steps=100, p=.25, rho=.8, seed=20261104):
    if not (0 < p < 1 and 0 <= rho < 1 and n_devices > 0 and steps > 1):
        raise ValueError("invalid simulation parameters")
    rng = random.Random(seed)
    a = p*(1-rho)
    b = p+rho*(1-p)
    completed, censored = [], []
    exits = exposure = 0
    for _ in range(n_devices):
        state = rng.random() < p
        length = int(state)
        for _ in range(1,steps):
            nxt = rng.random() < (b if state else a)
            if state:
                exposure += 1
                if not nxt:
                    exits += 1
                    completed.append(length)
                    length = 0
            if nxt:
                length = length+1 if state else 1
            state = nxt
        if state:
            censored.append(length)
    q_hat = exits/exposure
    return dict(completed_runs=len(completed),
                right_censored_runs=len(censored),
                completed_mean=sum(completed)/len(completed),
                transition_exit_probability=q_hat,
                transition_based_mean=1/q_hat,
                analytical_mean=1/((1-p)*(1-rho)),
                missing_exposure=exposure, exits=exits)

if __name__ == "__main__":
    import json
    print(json.dumps(simulate(),indent=2))
