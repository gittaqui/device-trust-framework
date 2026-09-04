"""Explainable multidimensional device-trust model.

This is a research baseline, not a production access-control implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple


DEFAULT_WEIGHTS: Dict[str, float] = {
    "compliance": 0.18,
    "endpoint_health": 0.16,
    "identity_assurance": 0.16,
    "patch_posture": 0.12,
    "security_coverage": 0.16,
    "freshness": 0.08,
    "threat_safety": 0.08,
    "anomaly_safety": 0.06,
}


@dataclass(frozen=True)
class TrustDecision:
    score: float
    decision: str
    explanation: Dict[str, float]
    hard_gate: str | None = None


def _clip(value: float) -> float:
    """Clamp a normalized input to the inclusive [0, 1] range."""
    return max(0.0, min(1.0, float(value)))


def normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    """Normalize non-negative weights so they sum to one."""
    if any(value < 0 for value in weights.values()):
        raise ValueError("Weights must be non-negative.")

    total = sum(weights.values())
    if total <= 0:
        raise ValueError("At least one weight must be positive.")

    return {name: value / total for name, value in weights.items()}


def calculate_trust(
    signals: Dict[str, float],
    *,
    weights: Dict[str, float] | None = None,
    allow_threshold: float = 0.75,
    step_up_threshold: float = 0.55,
) -> TrustDecision:
    """Calculate an explainable device-trust decision.

    Risk inputs are converted into positive "safety" values so every weighted
    component has the same direction: higher is safer.
    """
    if step_up_threshold > allow_threshold:
        raise ValueError("step_up_threshold cannot exceed allow_threshold.")

    required = {
        "compliance",
        "endpoint_health",
        "identity_assurance",
        "patch_posture",
        "security_coverage",
        "freshness",
        "threat_risk",
        "anomaly_risk",
    }
    missing = required.difference(signals)
    if missing:
        raise ValueError(f"Missing required signals: {sorted(missing)}")

    values = {name: _clip(signals[name]) for name in required}

    # Catastrophic signals should not be hidden by a high weighted average.
    if values["threat_risk"] >= 0.90:
        return TrustDecision(
            score=0.0,
            decision="DENY",
            explanation={"critical_threat_risk": values["threat_risk"]},
            hard_gate="critical_threat_risk",
        )

    if values["security_coverage"] <= 0.15:
        return TrustDecision(
            score=0.0,
            decision="DENY",
            explanation={"critical_security_coverage": values["security_coverage"]},
            hard_gate="critical_security_coverage",
        )

    factors = {
        "compliance": values["compliance"],
        "endpoint_health": values["endpoint_health"],
        "identity_assurance": values["identity_assurance"],
        "patch_posture": values["patch_posture"],
        "security_coverage": values["security_coverage"],
        "freshness": values["freshness"],
        "threat_safety": 1.0 - values["threat_risk"],
        "anomaly_safety": 1.0 - values["anomaly_risk"],
    }

    normalized = normalize_weights(weights or DEFAULT_WEIGHTS)
    missing_weights = set(factors).difference(normalized)
    if missing_weights:
        raise ValueError(f"Missing weights: {sorted(missing_weights)}")

    contributions = {
        name: factors[name] * normalized[name]
        for name in factors
    }
    score = sum(contributions.values())

    if score >= allow_threshold:
        decision = "ALLOW"
    elif score >= step_up_threshold:
        decision = "STEP_UP"
    else:
        decision = "DENY"

    return TrustDecision(
        score=round(score, 6),
        decision=decision,
        explanation={name: round(value, 6) for name, value in contributions.items()},
    )


def binary_compliance_decision(compliance: float) -> str:
    """Simple comparison baseline: compliant => ALLOW, else DENY."""
    return "ALLOW" if _clip(compliance) >= 0.5 else "DENY"
