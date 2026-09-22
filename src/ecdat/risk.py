"""Deterministic risk classification and explainability engine for CryptoSentinel Phase 2."""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional

from ecdat.config_policy import RiskPolicyConfig
from ecdat.context import AssetContext, BusinessCriticality, DataSensitivity
from ecdat.hndl import HNDLAssessment, HNDLStatus, evaluate_hndl_risk
from ecdat.lifecycle import LifecycleUrgency, MoscaLifecycleAssessment, evaluate_lifecycle_urgency
from ecdat.models import CryptoAsset
from ecdat.quantum import QuantumThreatAssessment, QuantumThreatType, evaluate_quantum_threat


RSA_MINIMUM_KEY_LENGTH = 2048


class RiskSeverity(str, Enum):
    """Risk levels assigned from evidence and context."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"
    UNKNOWN = "unknown"


class QuantumThreat(str, Enum):
    """Specific quantum computing threat type (backward compatible enum)."""
    SHOR = "shor"
    GROVER = "grover"
    NONE = "none"


@dataclass(frozen=True)
class PQCRecommendation:
    """Structured Post-Quantum Cryptography migration recommendation."""
    target_algorithm: str
    nist_standard: str
    migration_type: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class RiskAssessment:
    """Structured, secret-free interpretation of one cryptographic asset (Phase 1 backward compatible)."""
    asset_id: str
    severity: RiskSeverity
    reason: str
    confidence: float
    quantum_threat: QuantumThreat
    pqc_recommendation: Optional[PQCRecommendation] = None

    def to_dict(self) -> dict:
        """Return a serialization-friendly representation."""
        result = asdict(self)
        result["severity"] = self.severity.value
        result["quantum_threat"] = self.quantum_threat.value
        if self.pqc_recommendation:
            result["pqc_recommendation"] = self.pqc_recommendation.to_dict()
        return result


@dataclass
class RiskExplanation:
    """Fact-based explainability structure explaining why, why now, and what to plan."""
    what: str
    where: str
    context_summary: Dict[str, Any]
    why_vulnerable: List[str]
    why_now: List[str]
    missing_information: List[str]
    recommendations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class QuantumRiskAssessment:
    """Multi-dimensional, uncertainty-aware Phase 2 cryptographic risk intelligence assessment."""
    asset_id: str
    technical_quantum_risk: RiskSeverity
    quantum_threat: QuantumThreatAssessment
    hndl_assessment: HNDLAssessment
    lifecycle_assessment: MoscaLifecycleAssessment
    context_criticality: BusinessCriticality
    business_urgency: RiskSeverity
    overall_priority: str  # "IMMEDIATE_ACTION", "PLANNING_REQUIRED", "NEEDS_CONTEXT", "MONITOR", "LOW_PRIORITY"
    reasons: List[str]
    assumptions: Dict[str, Any]
    confidence: float
    explanation: RiskExplanation
    pqc_recommendation: Optional[PQCRecommendation] = None
    calculated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "technical_quantum_risk": self.technical_quantum_risk.value,
            "quantum_threat": self.quantum_threat.to_dict(),
            "hndl_assessment": self.hndl_assessment.to_dict(),
            "lifecycle_assessment": self.lifecycle_assessment.to_dict(),
            "context_criticality": self.context_criticality.value if hasattr(self.context_criticality, "value") else str(self.context_criticality),
            "business_urgency": self.business_urgency.value if hasattr(self.business_urgency, "value") else str(self.business_urgency),
            "overall_priority": self.overall_priority,
            "reasons": self.reasons,
            "assumptions": self.assumptions,
            "confidence": round(self.confidence, 2),
            "explanation": self.explanation.to_dict(),
            "pqc_recommendation": self.pqc_recommendation.to_dict() if self.pqc_recommendation else None,
            "calculated_at": self.calculated_at,
        }


def _assessment(
    asset_id: str,
    severity: RiskSeverity,
    reason: str,
    confidence: float,
    quantum_threat: QuantumThreat = QuantumThreat.NONE,
    pqc_recommendation: Optional[PQCRecommendation] = None,
) -> RiskAssessment:
    return RiskAssessment(
        asset_id=asset_id,
        severity=severity,
        reason=reason,
        confidence=max(0.0, min(round(confidence, 2), 1.0)),
        quantum_threat=quantum_threat,
        pqc_recommendation=pqc_recommendation,
    )


def classify_asset(asset: CryptoAsset) -> RiskAssessment:
    """Phase 1 backward compatible classifier."""
    algorithm = asset.algorithm.strip().upper()
    category = asset.category.strip().lower()
    confidence = asset.confidence
    aid = asset.asset_id

    if category == "hardcoded_secret" or algorithm == "SECRET":
        return _assessment(
            asset_id=aid,
            severity=RiskSeverity.CRITICAL,
            reason="A hardcoded secret was detected in source code.",
            confidence=confidence,
            quantum_threat=QuantumThreat.NONE,
        )

    if algorithm in {"MD5", "SHA-1", "SHA1"}:
        return _assessment(
            asset_id=aid,
            severity=RiskSeverity.HIGH,
            reason=f"{asset.algorithm} is a legacy or cryptographically weak hashing primitive.",
            confidence=confidence,
            quantum_threat=QuantumThreat.NONE,
            pqc_recommendation=PQCRecommendation("SHA-256 / SHA-3-256", "FIPS 180-4 / FIPS 202", "Direct Replacement")
        )

    if algorithm in {"DES", "3DES", "TRIPLE-DES", "RC4"}:
        return _assessment(
            asset_id=aid,
            severity=RiskSeverity.HIGH,
            reason=f"{asset.algorithm} is a deprecated legacy symmetric primitive.",
            confidence=confidence,
            quantum_threat=QuantumThreat.NONE,
            pqc_recommendation=PQCRecommendation("AES-256-GCM", "FIPS 197", "Direct Replacement")
        )

    if algorithm in {"RSA", "ECC", "EC", "DSA", "DH", "ECDSA", "ECDH"}:
        rec = get_pqc_recommendation(algorithm, category)

        if algorithm == "RSA" and asset.key_length is not None and asset.key_length < RSA_MINIMUM_KEY_LENGTH:
            return _assessment(
                asset_id=aid,
                severity=RiskSeverity.CRITICAL,
                reason=f"RSA key length {asset.key_length} is below the {RSA_MINIMUM_KEY_LENGTH} bit minimum and is vulnerable to Shor's algorithm.",
                confidence=confidence,
                quantum_threat=QuantumThreat.SHOR,
                pqc_recommendation=rec
            )
        if algorithm == "RSA" and asset.key_length is None:
            return _assessment(
                asset_id=aid,
                severity=RiskSeverity.CRITICAL,
                reason="RSA was detected, but its key length is unavailable; asymmetric cryptography requires migration planning.",
                confidence=min(confidence, 0.75),
                quantum_threat=QuantumThreat.SHOR,
                pqc_recommendation=rec
            )
        return _assessment(
            asset_id=aid,
            severity=RiskSeverity.CRITICAL,
            reason=f"{asset.algorithm} is an asymmetric primitive vulnerable to Shor's algorithm.",
            confidence=confidence,
            quantum_threat=QuantumThreat.SHOR,
            pqc_recommendation=rec
        )

    if algorithm == "AES":
        rec = PQCRecommendation("AES-256-GCM", "FIPS 197", "Upgrade key size and mode")
        if asset.key_length is not None and asset.key_length < 128:
            return _assessment(
                asset_id=aid,
                severity=RiskSeverity.HIGH,
                reason=f"AES key length {asset.key_length} is below the 128 bit minimum.",
                confidence=confidence,
                quantum_threat=QuantumThreat.NONE,
                pqc_recommendation=rec
            )
        if asset.key_length in {128, 192}:
            if asset.mode is None:
                return _assessment(
                    asset_id=aid,
                    severity=RiskSeverity.MEDIUM,
                    reason=f"AES-{asset.key_length} was detected but mode is unavailable. It also provides a reduced post-quantum security margin (approx {asset.key_length // 2} bits) due to Grover's algorithm, falling below the 128-bit safe floor.",
                    confidence=min(confidence, 0.75),
                    quantum_threat=QuantumThreat.GROVER,
                    pqc_recommendation=PQCRecommendation("AES-256-GCM", "FIPS 197", "Verify mode and upgrade key size")
                )

            return _assessment(
                asset_id=aid,
                severity=RiskSeverity.MEDIUM,
                reason=f"AES-{asset.key_length} provides a reduced post-quantum security margin (approx {asset.key_length // 2} bits) due to Grover's algorithm, falling below the 128-bit safe floor.",
                confidence=confidence,
                quantum_threat=QuantumThreat.GROVER,
                pqc_recommendation=PQCRecommendation("AES-256-GCM", "FIPS 197", "Upgrade key size")
            )

        if asset.key_length is None or asset.mode is None:
            return _assessment(
                asset_id=aid,
                severity=RiskSeverity.MEDIUM,
                reason="AES was detected but key length or mode is unavailable, so configuration strength cannot be confirmed.",
                confidence=min(confidence, 0.75),
                quantum_threat=QuantumThreat.GROVER,
                pqc_recommendation=PQCRecommendation("AES-256-GCM", "FIPS 197", "Verify key length and mode")
            )
        if asset.mode.upper() in {"ECB", "CBC"}:
            return _assessment(
                asset_id=aid,
                severity=RiskSeverity.MEDIUM,
                reason=f"AES uses {asset.mode.upper()}, which does not by itself provide authenticated encryption.",
                confidence=confidence,
                quantum_threat=QuantumThreat.NONE,
                pqc_recommendation=PQCRecommendation("AES-256-GCM", "FIPS 197", "Upgrade to authenticated mode")
            )
        return _assessment(
            asset_id=aid,
            severity=RiskSeverity.LOW,
            reason="AES has a strong key length and a recognized modern configuration.",
            confidence=confidence,
            quantum_threat=QuantumThreat.NONE,
        )

    if algorithm in {"SHA-256", "SHA256", "SHA-512", "SHA512", "SHA-3", "SHA3"}:
        return _assessment(
            asset_id=aid,
            severity=RiskSeverity.INFO,
            reason=f"{asset.algorithm} is a modern approved hashing primitive.",
            confidence=confidence,
            quantum_threat=QuantumThreat.NONE,
        )

    if algorithm in {"CERTIFICATE", "CERT"} or category == "certificate_or_key":
        return _assessment(
            asset_id=aid,
            severity=RiskSeverity.MEDIUM,
            reason="A certificate or key was detected, but its cryptographic parameters are unavailable.",
            confidence=min(confidence, 0.75),
            quantum_threat=QuantumThreat.NONE,
        )

    return _assessment(
        asset_id=aid,
        severity=RiskSeverity.MEDIUM,
        reason=f"The strength of {asset.algorithm} cannot be established from the available metadata.",
        confidence=min(confidence, 0.75),
        quantum_threat=QuantumThreat.NONE,
    )


def classify_assets(assets: Iterable[CryptoAsset]) -> List[RiskAssessment]:
    """Classify assets in input order without changing the assets (Phase 1 compatible)."""
    return [classify_asset(asset) for asset in assets]


def get_pqc_recommendation(algorithm: str, category: str) -> Optional[PQCRecommendation]:
    """Helper returning standard NIST PQC recommendations."""
    algo = algorithm.strip().upper()
    cat = category.strip().lower()

    if algo == "RSA":
        if cat == "digital_signature":
            return PQCRecommendation("ML-DSA-65", "FIPS 204", "Direct Replacement")
        elif cat in {"asymmetric_encryption", "key_exchange"}:
            return PQCRecommendation("ML-KEM-768", "FIPS 203", "Hybrid (ECDH + ML-KEM) or Direct Replacement")
        else:
            return PQCRecommendation("ML-KEM-768 / ML-DSA-65", "FIPS 203 / FIPS 204", "Algorithm Replacement")
    elif algo in {"ECDSA", "DSA"}:
        return PQCRecommendation("ML-DSA-65", "FIPS 204", "Direct Replacement")
    elif algo in {"ECDH", "DH"}:
        return PQCRecommendation("ML-KEM-768", "FIPS 203", "Hybrid or Direct Replacement")
    elif algo in {"ECC", "EC"}:
        return PQCRecommendation("ML-KEM-768 / ML-DSA-65", "FIPS 203 / FIPS 204", "Algorithm Replacement")
    elif algo == "AES":
        return PQCRecommendation("AES-256-GCM", "FIPS 197", "Upgrade key size to 256 bits")
    elif algo in {"MD5", "SHA-1", "SHA1"}:
        return PQCRecommendation("SHA-256 / SHA-3-256", "FIPS 180-4 / FIPS 202", "Direct Replacement")
    elif algo in {"DES", "3DES", "TRIPLE-DES", "RC4"}:
        return PQCRecommendation("AES-256-GCM", "FIPS 197", "Direct Replacement")
    return None


def assess_quantum_risk(
    asset: CryptoAsset,
    context: Optional[AssetContext] = None,
    policy: Optional[RiskPolicyConfig] = None,
) -> QuantumRiskAssessment:
    """Phase 2 Context-Aware Cryptographic Risk Intelligence Assessment.
    
    Evaluates:
    1. Technical Quantum Vulnerability (Shor vs Grover vs None)
    2. Harvest-Now-Decrypt-Later (HNDL) exposure
    3. Mosca-Style Cryptographic Lifecycle (C + M > Y)
    4. Explicit Context Provenance (User vs Derived vs Unknown)
    5. Fact-based Explainability Breakdown
    """
    if context is None:
        context = AssetContext()
    if policy is None:
        policy = RiskPolicyConfig()

    # 1. Technical Quantum Threat Assessment
    qt = evaluate_quantum_threat(asset.algorithm, asset.key_length)
    pqc_rec = get_pqc_recommendation(asset.algorithm, asset.category)

    # Calculate Technical Risk Severity
    if qt.threat_type == QuantumThreatType.SHOR:
        tech_risk = RiskSeverity.CRITICAL
    elif qt.threat_type == QuantumThreatType.GROVER:
        tech_risk = RiskSeverity.MEDIUM
    elif asset.category == "hardcoded_secret" or asset.algorithm.upper() == "SECRET":
        tech_risk = RiskSeverity.CRITICAL
    elif asset.algorithm.upper() in {"MD5", "SHA-1", "SHA1", "DES", "3DES", "RC4"}:
        tech_risk = RiskSeverity.HIGH
    elif asset.algorithm.upper() in {"SHA-256", "SHA256", "SHA-512", "SHA512", "SHA-3", "SHA3"}:
        tech_risk = RiskSeverity.INFO
    else:
        tech_risk = RiskSeverity.LOW if (asset.algorithm.upper() == "AES" and asset.key_length == 256) else RiskSeverity.MEDIUM

    # 2. HNDL Assessment
    hndl_res = evaluate_hndl_risk(asset, context, policy)

    # 3. Mosca Lifecycle Assessment
    lifecycle_res = evaluate_lifecycle_urgency(context, policy)

    # 4. Context Criticality
    context_crit = context.business_criticality.value

    # 5. Business Urgency & Overall Planning Priority
    why_vulnerable: List[str] = [qt.description]
    why_now: List[str] = []
    missing_info: List[str] = []
    reasons: List[str] = []
    recs: List[str] = []

    # Record reasons & missing context
    if hndl_res.status != HNDLStatus.NOT_APPLICABLE:
        reasons.extend(hndl_res.reasons)
    if lifecycle_res.explanation:
        reasons.append(lifecycle_res.explanation)

    # Check for missing context
    if context.business_criticality.source == "unknown" or context.business_criticality.value == BusinessCriticality.UNKNOWN:
        missing_info.append("business_criticality (Unknown - business impact cannot be verified)")
    if context.data_lifetime_years.source == "unknown" or context.data_lifetime_years.value is None:
        missing_info.append("data_lifetime_years (Unknown - Mosca protection horizon C+M cannot be evaluated)")
    if context.data_sensitivity.source == "unknown" or context.data_sensitivity.value == DataSensitivity.UNKNOWN:
        missing_info.append("data_sensitivity (Unknown - HNDL sensitivity requirement unconfirmed)")
    if context.internet_exposed.source == "unknown" or context.internet_exposed.value is None:
        missing_info.append("internet_exposed (Unknown - network exposure unconfirmed)")

    # Overall Priority & Business Urgency Determination
    if missing_info:
        why_now.append("Context is incomplete. Context enrichment required to finalize business urgency.")

    if hndl_res.status == HNDLStatus.CRITICAL or lifecycle_res.urgency == LifecycleUrgency.CRITICAL:
        overall_priority = "IMMEDIATE_ACTION"
        bus_urgency = RiskSeverity.CRITICAL
        why_now.append("Data protection horizon or active HNDL harvesting threat requires immediate PQC migration planning.")
    elif hndl_res.status == HNDLStatus.HIGH or lifecycle_res.urgency == LifecycleUrgency.HIGH:
        overall_priority = "PLANNING_REQUIRED"
        bus_urgency = RiskSeverity.HIGH
        why_now.append("High HNDL exposure or narrow quantum safety margin requires scheduled PQC migration planning.")
    elif missing_info:
        overall_priority = "NEEDS_CONTEXT"
        bus_urgency = RiskSeverity.UNKNOWN
    elif hndl_res.status in (HNDLStatus.MEDIUM, HNDLStatus.LOW) or lifecycle_res.urgency == LifecycleUrgency.MODERATE:
        overall_priority = "MONITOR"
        bus_urgency = RiskSeverity.MEDIUM
        why_now.append("Asset operates within safe quantum horizon; continuous monitoring recommended.")
    else:
        overall_priority = "LOW_PRIORITY"
        bus_urgency = RiskSeverity.LOW
        why_now.append("No immediate quantum urgency detected.")

    if pqc_rec:
        recs.append(f"Migrate primitive to NIST standard {pqc_rec.target_algorithm} ({pqc_rec.nist_standard}) via {pqc_rec.migration_type}.")
    else:
        recs.append("Review cryptographic parameters and update to standard algorithms.")

    # Calculate assessment confidence
    # Base confidence comes from asset detection confidence, reduced if context is missing
    base_conf = asset.confidence
    if missing_info:
        confidence = max(0.2, base_conf - (0.15 * len(missing_info)))
    else:
        confidence = min(1.0, base_conf)

    explanation = RiskExplanation(
        what=f"{asset.algorithm} ({asset.category}) discovered in {asset.language.upper()} using library '{asset.library}'.",
        where=f"{asset.file_path}:{asset.line_number}",
        context_summary=context.to_dict(),
        why_vulnerable=why_vulnerable,
        why_now=why_now,
        missing_information=missing_info,
        recommendations=recs,
    )

    return QuantumRiskAssessment(
        asset_id=asset.asset_id,
        technical_quantum_risk=tech_risk,
        quantum_threat=qt,
        hndl_assessment=hndl_res,
        lifecycle_assessment=lifecycle_res,
        context_criticality=context_crit,
        business_urgency=bus_urgency,
        overall_priority=overall_priority,
        reasons=reasons,
        assumptions=policy.to_dict(),
        confidence=round(confidence, 2),
        explanation=explanation,
        pqc_recommendation=pqc_rec,
    )