"""
Migration Priority Calculator for CryptoSentinel Phase 3.

Derives Migration Priority (CRITICAL, HIGH, MEDIUM, LOW, REVIEW_REQUIRED) by combining
Phase 2 Quantum Risk, HNDL exposure, Mosca lifecycle urgency, business criticality,
and migration complexity.
"""

from enum import Enum
from typing import Dict, Any, Optional

from ecdat.context import AssetContext, BusinessCriticality
from ecdat.hndl import HNDLStatus
from ecdat.lifecycle import LifecycleUrgency
from ecdat.migration_constraints import MigrationConstraints
from ecdat.risk import QuantumRiskAssessment, RiskSeverity


class MigrationPriority(str, Enum):
    """Migration priority classification."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


def calculate_migration_priority(
    risk_assessment: Optional[QuantumRiskAssessment],
    context: AssetContext,
    constraints: MigrationConstraints,
) -> MigrationPriority:
    """Calculates Migration Priority deterministically without overriding Phase 2 risk score."""
    if risk_assessment is None:
        return MigrationPriority.REVIEW_REQUIRED

    tech_risk = risk_assessment.technical_quantum_risk
    hndl_status = risk_assessment.hndl_assessment.status
    mosca_urgency = risk_assessment.lifecycle_assessment.urgency
    crit = context.business_criticality.value

    # Missing context or unknown algorithm -> REVIEW_REQUIRED
    if risk_assessment.overall_priority == "NEEDS_CONTEXT" or crit == BusinessCriticality.UNKNOWN:
        if hndl_status == HNDLStatus.CRITICAL or mosca_urgency == LifecycleUrgency.CRITICAL:
            return MigrationPriority.CRITICAL
        return MigrationPriority.REVIEW_REQUIRED

    # 1. Critical Priority
    if hndl_status == HNDLStatus.CRITICAL or mosca_urgency == LifecycleUrgency.CRITICAL:
        return MigrationPriority.CRITICAL
    if tech_risk == RiskSeverity.CRITICAL and crit in (BusinessCriticality.CRITICAL, BusinessCriticality.HIGH):
        return MigrationPriority.CRITICAL

    # 2. High Priority
    if hndl_status == HNDLStatus.HIGH or mosca_urgency == LifecycleUrgency.HIGH:
        return MigrationPriority.HIGH
    if tech_risk in (RiskSeverity.CRITICAL, RiskSeverity.HIGH):
        return MigrationPriority.HIGH

    # 3. Medium Priority
    if tech_risk == RiskSeverity.MEDIUM or mosca_urgency == LifecycleUrgency.MODERATE:
        return MigrationPriority.MEDIUM

    # 4. Low Priority
    if tech_risk in (RiskSeverity.LOW, RiskSeverity.INFO):
        return MigrationPriority.LOW

    return MigrationPriority.MEDIUM
