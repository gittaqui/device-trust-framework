"""Synthetic crossed-episode coverage audit; no endpoint data. Python standard library."""
import math
import random

def episode_interval(means, critical=2.2621571627409915):
    """95% t interval for exactly ten independent Gaussian episode means (df=9)."""
    if len(means) != 10 or not all(math.isfinite(x) for x in means):
        raise ValueError("requires ten finite episode means")
    center = sum(means)/10
    variance = sum((x-center)**2 for x in means)/9
    margin = critical*math.sqrt(variance/10)
    return center-margin, center+margin

def simulate(seed=20261115, datasets=2000, devices=100, episodes=10, rho=0.5):
    """Coverage under Y_it=sqrt(rho)*U_t+sqrt(1-rho)*E_it; truth=0."""
    if datasets < 1 or devices < 2 or episodes != 10 or not 0 <= rho <= 1:
        raise ValueError("invalid design")
    rng = random.Random(seed)
    episode_hits = naive_hits = 0
    for _ in range(datasets):
        common = [rng.gauss(0, math.sqrt(rho)) for _ in range(episodes)]
        device_sums = [0.0]*devices
        episode_sums = [0.0]*episodes
        for i in range(devices):
            for t in range(episodes):
                y = common[t]+rng.gauss(0, math.sqrt(1-rho))
                device_sums[i] += y
                episode_sums[t] += y
        dm = [x/episodes for x in device_sums]
        em = [x/devices for x in episode_sums]
        estimate = sum(dm)/devices
        naive_var = sum((x-estimate)**2 for x in dm)/(devices-1)/devices
        naive_hits += abs(estimate) <= 1.96*math.sqrt(naive_var)
        lo, hi = episode_interval(em)
        episode_hits += lo <= 0 <= hi
    return {"naive_coverage":naive_hits/datasets,
            "episode_t_coverage":episode_hits/datasets,
            "datasets":datasets,"devices":devices,"episodes":episodes,
            "rho":rho,"seed":seed}

if __name__ == "__main__":
    for rho in (0.0,0.1,0.5):
        print(simulate(rho=rho))
