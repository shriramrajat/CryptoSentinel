"""
Phase 2 Context + Quantum Risk Intelligence Comprehensive Test Suite.

Tests context models, context resolution, Mosca lifecycle evaluation (C+M>Y),
Harvest-Now-Decrypt-Later (HNDL) analysis, risk explainability, API endpoints,
and all 18 mandatory edge cases specified in Phase 2 requirement 18.
"""

import sys
from pathlib import Path
import pytest

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from fastapi.testclient import TestClient
from api.main import app
from ecdat.models import CryptoAsset
from ecdat.context import AssetContext, ContextField, ContextResolver, ContextSource, DataSensitivity, BusinessCriticality, Environment
from ecdat.config_policy import RiskPolicyConfig
from ecdat.quantum import evaluate_quantum_threat, QuantumThreatType
from ecdat.lifecycle import evaluate_lifecycle_urgency, LifecycleUrgency
from ecdat.hndl import evaluate_hndl_risk, HNDLStatus
from ecdat.risk import assess_quantum_risk, RiskSeverity

client = TestClient(app)


def make_asset(
    algorithm="RSA",
    category="asymmetric_encryption",
    key_length=2048,
    mode=None,
    padding=None,
    file_path="src/auth/signing.py",
    line_number=42,
) -> CryptoAsset:
    return CryptoAsset.create(
        name=f"{algorithm} asset",
        category=category,
        algorithm=algorithm,
        file_path=file_path,
        line_number=line_number,
        code_snippet="key = RSA.generate(2048)",
        library="cryptography",
        confidence=0.95,
        key_length=key_length,
        mode=mode,
        padding=padding,
    )


# ==============================================================================
# 18 MANDATORY EDGE CASE TESTS
# ==============================================================================

def test_edge_case_01_rsa_unknown_context():
    """1. RSA + unknown context -> Technical risk CRITICAL, Context urgency UNKNOWN, overall NEEDS_CONTEXT."""
    a = make_asset("RSA", "asymmetric_encryption", key_length=2048)
    ctx = AssetContext() # All unknown
    res = assess_quantum_risk(a, context=ctx)

    assert res.technical_quantum_risk == RiskSeverity.CRITICAL
    assert res.hndl_assessment.status == HNDLStatus.UNKNOWN
    assert res.lifecycle_assessment.urgency == LifecycleUrgency.UNKNOWN
    assert res.overall_priority == "NEEDS_CONTEXT"
    assert len(res.explanation.missing_information) >= 3


def test_edge_case_02_rsa_short_data_lifetime():
    """2. RSA + short data lifetime (1 year) -> Low Mosca lifecycle urgency."""
    a = make_asset("RSA", "asymmetric_encryption", key_length=2048)
    ctx = AssetContext.from_dict({
        "data_lifetime_years": 1.0,
        "data_sensitivity": "HIGH",
        "business_criticality": "HIGH",
        "internet_exposed": False,
    })
    policy = RiskPolicyConfig(quantum_horizon_years=10.0, default_migration_lead_time_years=3.0)
    # P = C + M = 1 + 3 = 4 years < Y (10 years). Delta = 6 years safety margin.
    res = assess_quantum_risk(a, context=ctx, policy=policy)

    assert res.lifecycle_assessment.urgency == LifecycleUrgency.LOW
    assert res.lifecycle_assessment.safety_margin_years == 6.0


def test_edge_case_03_rsa_long_data_lifetime():
    """3. RSA + long data lifetime (15 years) -> Critical Mosca lifecycle urgency (C+M > Y)."""
    a = make_asset("RSA", "asymmetric_encryption", key_length=2048)
    ctx = AssetContext.from_dict({
        "data_lifetime_years": 15.0,
        "data_sensitivity": "HIGH",
        "business_criticality": "HIGH",
        "internet_exposed": False,
    })
    policy = RiskPolicyConfig(quantum_horizon_years=10.0, default_migration_lead_time_years=3.0)
    # P = 15 + 3 = 18 years > Y (10 years). Deficit = 8 years.
    res = assess_quantum_risk(a, context=ctx, policy=policy)

    assert res.lifecycle_assessment.urgency == LifecycleUrgency.CRITICAL
    assert res.overall_priority == "IMMEDIATE_ACTION"


def test_edge_case_04_rsa_high_business_criticality():
    """4. RSA + high business criticality."""
    a = make_asset("RSA", "asymmetric_encryption", key_length=2048)
    ctx = AssetContext.from_dict({
        "business_criticality": "CRITICAL",
        "data_sensitivity": "CONFIDENTIAL",
        "data_lifetime_years": 10.0,
    })
    res = assess_quantum_risk(a, context=ctx)
    assert res.context_criticality == BusinessCriticality.CRITICAL


def test_edge_case_05_rsa_hndl_exposure():
    """5. RSA + HNDL (High sensitivity + long lifetime + internet exposure)."""
    a = make_asset("RSA", "asymmetric_encryption", key_length=2048)
    ctx = AssetContext.from_dict({
        "data_sensitivity": "CRITICAL",
        "data_lifetime_years": 10.0,
        "internet_exposed": True,
        "business_criticality": "HIGH",
    })
    res = assess_quantum_risk(a, context=ctx)
    assert res.hndl_assessment.status == HNDLStatus.CRITICAL
    assert res.overall_priority == "IMMEDIATE_ACTION"


def test_edge_case_06_ecdsa_shor_signature():
    """6. ECDSA -> Shor vulnerable, but NOT HNDL confidentiality candidate."""
    a = make_asset("ECDSA", "digital_signature")
    ctx = AssetContext.from_dict({
        "data_sensitivity": "CRITICAL",
        "data_lifetime_years": 10.0,
        "internet_exposed": True,
    })
    res = assess_quantum_risk(a, context=ctx)
    assert res.quantum_threat.threat_type == QuantumThreatType.SHOR
    assert res.hndl_assessment.status == HNDLStatus.NOT_APPLICABLE
    assert "digital_signature" in res.hndl_assessment.exposure_summary.lower() or "signature" in res.hndl_assessment.reasons[0].lower()


def test_edge_case_07_ecdh_shor_key_exchange():
    """7. ECDH -> Shor vulnerable key exchange, HNDL risk applicable."""
    a = make_asset("ECDH", "key_exchange")
    ctx = AssetContext.from_dict({
        "data_sensitivity": "CRITICAL",
        "data_lifetime_years": 10.0,
        "internet_exposed": True,
        "business_criticality": "HIGH",
    })
    res = assess_quantum_risk(a, context=ctx)
    assert res.quantum_threat.threat_type == QuantumThreatType.SHOR
    assert res.hndl_assessment.status == HNDLStatus.CRITICAL


def test_edge_case_08_aes_128_grover():
    """8. AES-128 -> Grover threat, reduced 64-bit security margin."""
    a = make_asset("AES", "symmetric_encryption", key_length=128, mode="GCM")
    res = assess_quantum_risk(a)
    assert res.quantum_threat.threat_type == QuantumThreatType.GROVER
    assert res.quantum_threat.security_margin_bits == 64
    assert res.hndl_assessment.status == HNDLStatus.NOT_APPLICABLE


def test_edge_case_09_aes_256_quantum_safe():
    """9. AES-256 -> Quantum resistant under modeled Grover threat."""
    a = make_asset("AES", "symmetric_encryption", key_length=256, mode="GCM")
    res = assess_quantum_risk(a)
    assert res.quantum_threat.quantum_resistant is True
    assert res.quantum_threat.security_margin_bits == 128


def test_edge_case_10_sha1_legacy_hashing():
    """10. SHA-1 -> Classical weakness, HIGH technical risk, no quantum threat."""
    a = make_asset("SHA-1", "hashing")
    res = assess_quantum_risk(a)
    assert res.technical_quantum_risk == RiskSeverity.HIGH
    assert res.quantum_threat.threat_type == QuantumThreatType.NONE


def test_edge_case_11_sha256_modern_hash():
    """11. SHA-256 -> INFO risk, quantum resistant hash."""
    a = make_asset("SHA-256", "hashing")
    res = assess_quantum_risk(a)
    assert res.technical_quantum_risk == RiskSeverity.INFO
    assert res.quantum_threat.quantum_resistant is True


def test_edge_case_12_unknown_algorithm():
    """12. Unknown algorithm -> Medium technical risk, unknown quantum threat."""
    a = make_asset("CustomCipher3000", "symmetric_encryption")
    res = assess_quantum_risk(a)
    assert res.technical_quantum_risk == RiskSeverity.MEDIUM
    assert res.quantum_threat.threat_type == QuantumThreatType.NONE


def test_edge_case_13_missing_data_lifetime():
    """13. Missing data lifetime -> Mosca urgency UNKNOWN."""
    a = make_asset("RSA", "asymmetric_encryption", key_length=2048)
    ctx = AssetContext.from_dict({"data_sensitivity": "HIGH"})
    res = assess_quantum_risk(a, context=ctx)
    assert res.lifecycle_assessment.urgency == LifecycleUrgency.UNKNOWN


def test_edge_case_14_missing_business_criticality():
    """14. Missing business criticality -> Context criticality UNKNOWN."""
    a = make_asset("RSA", "asymmetric_encryption", key_length=2048)
    res = assess_quantum_risk(a, context=AssetContext())
    assert res.context_criticality == BusinessCriticality.UNKNOWN


def test_edge_case_15_unknown_internet_exposure():
    """15. Unknown internet exposure -> Explicitly captured as missing info."""
    a = make_asset("RSA", "asymmetric_encryption", key_length=2048)
    ctx = AssetContext.from_dict({"data_sensitivity": "HIGH", "data_lifetime_years": 10.0})
    res = assess_quantum_risk(a, context=ctx)
    assert "internet_exposed (Unknown - network exposure unconfirmed)" in res.explanation.missing_information


def test_edge_case_16_conflicting_context_sources():
    """16. Conflicting context sources -> User source overrides derived/config source."""
    derived_ctx = AssetContext.from_dict({"environment": {"value": "TEST", "source": "derived", "confidence": 0.8}})
    user_ctx = AssetContext.from_dict({"environment": {"value": "PRODUCTION", "source": "user", "confidence": 1.0}})

    merged = derived_ctx.merge(user_ctx)
    assert merged.environment.value == Environment.PRODUCTION
    assert merged.environment.source == ContextSource.USER


def test_edge_case_17_invalid_configuration():
    """17. Invalid configuration -> Raises ValueError on validation."""
    with pytest.raises(ValueError):
        RiskPolicyConfig(quantum_horizon_years=-5.0)


def test_edge_case_18_deterministic_repeated_assessment():
    """18. Deterministic repeated assessment -> Same input produces exact same output."""
    a = make_asset("RSA", "asymmetric_encryption", key_length=2048)
    ctx = AssetContext.from_dict({"data_sensitivity": "CRITICAL", "data_lifetime_years": 10.0, "internet_exposed": True})
    policy = RiskPolicyConfig()

    res1 = assess_quantum_risk(a, context=ctx, policy=policy)
    res2 = assess_quantum_risk(a, context=ctx, policy=policy)

    # Compare serialized output excluding timestamp
    dict1 = res1.to_dict()
    dict2 = res2.to_dict()
    del dict1["calculated_at"]
    del dict2["calculated_at"]

    assert dict1 == dict2


# ==============================================================================
# API ENDPOINT INTEGRATION TESTS
# ==============================================================================

def test_api_context_and_risk_endpoints(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "main.py").write_text("from Crypto.PublicKey import RSA\nkey = RSA.generate(2048)\n", encoding="utf-8")

    # 1. Run scan
    scan_resp = client.post("/api/v1/scan", json={"target_path": str(repo)})
    assert scan_resp.status_code == 200
    data = scan_resp.json()
    assert len(data["findings"]) > 0
    asset_id = data["findings"][0]["finding_id"]

    # Verify Phase 2 enriched structure in scan response
    finding = data["findings"][0]
    assert "context" in finding
    assert "quantum_risk_intelligence" in finding

    # 2. Update context via POST /api/v1/context
    ctx_update_resp = client.post("/api/v1/context", json={
        "asset_id": asset_id,
        "context": {
            "data_sensitivity": "CRITICAL",
            "data_lifetime_years": 12.0,
            "internet_exposed": True,
            "business_criticality": "HIGH",
        }
    })
    assert ctx_update_resp.status_code == 200

    # 3. Fetch context via GET /api/v1/assets/{asset_id}/context
    get_ctx_resp = client.get(f"/api/v1/assets/{asset_id}/context")
    assert get_ctx_resp.status_code == 200
    assert get_ctx_resp.json()["context"]["data_sensitivity"]["value"] == "CRITICAL"

    # 4. Re-run scan with injected context and verify HNDL and Mosca urgency updates
    scan_resp2 = client.post("/api/v1/scan", json={
        "target_path": str(repo),
        "user_context_map": {
            asset_id: {
                "data_sensitivity": "CRITICAL",
                "data_lifetime_years": 12.0,
                "internet_exposed": True,
                "business_criticality": "HIGH",
            }
        }
    })
    assert scan_resp2.status_code == 200
    finding2 = scan_resp2.json()["findings"][0]
    qri2 = finding2["quantum_risk_intelligence"]
    assert qri2["hndl_assessment"]["status"] == "CRITICAL"
    assert qri2["lifecycle_assessment"]["urgency"] == "CRITICAL"
    assert qri2["overall_priority"] == "IMMEDIATE_ACTION"

    # 5. Test summary endpoints
    summary_resp = client.get("/api/v1/risk/summary")
    assert summary_resp.status_code == 200
    assert "hndl_counts" in summary_resp.json()["summary"]

    quantum_resp = client.get("/api/v1/risk/quantum")
    assert quantum_resp.status_code == 200
    assert quantum_resp.json()["shor_vulnerable_count"] >= 1

    hndl_resp = client.get("/api/v1/risk/hndl")
    assert hndl_resp.status_code == 200
    assert hndl_resp.json()["hndl_candidates_count"] >= 1
