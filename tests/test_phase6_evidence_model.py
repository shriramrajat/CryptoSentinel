"""Phase 6: Evidence model constants and completeness validation."""
import pytest
from ecdat.evidence import (
    ObservationType, DependencyState, Provenance,
    check_completeness, normalise_observation_type,
)

def test_observation_type_constants_exist():
    assert ObservationType.DIRECTLY_OBSERVED == "DIRECTLY_OBSERVED"
    assert ObservationType.REFERENCE_ONLY == "REFERENCE_ONLY"
    assert ObservationType.CONFIGURED == "CONFIGURED"
    assert len(ObservationType.ALL) >= 10

def test_dependency_state_constants():
    assert DependencyState.DECLARED != DependencyState.OBSERVED_USAGE

def test_completeness_valid():
    finding = {
        "asset_type": "algorithm", "path": "src/main.py",
        "detection_mechanism": "regex", "observation_type": "CONFIGURED",
        "confidence": 0.9,
    }
    report = check_completeness(finding)
    assert report["complete"] is True
    assert not report["missing_required"]

def test_completeness_missing_required():
    report = check_completeness({"path": "src/main.py"})
    assert report["complete"] is False
    assert "asset_type" in report["missing_required"]

def test_completeness_bad_confidence():
    finding = {
        "asset_type": "algorithm", "path": "src/main.py",
        "detection_mechanism": "regex", "observation_type": "CONFIGURED",
        "confidence": 1.5,
    }
    assert check_completeness(finding)["invalid_confidence"] is True

def test_normalise_unknown_returns_unknown():
    assert normalise_observation_type("garbage") == "UNKNOWN"
    assert normalise_observation_type(None) == "UNKNOWN"

def test_normalise_case_insensitive():
    assert normalise_observation_type("directly_observed") == "DIRECTLY_OBSERVED"
    assert normalise_observation_type("REFERENCE_ONLY") == "REFERENCE_ONLY"
