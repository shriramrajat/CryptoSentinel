"""
Harvest-Now-Decrypt-Later (HNDL) Analyzer for CryptoSentinel Phase 2.

Evaluates whether a cryptographic asset poses a Harvest-Now-Decrypt-Later exposure risk
based on primitive capability (asymmetric confidentiality / key exchange vs signature),
data sensitivity, data lifetime, and network exposure.
"""

from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, Any, List, Optional

from ecdat.config_policy import RiskPolicyConfig
from ecdat.context import AssetContext, DataSensitivity
from ecdat.models import CryptoAsset
from ecdat.quantum import QuantumThreatType, evaluate_quantum_threat


class HNDLStatus(str, Enum):
    """HNDL Exposure classification status."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class HNDLAssessment:
    """Structured Harvest-Now-Decrypt-Later assessment result."""
    status: HNDLStatus
    is_confidentiality_primitive: bool
    is_shor_vulnerable: bool
    reasons: List[str]
    exposure_summary: str

    def to_dict(self) -> Dict[str, Any]:
        res = asdict(self)
        res["status"] = self.status.value
        return res


CONFIDENTIALITY_CATEGORIES = {
    "asymmetric_encryption",
    "key_exchange",
    "hybrid_encryption",
    "certificate_or_key",
}

CONFIDENTIALITY_ALGORITHMS = {
    "RSA",
    "ECDH",
    "DH",
    "DIFFIE-HELLMAN",
    "ECC",
    "EC",
}

HIGH_SENSITIVITY_LEVELS = {
    DataSensitivity.HIGH,
    DataSensitivity.CONFIDENTIAL,
    DataSensitivity.RESTRICTED,
    DataSensitivity.CRITICAL,
    "HIGH",
    "CONFIDENTIAL",
    "RESTRICTED",
    "CRITICAL",
}


def evaluate_hndl_risk(
    asset: CryptoAsset,
    context: AssetContext,
    policy: Optional[RiskPolicyConfig] = None,
) -> HNDLAssessment:
    """Evaluates Harvest-Now-Decrypt-Later (HNDL) exposure for an asset given its context and policy.
    
    HNDL strictly requires:
    1. Quantum-vulnerable asymmetric primitive used for confidentiality/key-exchange (Shor target).
    2. Long-lived data secrecy requirements.
    3. High sensitivity / internet exposure.
    
    If data sensitivity or lifetime is UNKNOWN, HNDL status remains UNKNOWN.
    """
    if policy is None:
        policy = RiskPolicyConfig()

    algo = asset.algorithm.strip().upper()
    cat = asset.category.strip().lower()
    qt = evaluate_quantum_threat(algo, asset.key_length)

    is_shor = (qt.threat_type == QuantumThreatType.SHOR)

    # Determine if asset is used for confidentiality or key exchange
    is_confidentiality = (
        cat in CONFIDENTIALITY_CATEGORIES or
        (algo in CONFIDENTIALITY_ALGORITHMS and cat != "digital_signature")
    )

    reasons: List[str] = []

    # Non-Shor or non-confidentiality primitives (e.g. signatures or symmetric hashes) are NOT HNDL targets
    if not is_shor or not is_confidentiality:
        if not is_shor:
            reasons.append(f"{asset.algorithm} is not vulnerable to Shor's algorithm for public-key decryption.")
        if not is_confidentiality:
            reasons.append(f"Asset category '{asset.category}' is used for authentication/signatures, not data confidentiality.")

        return HNDLAssessment(
            status=HNDLStatus.NOT_APPLICABLE,
            is_confidentiality_primitive=is_confidentiality,
            is_shor_vulnerable=is_shor,
            reasons=reasons,
            exposure_summary="Not an HNDL candidate (primitive is symmetric or signature-only).",
        )

    # Shor-vulnerable confidentiality/key-exchange primitive! Evaluate context.
    reasons.append(f"{asset.algorithm} is an asymmetric primitive vulnerable to Shor's algorithm decryption.")

    sens_obj = context.data_sensitivity.value
    sensitivity_str = sens_obj.value if isinstance(sens_obj, Enum) else str(sens_obj)

    lifetime = context.data_lifetime_years.value
    exposed = context.internet_exposed.value

    # Check for missing context
    if sensitivity_str == "UNKNOWN" or lifetime is None:
        missing_fields = []
        if sensitivity_str == "UNKNOWN":
            missing_fields.append("data_sensitivity")
        if lifetime is None:
            missing_fields.append("data_lifetime_years")

        reasons.append(f"HNDL evaluation incomplete because context fields are UNKNOWN: {', '.join(missing_fields)}.")

        return HNDLAssessment(
            status=HNDLStatus.UNKNOWN,
            is_confidentiality_primitive=True,
            is_shor_vulnerable=True,
            reasons=reasons,
            exposure_summary="HNDL status is UNKNOWN due to missing data lifetime or sensitivity context.",
        )

    # Context is present! Perform deterministic classification.
    is_high_sensitivity = (sens_obj in HIGH_SENSITIVITY_LEVELS or sensitivity_str in HIGH_SENSITIVITY_LEVELS)
    is_long_lifetime = (lifetime >= policy.hndl_min_lifetime_years)

    if is_high_sensitivity and is_long_lifetime:
        if exposed is True:
            status = HNDLStatus.CRITICAL
            summary = "CRITICAL HNDL risk: Internet-exposed service encrypting/exchanging key for highly sensitive, long-lived data using quantum-vulnerable algorithm."
            reasons.append("Internet exposure enables passive adversary signal intelligence harvesting.")
        else:
            status = HNDLStatus.HIGH
            summary = "HIGH HNDL risk: Encrypting/exchanging key for highly sensitive, long-lived data using quantum-vulnerable algorithm."

        reasons.append(f"Data sensitivity is {sensitivity_str} and protected data lifetime is {lifetime} years (>= threshold {policy.hndl_min_lifetime_years} years).")
    elif is_high_sensitivity or is_long_lifetime:
        status = HNDLStatus.MEDIUM
        summary = "MEDIUM HNDL risk: Moderate confidentiality horizon or sensitivity requirement."
        reasons.append(f"Data sensitivity is {sensitivity_str}, lifetime is {lifetime} years.")
    else:
        status = HNDLStatus.LOW
        summary = "LOW HNDL risk: Short data lifetime or low sensitivity reduces harvest-and-decrypt threat."
        reasons.append(f"Protected data has low sensitivity ({sensitivity_str}) or short lifetime ({lifetime} years).")

    return HNDLAssessment(
        status=status,
        is_confidentiality_primitive=True,
        is_shor_vulnerable=True,
        reasons=reasons,
        exposure_summary=summary,
    )
