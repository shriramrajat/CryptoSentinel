"""Shared contracts for Phase 5 discovery sources."""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
import os
import hashlib
import json

from ecdat.models import CryptoAsset, Evidence


class DiscoveryError(ValueError):
    """Safe, user-facing discovery input error."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable_id(prefix: str, values: Iterable[Any]) -> str:
    encoded = json.dumps(list(values), sort_keys=True, default=str, separators=(",", ":"))
    return f"{prefix}-{hashlib.sha256(encoded.encode('utf-8')).hexdigest()[:16]}"


@dataclass
class DiscoveryFinding:
    source_type: str
    source_location: str
    indicator: str
    evidence: str
    confidence: float
    detection_mechanism: str
    rule_id: Optional[str] = None
    timestamp: str = field(default_factory=utc_now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    identity_inputs: List[str] = field(default_factory=list)
    observation_type: str = "INFERRED_FROM_INDICATOR"
    finding_id: str = ""

    def __post_init__(self) -> None:
        self.confidence = round(max(0.0, min(1.0, self.confidence)), 2)
        if not self.finding_id:
            self.finding_id = stable_id("finding", [self.source_type, self.source_location, *self.identity_inputs, self.indicator])

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AdvancedDiscoveryResult:
    source_type: str
    source_location: str
    findings: List[DiscoveryFinding] = field(default_factory=list)
    assets: List[Dict[str, Any]] = field(default_factory=list)
    dependencies: List[Dict[str, Any]] = field(default_factory=list)
    protocols: List[Dict[str, Any]] = field(default_factory=list)
    certificates: List[Dict[str, Any]] = field(default_factory=list)
    relationships: List[Dict[str, Any]] = field(default_factory=list)
    git_metadata: Optional[Dict[str, Any]] = None
    errors: List[str] = field(default_factory=list)

    def add_finding(self, finding: DiscoveryFinding) -> None:
        if not any(existing.finding_id == finding.finding_id for existing in self.findings):
            self.findings.append(finding)

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["findings"] = [finding.to_dict() for finding in self.findings]
        return result


def finding_to_asset(finding: DiscoveryFinding, root_dir: Optional[str] = None) -> CryptoAsset:
    """Adapt a finding to the existing Phase 1 model at the boundary."""
    metadata = finding.metadata
    return CryptoAsset.create(
        name=metadata.get("name", finding.indicator),
        category=metadata.get("category", "cryptographic_indicator"),
        algorithm=metadata.get("algorithm", "UNKNOWN"),
        file_path=finding.source_location,
        line_number=int(metadata.get("line_number", 0)),
        code_snippet=finding.evidence,
        library=metadata.get("library", finding.indicator),
        confidence=finding.confidence,
        language=metadata.get("language", "binary"),
        detection_mechanism=finding.detection_mechanism,
        matched_rule_id=finding.rule_id or "advanced-discovery",
        evidence=Evidence(finding.evidence, finding.detection_mechanism, finding.rule_id or "advanced-discovery"),
        key_length=metadata.get("key_length"),
        mode=metadata.get("mode"),
        root_dir=root_dir,
    )


def validate_file(path: str, max_size: int, allowed_root: Optional[str] = None) -> Path:
    candidate = Path(path)
    if not candidate.is_file():
        raise DiscoveryError(f"Input file does not exist: {path}")
    resolved = candidate.resolve()
    configured_root = allowed_root or os.getenv("DISCOVERY_ALLOWED_ROOT")
    if configured_root:
        root = Path(configured_root).resolve()
        try:
            resolved.relative_to(root)
        except ValueError as exc:
            raise DiscoveryError("Input path is outside the configured discovery workspace") from exc
    if candidate.is_symlink() and configured_root:
        try:
            resolved.relative_to(Path(configured_root).resolve())
        except ValueError as exc:
            raise DiscoveryError("Symlink resolves outside the configured discovery workspace") from exc
    if resolved.stat().st_size > max_size:
        raise DiscoveryError(f"Input exceeds the {max_size}-byte limit")
    return resolved
