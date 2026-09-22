"""
Asset Context Engine for CryptoSentinel Phase 2.

Defines deterministic models for cryptographic asset context, context sources,
provenance tracking, and context resolution.
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union
import json

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


class DataSensitivity(str, Enum):
    """Sensitivity level of data protected by a cryptographic asset."""
    UNKNOWN = "UNKNOWN"
    PUBLIC = "PUBLIC"
    LOW = "LOW"
    INTERNAL = "INTERNAL"
    MEDIUM = "MEDIUM"
    CONFIDENTIAL = "CONFIDENTIAL"
    HIGH = "HIGH"
    RESTRICTED = "RESTRICTED"
    CRITICAL = "CRITICAL"


class BusinessCriticality(str, Enum):
    """Business criticality of the application or service hosting the asset."""
    UNKNOWN = "UNKNOWN"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Environment(str, Enum):
    """Deployment environment where the asset operates."""
    UNKNOWN = "UNKNOWN"
    DEVELOPMENT = "DEVELOPMENT"
    TEST = "TEST"
    STAGING = "STAGING"
    PRODUCTION = "PRODUCTION"


class ContextSource(str, Enum):
    """Provenance mechanism indicating where context originated."""
    OBSERVED = "observed"   # Inferred directly from code AST/evidence
    DERIVED = "derived"     # Derived from config files / directory structure
    USER = "user"           # Explicitly provided by user/operator
    UNKNOWN = "unknown"     # Missing / default unassigned value


T = TypeVar("T")


@dataclass
class ContextField(Generic[T]):
    """Wrapper holding a context value along with its provenance source and confidence level."""
    value: T
    source: ContextSource = ContextSource.UNKNOWN
    confidence: float = 0.0
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        val = self.value
        if isinstance(val, Enum):
            val = val.value
        return {
            "value": val,
            "source": self.source.value,
            "confidence": round(self.confidence, 2),
            "notes": self.notes,
        }

    @classmethod
    def unknown(cls, default_val: Any) -> "ContextField":
        return cls(value=default_val, source=ContextSource.UNKNOWN, confidence=0.0)

    @classmethod
    def from_dict(cls, data: Any, enum_cls: Optional[type] = None, default_val: Any = None) -> "ContextField":
        if isinstance(data, dict) and "value" in data:
            raw_val = data["value"]
            source_str = data.get("source", "unknown")
            conf = float(data.get("confidence", 1.0 if source_str in ("user", "derived") else 0.0))
            notes = data.get("notes")
        else:
            raw_val = data
            source_str = "user" if data is not None else "unknown"
            conf = 1.0 if data is not None else 0.0
            notes = None

        if raw_val is None:
            raw_val = default_val

        if enum_cls and isinstance(raw_val, str):
            try:
                val = enum_cls(raw_val.upper())
            except ValueError:
                val = default_val if default_val is not None else enum_cls.UNKNOWN
        else:
            val = raw_val

        try:
            source = ContextSource(source_str.lower())
        except ValueError:
            source = ContextSource.UNKNOWN

        return cls(value=val, source=source, confidence=conf, notes=notes)


@dataclass
class AssetContext:
    """Structured context characterizing the environment and business role of a CryptoAsset."""
    application: ContextField[str] = field(default_factory=lambda: ContextField.unknown("UNKNOWN"))
    system: ContextField[str] = field(default_factory=lambda: ContextField.unknown("UNKNOWN"))
    environment: ContextField[Environment] = field(default_factory=lambda: ContextField.unknown(Environment.UNKNOWN))
    owner: ContextField[str] = field(default_factory=lambda: ContextField.unknown("UNKNOWN"))
    team: ContextField[str] = field(default_factory=lambda: ContextField.unknown("UNKNOWN"))
    repository: ContextField[str] = field(default_factory=lambda: ContextField.unknown("UNKNOWN"))
    service: ContextField[str] = field(default_factory=lambda: ContextField.unknown("UNKNOWN"))
    deployment_type: ContextField[str] = field(default_factory=lambda: ContextField.unknown("UNKNOWN"))
    internet_exposed: ContextField[Optional[bool]] = field(default_factory=lambda: ContextField.unknown(None))
    data_type: ContextField[str] = field(default_factory=lambda: ContextField.unknown("UNKNOWN"))
    data_sensitivity: ContextField[DataSensitivity] = field(default_factory=lambda: ContextField.unknown(DataSensitivity.UNKNOWN))
    data_lifetime_years: ContextField[Optional[float]] = field(default_factory=lambda: ContextField.unknown(None))
    business_criticality: ContextField[BusinessCriticality] = field(default_factory=lambda: ContextField.unknown(BusinessCriticality.UNKNOWN))
    operational_criticality: ContextField[BusinessCriticality] = field(default_factory=lambda: ContextField.unknown(BusinessCriticality.UNKNOWN))
    external_dependency: ContextField[Optional[bool]] = field(default_factory=lambda: ContextField.unknown(None))
    compliance_relevance: ContextField[List[str]] = field(default_factory=lambda: ContextField.unknown([]))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "application": self.application.to_dict(),
            "system": self.system.to_dict(),
            "environment": self.environment.to_dict(),
            "owner": self.owner.to_dict(),
            "team": self.team.to_dict(),
            "repository": self.repository.to_dict(),
            "service": self.service.to_dict(),
            "deployment_type": self.deployment_type.to_dict(),
            "internet_exposed": self.internet_exposed.to_dict(),
            "data_type": self.data_type.to_dict(),
            "data_sensitivity": self.data_sensitivity.to_dict(),
            "data_lifetime_years": self.data_lifetime_years.to_dict(),
            "business_criticality": self.business_criticality.to_dict(),
            "operational_criticality": self.operational_criticality.to_dict(),
            "external_dependency": self.external_dependency.to_dict(),
            "compliance_relevance": self.compliance_relevance.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "AssetContext":
        if not data:
            return cls()

        return cls(
            application=ContextField.from_dict(data.get("application"), default_val="UNKNOWN"),
            system=ContextField.from_dict(data.get("system"), default_val="UNKNOWN"),
            environment=ContextField.from_dict(data.get("environment"), enum_cls=Environment, default_val=Environment.UNKNOWN),
            owner=ContextField.from_dict(data.get("owner"), default_val="UNKNOWN"),
            team=ContextField.from_dict(data.get("team"), default_val="UNKNOWN"),
            repository=ContextField.from_dict(data.get("repository"), default_val="UNKNOWN"),
            service=ContextField.from_dict(data.get("service"), default_val="UNKNOWN"),
            deployment_type=ContextField.from_dict(data.get("deployment_type"), default_val="UNKNOWN"),
            internet_exposed=ContextField.from_dict(data.get("internet_exposed"), default_val=None),
            data_type=ContextField.from_dict(data.get("data_type"), default_val="UNKNOWN"),
            data_sensitivity=ContextField.from_dict(data.get("data_sensitivity"), enum_cls=DataSensitivity, default_val=DataSensitivity.UNKNOWN),
            data_lifetime_years=ContextField.from_dict(data.get("data_lifetime_years"), default_val=None),
            business_criticality=ContextField.from_dict(data.get("business_criticality"), enum_cls=BusinessCriticality, default_val=BusinessCriticality.UNKNOWN),
            operational_criticality=ContextField.from_dict(data.get("operational_criticality"), enum_cls=BusinessCriticality, default_val=BusinessCriticality.UNKNOWN),
            external_dependency=ContextField.from_dict(data.get("external_dependency"), default_val=None),
            compliance_relevance=ContextField.from_dict(data.get("compliance_relevance"), default_val=[]),
        )

    def merge(self, override: "AssetContext") -> "AssetContext":
        """Returns a new AssetContext where fields in override supersede self if they provide higher precedence context."""
        merged = AssetContext.from_dict(self.to_dict())

        # Precedence order: USER > DERIVED > OBSERVED > UNKNOWN
        priority = {
            ContextSource.USER: 4,
            ContextSource.DERIVED: 3,
            ContextSource.OBSERVED: 2,
            ContextSource.UNKNOWN: 1,
        }

        for attr in self.__dataclass_fields__:
            self_field: ContextField = getattr(self, attr)
            other_field: ContextField = getattr(override, attr)

            p_self = priority.get(self_field.source, 1)
            p_other = priority.get(other_field.source, 1)

            if p_other > p_self or (p_other == p_self and other_field.confidence >= self_field.confidence and other_field.source != ContextSource.UNKNOWN):
                setattr(merged, attr, ContextField.from_dict(other_field.to_dict(), default_val=self_field.value))

        return merged


class ContextResolver:
    """Resolves asset context from repository config files, path rules, and user overlays."""

    @staticmethod
    def load_repo_config(target_dir: Union[str, Path]) -> Optional[Dict[str, Any]]:
        """Scans target_dir for .cryptosentinel.yml / .cryptosentinel.json configuration file."""
        target_path = Path(target_dir)
        if not target_path.exists():
            return None

        if target_path.is_file():
            target_path = target_path.parent

        yaml_path = target_path / ".cryptosentinel.yml"
        if yaml_path.exists() and HAS_YAML:
            try:
                with open(yaml_path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f)
            except Exception:
                pass

        json_path = target_path / ".cryptosentinel.json"
        if json_path.exists():
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        return None

    @classmethod
    def resolve_context(
        cls,
        target_dir: Union[str, Path],
        asset_id: Optional[str] = None,
        file_path: Optional[str] = None,
        user_context_map: Optional[Dict[str, Any]] = None,
    ) -> AssetContext:
        """Constructs a merged AssetContext by resolving repo config and user overlays."""
        base_ctx = AssetContext()

        repo_cfg = cls.load_repo_config(target_dir)
        if repo_cfg and isinstance(repo_cfg, dict):
            # 1. Global repo-level context
            global_ctx_dict = repo_cfg.get("default_context", {})
            if global_ctx_dict:
                # Mark as DERIVED source
                for k, v in global_ctx_dict.items():
                    if isinstance(v, dict) and "source" not in v:
                        v["source"] = "derived"
                    elif not isinstance(v, dict):
                        global_ctx_dict[k] = {"value": v, "source": "derived", "confidence": 0.9}
                base_ctx = base_ctx.merge(AssetContext.from_dict(global_ctx_dict))

            # 2. Asset-specific context in repo config
            assets_cfg = repo_cfg.get("asset_context", {})
            if asset_id and asset_id in assets_cfg:
                asset_cfg_dict = assets_cfg[asset_id]
                for k, v in asset_cfg_dict.items():
                    if isinstance(v, dict) and "source" not in v:
                        v["source"] = "derived"
                    elif not isinstance(v, dict):
                        asset_cfg_dict[k] = {"value": v, "source": "derived", "confidence": 0.9}
                base_ctx = base_ctx.merge(AssetContext.from_dict(asset_cfg_dict))

        # 3. Direct user-provided context map override
        if user_context_map and isinstance(user_context_map, dict):
            # Direct asset match or default fallback
            user_override = user_context_map.get(asset_id) if asset_id else None
            if not user_override and "default" in user_context_map:
                user_override = user_context_map.get("default")
            if not user_override and asset_id not in user_context_map and "default" not in user_context_map:
                # user_context_map is a direct context dict for this asset
                user_override = user_context_map

            if user_override and isinstance(user_override, dict):
                user_ctx_dict = {}
                for k, v in user_override.items():
                    if isinstance(v, dict):
                        user_ctx_dict[k] = v
                    else:
                        user_ctx_dict[k] = {"value": v, "source": "user", "confidence": 1.0}
                base_ctx = base_ctx.merge(AssetContext.from_dict(user_ctx_dict))

        return base_ctx
