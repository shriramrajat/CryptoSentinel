"""
Migration Readiness Assessment Engine for CryptoSentinel Phase 3.

Evaluates asset/application readiness across 5 dimensions: Discovery completeness,
Context completeness, Dependency/Library support, Protocol compatibility, and Testing readiness.
"""

from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, Any, List, Optional

from ecdat.context import AssetContext
from ecdat.migration_constraints import MigrationConstraints
from ecdat.models import CryptoAsset
from ecdat.pqc_recommendation import MigrationRecommendation


class ReadinessState(str, Enum):
    """Overall readiness state for PQC migration."""
    READY_FOR_MIGRATION = "READY_FOR_MIGRATION"
    READY_FOR_PLANNING = "READY_FOR_PLANNING"
    PARTIALLY_READY = "PARTIALLY_READY"
    NOT_READY = "NOT_READY"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class DimensionScore:
    """Individual readiness dimension result."""
    name: str
    passed: bool
    score: float  # 0.0 to 1.0
    notes: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MigrationReadiness:
    """Structured 5-dimensional migration readiness assessment."""
    state: ReadinessState
    overall_score: float  # 0.0 to 100.0 (deterministic weighted sum)
    discovery_completeness: DimensionScore
    context_completeness: DimensionScore
    dependency_library_support: DimensionScore
    protocol_compatibility: DimensionScore
    testing_readiness: DimensionScore
    checklist: List[str]

    def to_dict(self) -> Dict[str, Any]:
        res = asdict(self)
        res["state"] = self.state.value
        return res


def evaluate_migration_readiness(
    asset: CryptoAsset,
    context: AssetContext,
    recommendation: MigrationRecommendation,
) -> MigrationReadiness:
    """Evaluates migration readiness across 5 explicit dimensions deterministically."""
    checklist: List[str] = []

    # 1. Discovery Completeness
    disc_passed = bool(asset.asset_id and asset.file_path and asset.evidence and asset.evidence.code_snippet)
    disc_score = 1.0 if disc_passed else 0.5
    disc_dim = DimensionScore(
        name="Discovery Completeness",
        passed=disc_passed,
        score=disc_score,
        notes="Asset evidence and source line numbers verified." if disc_passed else "Incomplete discovery evidence.",
    )
    if disc_passed:
        checklist.append("✔ Cryptographic asset location and code evidence verified.")

    # 2. Context Completeness
    missing_cnt = 0
    if context.business_criticality.source == "unknown": missing_cnt += 1
    if context.data_lifetime_years.source == "unknown": missing_cnt += 1
    if context.data_sensitivity.source == "unknown": missing_cnt += 1
    if context.internet_exposed.source == "unknown": missing_cnt += 1

    ctx_score = max(0.0, round(1.0 - (0.25 * missing_cnt), 2))
    ctx_passed = (missing_cnt <= 1)
    ctx_dim = DimensionScore(
        name="Context Completeness",
        passed=ctx_passed,
        score=ctx_score,
        notes=f"Context completeness score {int(ctx_score*100)}% ({missing_cnt} parameters UNKNOWN).",
    )
    if ctx_passed:
        checklist.append("✔ Operational context (sensitivity, lifetime, environment) resolved.")
    else:
        checklist.append("✖ Missing business context; context enrichment required.")

    # 3. Dependency & Library Support
    lib_risk = recommendation.constraints.library_availability_risk
    dep_passed = not lib_risk
    dep_score = 0.5 if lib_risk else 1.0
    dep_dim = DimensionScore(
        name="Dependency & Library Support",
        passed=dep_passed,
        score=dep_score,
        notes=f"Library '{asset.library}' compatibility for {recommendation.recommended_algorithm} " +
              ("requires liboqs / OpenSSL 3.5+ bindings." if lib_risk else "verified."),
    )
    if dep_passed:
        checklist.append(f"✔ Library '{asset.library}' supports PQC bindings.")
    else:
        checklist.append(f"✖ Library '{asset.library}' requires liboqs or OpenSSL 3.5+ upgrade.")

    # 4. Protocol Compatibility
    prot_risk = recommendation.constraints.protocol_compatibility_risk or recommendation.constraints.packet_fragmentation_risk
    prot_passed = not prot_risk
    prot_score = 0.5 if prot_risk else 1.0
    prot_dim = DimensionScore(
        name="Protocol Compatibility",
        passed=prot_passed,
        score=prot_score,
        notes="Packet fragmentation or protocol buffer risk identified." if prot_risk else "Protocol key/sig sizes compatible.",
    )
    if prot_passed:
        checklist.append("✔ Protocol buffer and packet size compatibility verified.")
    else:
        checklist.append("✖ Signature/key size overhead requires packet fragmentation testing.")

    # 5. Testing Readiness
    env = context.environment.value
    test_passed = (env in ("DEVELOPMENT", "TEST", "STAGING", "PRODUCTION"))
    test_score = 1.0 if test_passed else 0.5
    test_dim = DimensionScore(
        name="Testing Readiness",
        passed=test_passed,
        score=test_score,
        notes=f"Deployment environment is {env}.",
    )
    if test_passed:
        checklist.append(f"✔ Environment ({env}) available for migration test execution.")

    # Overall Deterministic Weighted Score (0 to 100)
    # Weights: Discovery 20%, Context 25%, Dependency 25%, Protocol 15%, Testing 15%
    overall_score = round(
        (disc_score * 20.0) +
        (ctx_score * 25.0) +
        (dep_score * 25.0) +
        (prot_score * 15.0) +
        (test_score * 15.0),
        1
    )

    # Derive State
    if overall_score >= 85.0:
        state = ReadinessState.READY_FOR_MIGRATION
    elif overall_score >= 70.0:
        state = ReadinessState.READY_FOR_PLANNING
    elif overall_score >= 50.0:
        state = ReadinessState.PARTIALLY_READY
    elif disc_passed:
        state = ReadinessState.NOT_READY
    else:
        state = ReadinessState.UNKNOWN

    return MigrationReadiness(
        state=state,
        overall_score=overall_score,
        discovery_completeness=disc_dim,
        context_completeness=ctx_dim,
        dependency_library_support=dep_dim,
        protocol_compatibility=prot_dim,
        testing_readiness=test_dim,
        checklist=checklist,
    )
