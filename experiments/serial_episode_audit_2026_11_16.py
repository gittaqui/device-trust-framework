"""Exact Gaussian coverage of episode-normal intervals under AR(1) common shocks.
Synthetic mathematical audit; no endpoint observations. Standard library only.
"""
import math
from statistics import NormalDist

def variance_inflation(episodes: int, phi: float) -> float:
    """Var(mean) / (marginal variance / episodes) for stationary AR(1)."""
    if episodes < 2 or not math.isfinite(phi) or abs(phi) >= 1:
        raise ValueError("episodes >= 2 and |phi| < 1 required")
    return 1 + 2 * sum((1 - k / episodes) * phi ** k for k in range(1, episodes))

def normal_reference_coverage(episodes: int, phi: float, critical: float = 1.96) -> float:
    """Known-marginal-variance normal-reference coverage, NOT Student-t coverage."""
    if not math.isfinite(critical) or critical <= 0:
        raise ValueError("positive critical required")
    return 2 * NormalDist().cdf(critical / math.sqrt(variance_inflation(episodes, phi))) - 1

def audit():
    return [(phi, variance_inflation(10, phi), normal_reference_coverage(10, phi))
            for phi in (0.0, 0.3, 0.6, 0.9)]

if __name__ == "__main__":
    for phi, vif, coverage in audit():
        print(f"phi={phi:.1f} variance_inflation={vif:.6f} normal_reference_coverage={coverage:.6%}")
