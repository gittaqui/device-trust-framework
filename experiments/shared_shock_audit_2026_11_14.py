"""Synthetic shared-outage audit; no endpoint telemetry or trust-engine claims."""
import math
import random


def simulate(seed=20261114, datasets=1000, devices=100, episodes=10, rho=0.5):
    """Coverage of naive device-mean normal CI under crossed common episode shocks.

    Each device has one observation in each independent episode. The estimand is
    zero; outcomes are Gaussian with common episode and idiosyncratic shocks.
    rho is the fraction of per-observation variance from the common shock.
    """
    if not (0 <= rho <= 1) or min(datasets, devices, episodes) < 2:
        raise ValueError('invalid design')
    rng = random.Random(seed)
    hits = 0
    for _ in range(datasets):
        common = [rng.gauss(0, math.sqrt(rho)) for _ in range(episodes)]
        means = [sum(common[t] + rng.gauss(0, math.sqrt(1-rho))
                     for t in range(episodes))/episodes for _ in range(devices)]
        estimate = sum(means)/devices
        variance = sum((x-estimate)**2 for x in means)/(devices-1)
        half_width = 1.96*math.sqrt(variance/devices)
        hits += abs(estimate) <= half_width
    return hits/datasets


def analytic_variance(devices=100, episodes=10, rho=0.5):
    """Var(grand mean), and expected naive device-mean variance estimate."""
    if devices < 2 or episodes < 1 or not 0 <= rho <= 1:
        raise ValueError('invalid design')
    true = rho/episodes + (1-rho)/(devices*episodes)
    naive = (1-rho)/(devices*episodes)
    return true, naive


if __name__ == '__main__':
    for rho in (0, 0.1, 0.5):
        truth, naive = analytic_variance(rho=rho)
        print(f'rho={rho:.1f} true_var={truth:.6f} naive_var={naive:.6f} '
              f'coverage={simulate(rho=rho):.3f}')
