"""
Mosca-Style Cryptographic Lifecycle Analysis for CryptoSentinel Phase 2.

Implements deterministic Mosca-style evaluation evaluating data confidentiality lifetime (C),
migration lead time (M), and quantum threat horizon (Y): C + M > Y.
"""

from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, Any, Optional

from ecdat.config_policy import RiskPolicyConfig
from ecdat.context import AssetContext


class LifecycleUrgency(str, Enum):
    """Urgency level derived from Mosca-style lifecycle analysis."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class MoscaLifecycleAssessment:
    """Structured result of Mosca-style cryptographic lifecycle analysis."""
    urgency: LifecycleUrgency
    data_lifetime_years: Optional[float]
    migration_lead_time_years: float
    quantum_horizon_years: float
    protection_horizon_years: Optional[float]
    safety_margin_years: Optional[float]
    formula: str
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        res = asdict(self)
        res["urgency"] = self.urgency.value
        return res


def evaluate_lifecycle_urgency(
    context: AssetContext,
    policy: Optional[RiskPolicyConfig] = None,
) -> MoscaLifecycleAssessment:
    """Evaluates cryptographic lifecycle urgency using Mosca's equation: C + M > Y.
    
    Variables:
      C = Data Lifetime / Confidentiality Requirement (in years)
      M = Migration Lead Time (in years)
      Y = Quantum Threat Horizon (in years)
      Protection Horizon P = C + M
      Safety Margin Delta = Y - P = Y - (C + M)
    """
    if policy is None:
        policy = RiskPolicyConfig()

    y = policy.quantum_horizon_years
    m = policy.default_migration_lead_time_years
    c_field = context.data_lifetime_years
    c = c_field.value if (c_field and c_field.value is not None) else None

    # Handle UNKNOWN data lifetime
    if c is None:
        return MoscaLifecycleAssessment(
            urgency=LifecycleUrgency.UNKNOWN,
            data_lifetime_years=None,
            migration_lead_time_years=m,
            quantum_horizon_years=y,
            protection_horizon_years=None,
            safety_margin_years=None,
            formula="C + M vs Y (C is UNKNOWN)",
            explanation="Data protection lifetime (C) is UNKNOWN. Lifecycle urgency cannot be determined without data lifetime context.",
        )

    protection_horizon = c + m
    safety_margin = y - protection_horizon

    formula_str = f"P ({c}y data + {m}y migration = {protection_horizon}y) vs Y ({y}y quantum horizon)"

    # Urgency Classification
    if protection_horizon > y:
        deficit = protection_horizon - y
        if deficit >= 5.0:
            urgency = LifecycleUrgency.CRITICAL
            exp = (
                f"CRITICAL: Protection horizon ({protection_horizon:.1f} yrs) exceeds quantum horizon ({y:.1f} yrs) "
                f"by {deficit:.1f} years! Data will remain exposed to quantum cryptanalysis before migration completes."
            )
        else:
            urgency = LifecycleUrgency.HIGH
            exp = (
                f"HIGH: Protection horizon ({protection_horizon:.1f} yrs) exceeds quantum horizon ({y:.1f} yrs) "
                f"by {deficit:.1f} years. Active migration planning must commence immediately."
            )
    elif safety_margin <= 2.0:
        urgency = LifecycleUrgency.MODERATE
        exp = (
            f"MODERATE: Safety margin ({safety_margin:.1f} yrs) is narrow. "
            f"Protection horizon ({protection_horizon:.1f} yrs) approaches quantum horizon ({y:.1f} yrs)."
        )
    else:
        urgency = LifecycleUrgency.LOW
        exp = (
            f"LOW: Sufficient safety margin ({safety_margin:.1f} yrs) exists before quantum horizon ({y:.1f} yrs)."
        )

    return MoscaLifecycleAssessment(
        urgency=urgency,
        data_lifetime_years=c,
        migration_lead_time_years=m,
        quantum_horizon_years=y,
        protection_horizon_years=protection_horizon,
        safety_margin_years=safety_margin,
        formula=formula_str,
        explanation=exp,
    )
