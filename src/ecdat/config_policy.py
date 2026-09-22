"""
Configurable Risk Policy for CryptoSentinel Phase 2.

Defines configurable assumptions for quantum planning horizon, migration lead times,
data sensitivity thresholds, and lifecycle risk parameters.
"""

from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional


@dataclass
class RiskPolicyConfig:
    """Configurable risk assumptions and planning thresholds.
    
    Attributes:
        quantum_horizon_years (float): Estimated quantum planning horizon Y (default: 10.0 years).
        default_migration_lead_time_years (float): Expected migration lead time M (default: 3.0 years).
        hndl_sensitivity_threshold (str): Minimum data sensitivity level triggering HNDL concern.
        hndl_min_lifetime_years (float): Minimum data lifetime triggering HNDL concern (default: 5.0 years).
    """
    quantum_horizon_years: float = 10.0
    default_migration_lead_time_years: float = 3.0
    hndl_sensitivity_threshold: str = "HIGH"
    hndl_min_lifetime_years: float = 5.0

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """Validate configuration values."""
        if self.quantum_horizon_years <= 0:
            raise ValueError("quantum_horizon_years must be greater than 0")
        if self.default_migration_lead_time_years < 0:
            raise ValueError("default_migration_lead_time_years must be non-negative")
        if self.hndl_min_lifetime_years < 0:
            raise ValueError("hndl_min_lifetime_years must be non-negative")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]] = None) -> "RiskPolicyConfig":
        if not data:
            return cls()
        config = cls(
            quantum_horizon_years=float(data.get("quantum_horizon_years", 10.0)),
            default_migration_lead_time_years=float(data.get("default_migration_lead_time_years", 3.0)),
            hndl_sensitivity_threshold=str(data.get("hndl_sensitivity_threshold", "HIGH")).upper(),
            hndl_min_lifetime_years=float(data.get("hndl_min_lifetime_years", 5.0)),
        )
        config.validate()
        return config
