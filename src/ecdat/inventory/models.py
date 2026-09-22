"""Domain models and dataclasses for Enterprise Cryptographic Inventory & Continuous Monitoring."""
import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class ScanStatus(str, Enum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ObservationStatus(str, Enum):
    ACTIVE = "ACTIVE"
    REMOVED = "REMOVED"


class DriftType(str, Enum):
    NEW_ASSET = "NEW_ASSET"
    REMOVED_ASSET = "REMOVED_ASSET"
    MODIFIED_ASSET = "MODIFIED_ASSET"
    RISK_REGRESSION = "RISK_REGRESSION"
    RISK_IMPROVEMENT = "RISK_IMPROVEMENT"
    MIGRATION_PROGRESS = "MIGRATION_PROGRESS"
    MIGRATION_REGRESSION = "MIGRATION_REGRESSION"


class DriftSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class AlertType(str, Enum):
    WEAK_ALGORITHM_DETECTED = "WEAK_ALGORITHM_DETECTED"
    QUANTUM_CRITICAL_ASSET = "QUANTUM_CRITICAL_ASSET"
    NEW_QUANTUM_VULNERABLE_ASSET = "NEW_QUANTUM_VULNERABLE_ASSET"
    CERTIFICATE_EXPIRING = "CERTIFICATE_EXPIRING"
    CRYPTO_REGRESSION = "CRYPTO_REGRESSION"
    MIGRATION_OVERDUE = "MIGRATION_OVERDUE"
    HIGH_PRIORITY_NEW_ASSET = "HIGH_PRIORITY_NEW_ASSET"
    MIGRATION_STATE_REGRESSION = "MIGRATION_STATE_REGRESSION"


class AlertSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class AlertStatus(str, Enum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"


class AlertScopeType(str, Enum):
    ORGANIZATION = "organization"
    PROJECT = "project"
    REPOSITORY = "repository"
    ASSET = "asset"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Organization:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Default Enterprise"
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Project:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str = ""
    name: str = "Default Project"
    description: str = ""
    business_criticality: str = "high"
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Repository:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = ""
    name: str = "Default Repository"
    provider: str = "git"
    url: str = ""
    default_branch: str = "main"
    environment: str = "production"
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ScanRecord:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    repository_id: str = ""
    started_at: str = field(default_factory=utc_now_iso)
    completed_at: Optional[str] = None
    status: ScanStatus = ScanStatus.IN_PROGRESS
    commit_sha: str = "head"
    branch: str = "main"
    scanner_version: str = "0.2.0"
    source_type: str = "repository"
    asset_count: int = 0
    error_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        res = asdict(self)
        res["status"] = self.status.value if isinstance(self.status, ScanStatus) else self.status
        return res


@dataclass
class CryptoAssetRecord:
    asset_id: str
    algorithm: str
    category: str
    purpose: Optional[str] = None
    language: Optional[str] = None
    library: Optional[str] = None
    key_length: Optional[int] = None
    mode: Optional[str] = None
    padding: Optional[str] = None
    source_path: str = ""
    line_number: int = 1
    evidence_json: str = "{}"
    detection_rule: str = "unknown"
    confidence: float = 0.9
    certificate_metadata_json: Optional[str] = None
    key_metadata_json: Optional[str] = None
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "algorithm": self.algorithm,
            "category": self.category,
            "purpose": self.purpose,
            "language": self.language,
            "library": self.library,
            "key_length": self.key_length,
            "mode": self.mode,
            "padding": self.padding,
            "source_path": self.source_path,
            "line_number": self.line_number,
            "evidence": json.loads(self.evidence_json) if self.evidence_json else {},
            "detection_rule": self.detection_rule,
            "confidence": self.confidence,
            "certificate_metadata": json.loads(self.certificate_metadata_json) if self.certificate_metadata_json else None,
            "key_metadata": json.loads(self.key_metadata_json) if self.key_metadata_json else None,
            "created_at": self.created_at,
        }


@dataclass
class ObservationRecord:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    asset_id: str = ""
    scan_id: str = ""
    repository_id: str = ""
    observed_at: str = field(default_factory=utc_now_iso)
    source_path: str = ""
    line_number: int = 1
    status: ObservationStatus = ObservationStatus.ACTIVE
    fingerprint: str = ""

    def to_dict(self) -> Dict[str, Any]:
        res = asdict(self)
        res["status"] = self.status.value if isinstance(self.status, ObservationStatus) else self.status
        return res


@dataclass
class RiskAssessmentSnapshot:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    observation_id: str = ""
    asset_id: str = ""
    scan_id: str = ""
    technical_quantum_risk: str = "unknown"
    business_urgency: str = "unknown"
    overall_priority: str = "MONITOR"
    hndl_status: str = "NOT_APPLICABLE"
    mosca_urgency: str = "LOW"
    policy_json: str = "{}"
    assessed_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "observation_id": self.observation_id,
            "asset_id": self.asset_id,
            "scan_id": self.scan_id,
            "technical_quantum_risk": self.technical_quantum_risk,
            "business_urgency": self.business_urgency,
            "overall_priority": self.overall_priority,
            "hndl_status": self.hndl_status,
            "mosca_urgency": self.mosca_urgency,
            "policy": json.loads(self.policy_json) if self.policy_json else {},
            "assessed_at": self.assessed_at,
        }


@dataclass
class MigrationAssessmentSnapshot:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    observation_id: str = ""
    asset_id: str = ""
    scan_id: str = ""
    recommendation_type: str = "DIRECT"
    target_algorithm: str = ""
    readiness_state: str = "UNKNOWN"
    migration_priority: str = "LOW"
    lifecycle_state: str = "DISCOVERED"
    assessed_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DriftEvent:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    repository_id: str = ""
    scan_id: str = ""
    asset_id: str = ""
    type: DriftType = DriftType.NEW_ASSET
    severity: DriftSeverity = DriftSeverity.INFO
    before_state_json: str = "{}"
    after_state_json: str = "{}"
    detected_at: str = field(default_factory=utc_now_iso)
    explanation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "repository_id": self.repository_id,
            "scan_id": self.scan_id,
            "asset_id": self.asset_id,
            "type": self.type.value if isinstance(self.type, DriftType) else self.type,
            "severity": self.severity.value if isinstance(self.severity, DriftSeverity) else self.severity,
            "before_state": json.loads(self.before_state_json) if self.before_state_json else {},
            "after_state": json.loads(self.after_state_json) if self.after_state_json else {},
            "detected_at": self.detected_at,
            "explanation": self.explanation,
        }


@dataclass
class Alert:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: AlertType = AlertType.WEAK_ALGORITHM_DETECTED
    severity: AlertSeverity = AlertSeverity.MEDIUM
    scope_type: AlertScopeType = AlertScopeType.REPOSITORY
    scope_id: str = ""
    repository_id: str = ""
    asset_id: Optional[str] = None
    message: str = ""
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)
    status: AlertStatus = AlertStatus.OPEN
    dedup_key: str = ""

    def transition_to(self, new_status: AlertStatus) -> None:
        valid_transitions = {
            AlertStatus.OPEN: {AlertStatus.ACKNOWLEDGED, AlertStatus.RESOLVED},
            AlertStatus.ACKNOWLEDGED: {AlertStatus.RESOLVED},
            AlertStatus.RESOLVED: {AlertStatus.OPEN},  # Reopen when issue recurs
        }
        if new_status not in valid_transitions.get(self.status, set()):
            raise ValueError(f"Invalid alert state transition from '{self.status.value}' to '{new_status.value}'")
        self.status = new_status
        self.updated_at = utc_now_iso()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value if isinstance(self.type, AlertType) else self.type,
            "severity": self.severity.value if isinstance(self.severity, AlertSeverity) else self.severity,
            "scope_type": self.scope_type.value if isinstance(self.scope_type, AlertScopeType) else self.scope_type,
            "scope_id": self.scope_id,
            "repository_id": self.repository_id,
            "asset_id": self.asset_id,
            "message": self.message,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "status": self.status.value if isinstance(self.status, AlertStatus) else self.status,
            "dedup_key": self.dedup_key,
        }


@dataclass
class ScanSchedule:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    repository_id: str = ""
    enabled: bool = True
    interval_hours: int = 24
    next_run_at: str = field(default_factory=utc_now_iso)
    last_run_at: Optional[str] = None
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
