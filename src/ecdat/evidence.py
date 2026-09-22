"""
Evidence model constants and completeness validator.

Every finding in CryptoSentinel must be able to answer:
  WHAT?      -- asset_type + algorithm
  WHERE?     -- path + line/offset
  HOW?       -- detection_mechanism + rule_id
  WHY?       -- observation_type
  CONFIDENCE -- 0.0-1.0

This module provides authoritative constants for observation types and
provenance values, plus a lightweight validation helper.  It never creates
or mutates findings; it only validates and labels them.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional


class ObservationType:
    """Authoritative observation type labels."""
    DIRECTLY_OBSERVED = "DIRECTLY_OBSERVED"
    LIVE_VERIFIED = "LIVE_VERIFIED"
    CONFIGURED = "CONFIGURED"
    DERIVED = "DERIVED"
    INFERRED_FROM_INDICATOR = "INFERRED_FROM_INDICATOR"
    INFERRED_FROM_BINARY_INDICATOR = "INFERRED_FROM_BINARY_INDICATOR"
    DECLARED = "DECLARED"
    LOCKED = "LOCKED"
    REFERENCE_ONLY = "REFERENCE_ONLY"
    USER_PROVIDED = "USER_PROVIDED"
    UNKNOWN = "UNKNOWN"

    ALL: List[str] = [
        DIRECTLY_OBSERVED, LIVE_VERIFIED, CONFIGURED, DERIVED,
        INFERRED_FROM_INDICATOR, INFERRED_FROM_BINARY_INDICATOR,
        DECLARED, LOCKED, REFERENCE_ONLY, USER_PROVIDED, UNKNOWN,
    ]


class DependencyState:
    """State of a dependency relative to cryptographic usage evidence."""
    DECLARED = "DECLARED"
    LOCKED = "LOCKED"
    INSTALLED = "INSTALLED"
    IMPORTED = "IMPORTED"
    CRYPTO_CAPABLE = "CRYPTO_CAPABLE"
    OBSERVED_USAGE = "OBSERVED_USAGE"


class Provenance:
    """Where the evidence originated."""
    SOURCE_CODE = "source_code"
    BINARY = "binary"
    CONTAINER = "container"
    DEPENDENCY_MANIFEST = "dependency_manifest"
    CONFIGURATION_FILE = "configuration_file"
    IaC = "infrastructure_as_code"
    CERTIFICATE_FILE = "certificate_file"
    KEY_FILE = "key_file"
    HARDWARE_CONFIG = "hardware_config"
    CLOUD_IaC = "cloud_iac"
    ENVIRONMENT_VARIABLE = "environment_variable"
    USER_INPUT = "user_input"
    UNKNOWN = "unknown"


_REQUIRED_FIELDS = ("asset_type", "path", "detection_mechanism", "observation_type", "confidence")
_OPTIONAL_FIELDS = ("algorithm", "library", "version", "mode", "line", "offset", "snippet",
                    "rule_id", "provenance", "first_seen", "last_seen")


def check_completeness(finding: Dict[str, Any]) -> Dict[str, Any]:
    """Return a completeness report for a finding dict. Does NOT raise."""
    missing_required = [f for f in _REQUIRED_FIELDS if finding.get(f) is None]
    missing_optional = [f for f in _OPTIONAL_FIELDS if finding.get(f) is None]
    obs = finding.get("observation_type", "UNKNOWN")
    invalid_obs = obs not in ObservationType.ALL
    confidence = finding.get("confidence")
    invalid_confidence = not isinstance(confidence, (int, float)) or not (0.0 <= float(confidence) <= 1.0)
    return {
        "complete": not missing_required and not invalid_obs and not invalid_confidence,
        "missing_required": missing_required,
        "missing_optional": missing_optional,
        "invalid_observation_type": invalid_obs,
        "invalid_confidence": invalid_confidence,
    }


def normalise_observation_type(raw: Optional[str]) -> str:
    """Return a valid ObservationType string, defaulting to UNKNOWN."""
    if raw:
        for t in ObservationType.ALL:
            if t.upper() == raw.upper():
                return t
    return ObservationType.UNKNOWN
