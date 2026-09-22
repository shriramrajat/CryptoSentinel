"""
PQC Migration Recommendation Engine for CryptoSentinel Phase 3.

Combines Phase 1 asset metadata, Phase 2 risk/context intelligence, PQC Knowledge Base,
and constraint evaluations to generate deterministic MigrationRecommendations.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional

from ecdat.context import AssetContext
from ecdat.migration_constraints import MigrationConstraints, evaluate_migration_constraints
from ecdat.models import CryptoAsset
from ecdat.pqc_kb import PQCAlgorithmInfo
from ecdat.pqc_mapping import HybridStrategy, MappingResult, MigrationType, map_asset_to_pqc
from ecdat.risk import QuantumRiskAssessment


@dataclass
class MigrationRecommendation:
    """Structured PQC migration recommendation for a cryptographic asset."""
    asset_id: str
    current_algorithm: str
    current_purpose: str
    current_library: str
    recommended_algorithm: str
    recommended_family: str
    nist_standard: str
    migration_type: MigrationType
    hybrid_strategy: Optional[HybridStrategy]
    alternative_recommendation: Optional[str]
    rationale: List[str]
    constraints: MigrationConstraints
    confidence: float
    source: str = "deterministic_engine"
    assumptions: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "current_algorithm": self.current_algorithm,
            "current_purpose": self.current_purpose,
            "current_library": self.current_library,
            "recommended_algorithm": self.recommended_algorithm,
            "recommended_family": self.recommended_family,
            "nist_standard": self.nist_standard,
            "migration_type": self.migration_type.value,
            "hybrid_strategy": self.hybrid_strategy.to_dict() if self.hybrid_strategy else None,
            "alternative_recommendation": self.alternative_recommendation,
            "rationale": self.rationale,
            "constraints": self.constraints.to_dict(),
            "confidence": round(self.confidence, 2),
            "source": self.source,
            "assumptions": self.assumptions,
        }


def generate_migration_recommendation(
    asset: CryptoAsset,
    context: Optional[AssetContext] = None,
    risk_assessment: Optional[QuantumRiskAssessment] = None,
) -> MigrationRecommendation:
    """Generates a deterministic MigrationRecommendation for a CryptoAsset."""
    if context is None:
        context = AssetContext()

    # 1. Map classical algorithm + purpose to PQC / Hybrid target
    mapping: MappingResult = map_asset_to_pqc(asset)

    # 2. Evaluate migration constraints
    constraints: MigrationConstraints = evaluate_migration_constraints(
        asset=asset,
        context=context,
        target_pqc=mapping.target_pqc_info,
    )

    # 3. Construct rationale list
    rationale: List[str] = [mapping.rationale]
    if risk_assessment and risk_assessment.reasons:
        rationale.extend(risk_assessment.reasons)

    # Determine recommended algorithm details
    if mapping.target_pqc_info:
        rec_alg = mapping.target_pqc_info.name
        rec_fam = mapping.target_pqc_info.family
        nist_std = mapping.target_pqc_info.nist_standard
    else:
        rec_alg = "N/A"
        rec_fam = "N/A"
        nist_std = "N/A"

    alt_rec = mapping.alternative_pqc_info.name if mapping.alternative_pqc_info else None

    # Calculate confidence based on asset confidence and context presence
    confidence = asset.confidence
    if context.business_criticality.source == "unknown":
        confidence = max(0.3, confidence - 0.1)

    assumptions = {
        "pqc_standardization_baseline": "NIST FIPS 203 / 204 / 205 (Aug 2024)",
        "deterministic_mapping": True,
    }

    return MigrationRecommendation(
        asset_id=asset.asset_id,
        current_algorithm=asset.algorithm,
        current_purpose=asset.category,
        current_library=asset.library,
        recommended_algorithm=rec_alg,
        recommended_family=rec_fam,
        nist_standard=nist_std,
        migration_type=mapping.migration_type,
        hybrid_strategy=mapping.hybrid_strategy,
        alternative_recommendation=alt_rec,
        rationale=rationale,
        constraints=constraints,
        confidence=confidence,
        source="deterministic_engine",
        assumptions=assumptions,
    )
