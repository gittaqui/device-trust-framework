"""Exact AR(1) finite-sample variance oracle and Bartlett truncation audit.
Synthetic mathematical model, not endpoint evidence. Standard library only.
"""
import math


def exact_vif(n: int, phi: float) -> float:
    if n < 2 or not math.isfinite(phi) or abs(phi) >= 1:
        raise ValueError('n>=2 and finite |phi|<1 required')
    return 1 + 2 * sum((1-k/n)*phi**k for k in range(1,n))


def bartlett_population_vif(n: int, phi: float, bandwidth: int) -> float:
    """Oracle Bartlett-weighted long-run variance, using known mean/covariances.

    This is NOT the expected value of a sample-mean-centered Newey-West
    estimator; it isolates truncation and taper bias from estimation noise.
    """
    exact_vif(n, phi)
    if not isinstance(bandwidth, int) or not 0 <= bandwidth < n:
        raise ValueError('bandwidth must be integer in [0,n)')
    return 1 + 2 * sum((1-k/(bandwidth+1))*phi**k for k in range(1,bandwidth+1))


def audit():
    return [(n, phi, lag, exact_vif(n,phi), bartlett_population_vif(n,phi,lag))
            for n in (10,30,100) for phi in (0.0,0.3,0.6,0.9)
            for lag in (0, min(3,n-1), min(8,n-1))]


if __name__ == '__main__':
    print('episodes,phi,bandwidth,exact_vif,bartlett_oracle_vif,ratio')
    for n, phi, lag, truth, approx in audit():
        print(f'{n},{phi:.1f},{lag},{truth:.6f},{approx:.6f},{approx/truth:.6f}')
