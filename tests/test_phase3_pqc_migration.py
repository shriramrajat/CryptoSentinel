"""
Phase 3 PQC & Hybrid Migration Intelligence Comprehensive Test Suite.

Tests PQC Knowledge Base, classical-to-PQC mappings, purpose awareness, hybrid strategies,
migration constraints, 5-dimensional readiness, migration priority, roadmap lifecycle state machine,
what-if simulator, API endpoints, and all 20 mandatory test cases specified in requirement 24.
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
from ecdat.context import AssetContext, DataSensitivity, BusinessCriticality
from ecdat.pqc_kb import PQC_KNOWLEDGE_BASE, get_pqc_algorithm
from ecdat.pqc_mapping import map_asset_to_pqc, MigrationType
from ecdat.pqc_recommendation import generate_migration_recommendation
from ecdat.migration_readiness import evaluate_migration_readiness, ReadinessState
from ecdat.migration_priority import calculate_migration_priority, MigrationPriority
from ecdat.migration_lifecycle import MigrationRecord, LifecycleState, generate_migration_roadmap
from ecdat.migration_simulator import simulate_migration
from ecdat.risk import assess_quantum_risk

client = TestClient(app)


def make_asset(
    algorithm="RSA",
    category="asymmetric_encryption",
    key_length=2048,
    mode=None,
    padding=None,
    file_path="src/auth/crypto.py",
    line_number=10,
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
# 20 MANDATORY PHASE 3 TEST SCENARIOS
# ==============================================================================

def test_p3_01_rsa_signature_to_mldsa():
    """1. RSA signature -> ML-DSA-65."""
    a = make_asset("RSA", "digital_signature", key_length=2048)
    rec = generate_migration_recommendation(a)
    assert rec.recommended_algorithm == "ML-DSA-65"
    assert rec.recommended_family == "ML-DSA"
    assert rec.nist_standard == "FIPS 204"
    assert rec.migration_type == MigrationType.DIRECT


def test_p3_02_rsa_key_establishment_to_mlkem():
    """2. RSA key establishment -> ML-KEM-768."""
    a = make_asset("RSA", "asymmetric_encryption", key_length=2048)
    rec = generate_migration_recommendation(a)
    assert rec.recommended_algorithm == "ML-KEM-768"
    assert rec.recommended_family == "ML-KEM"
    assert rec.nist_standard == "FIPS 203"


def test_p3_03_ecdsa_to_mldsa():
    """3. ECDSA -> ML-DSA-65."""
    a = make_asset("ECDSA", "digital_signature")
    rec = generate_migration_recommendation(a)
    assert rec.recommended_algorithm == "ML-DSA-65"
    assert rec.migration_type == MigrationType.DIRECT
    assert rec.hybrid_strategy is not None


def test_p3_04_ecdh_to_mlkem():
    """4. ECDH -> ML-KEM-768."""
    a = make_asset("ECDH", "key_exchange")
    rec = generate_migration_recommendation(a)
    assert rec.recommended_algorithm == "ML-KEM-768"
    assert rec.hybrid_strategy is not None
    assert "ECDH" in rec.hybrid_strategy.classical_component


def test_p3_05_dh_to_mlkem():
    """5. Diffie-Hellman (DH) -> ML-KEM-768."""
    a = make_asset("DH", "key_exchange")
    rec = generate_migration_recommendation(a)
    assert rec.recommended_algorithm == "ML-KEM-768"


def test_p3_06_aes_128_indirect_upgrade():
    """6. AES-128 -> Symmetric assessment (INDIRECT key size upgrade to AES-256-GCM, no ML-KEM/ML-DSA)."""
    a = make_asset("AES", "symmetric_encryption", key_length=128, mode="GCM")
    rec = generate_migration_recommendation(a)
    assert rec.recommended_algorithm == "AES-256-GCM"
    assert rec.migration_type == MigrationType.INDIRECT
    assert rec.recommended_family == "AES"


def test_p3_07_aes_256_no_pqc_needed():
    """7. AES-256 -> NO_PQC_REPLACEMENT_NEEDED."""
    a = make_asset("AES", "symmetric_encryption", key_length=256, mode="GCM")
    rec = generate_migration_recommendation(a)
    assert rec.migration_type == MigrationType.NO_PQC_REPLACEMENT_NEEDED


def test_p3_08_sha1_legacy_hashing():
    """8. SHA-1 -> Indirect replacement with classical SHA-256 (no PQC algorithm)."""
    a = make_asset("SHA-1", "hashing")
    rec = generate_migration_recommendation(a)
    assert rec.migration_type == MigrationType.INDIRECT


def test_p3_09_sha256_quantum_resistant_hash():
    """9. SHA-256 -> NO_PQC_REPLACEMENT_NEEDED."""
    a = make_asset("SHA-256", "hashing")
    rec = generate_migration_recommendation(a)
    assert rec.migration_type == MigrationType.NO_PQC_REPLACEMENT_NEEDED


def test_p3_10_unknown_algorithm():
    """10. Unknown algorithm -> NO_DIRECT_EQUIVALENT."""
    a = make_asset("CustomCipher9000", "symmetric_encryption")
    rec = generate_migration_recommendation(a)
    assert rec.migration_type == MigrationType.NO_DIRECT_EQUIVALENT


def test_p3_11_unknown_purpose():
    """11. Unknown purpose -> Generic asymmetric mapping handling."""
    a = make_asset("RSA", "unknown_category")
    rec = generate_migration_recommendation(a)
    assert rec.recommended_algorithm == "ML-KEM-768"
    assert rec.alternative_recommendation == "ML-DSA-65"


def test_p3_12_unknown_protocol():
    """12. Unknown protocol handling in constraints."""
    a = make_asset("RSA", "asymmetric_encryption")
    ctx = AssetContext.from_dict({"internet_exposed": False})
    rec = generate_migration_recommendation(a, context=ctx)
    assert rec.constraints.protocol_compatibility_risk is False


def test_p3_13_missing_context_handling():
    """13. Missing context -> Lower recommendation confidence, checklist note in readiness."""
    a = make_asset("RSA", "asymmetric_encryption")
    ctx = AssetContext() # All UNKNOWN
    rec = generate_migration_recommendation(a, context=ctx)
    readiness = evaluate_migration_readiness(a, context=ctx, recommendation=rec)
    assert rec.confidence < a.confidence
    assert readiness.state in (ReadinessState.PARTIALLY_READY, ReadinessState.READY_FOR_PLANNING)


def test_p3_14_high_criticality_asset_priority():
    """14. High-criticality asset migration priority -> CRITICAL / HIGH."""
    a = make_asset("RSA", "asymmetric_encryption", key_length=2048)
    ctx = AssetContext.from_dict({
        "business_criticality": "CRITICAL",
        "data_sensitivity": "CRITICAL",
        "data_lifetime_years": 10.0,
        "internet_exposed": True,
    })
    qri = assess_quantum_risk(a, context=ctx)
    rec = generate_migration_recommendation(a, context=ctx, risk_assessment=qri)
    priority = calculate_migration_priority(qri, ctx, rec.constraints)
    assert priority == MigrationPriority.CRITICAL


def test_p3_15_hndl_asset_migration_priority_and_roadmap():
    """15. HNDL asset migration priority & roadmap generation."""
    a = make_asset("RSA", "asymmetric_encryption", key_length=2048)
    ctx = AssetContext.from_dict({
        "data_sensitivity": "CRITICAL",
        "data_lifetime_years": 12.0,
        "internet_exposed": True,
        "business_criticality": "HIGH",
    })
    qri = assess_quantum_risk(a, context=ctx)
    rec = generate_migration_recommendation(a, context=ctx, risk_assessment=qri)
    priority = calculate_migration_priority(qri, ctx, rec.constraints)
    roadmap = generate_migration_roadmap(a, rec, current_state=LifecycleState.DISCOVERED)

    assert priority == MigrationPriority.CRITICAL
    assert len(roadmap) == 6
    assert roadmap[0].completed is True


def test_p3_16_hybrid_migration_candidate():
    """16. Hybrid migration candidate generation (ECDH + ML-KEM)."""
    a = make_asset("ECDH", "key_exchange")
    rec = generate_migration_recommendation(a)
    assert rec.hybrid_strategy is not None
    assert rec.hybrid_strategy.classical_component == "ECDH (P-256)"
    assert rec.hybrid_strategy.pqc_component == "ML-KEM-768"
    assert rec.hybrid_strategy.combined_public_key_bytes == 64 + 1184


def test_p3_17_unsupported_candidate_simulation():
    """17. Unsupported candidate simulation validation."""
    a = make_asset("RSA", "asymmetric_encryption")
    sim = simulate_migration(a, "FakeAlgorithm3000")
    assert sim.projected_security_posture == "UNKNOWN"
    assert "Unsupported candidate algorithm" in sim.compatibility_risk


def test_p3_18_invalid_lifecycle_transition_rejection():
    """18. Invalid migration lifecycle transition rejection (DISCOVERED -> VERIFIED fails)."""
    record = MigrationRecord(asset_id="crypto-12345", current_state=LifecycleState.DISCOVERED)
    with pytest.raises(ValueError):
        record.transition_to(LifecycleState.VERIFIED)

    # Valid step-by-step transitions pass
    assert record.transition_to(LifecycleState.ASSESSED) is True
    assert record.transition_to(LifecycleState.PLANNED) is True


def test_p3_19_repeated_identical_simulation():
    """19. Repeated identical simulation determinism."""
    a = make_asset("ECDSA", "digital_signature")
    sim1 = simulate_migration(a, "ML-DSA-65")
    sim2 = simulate_migration(a, "ML-DSA-65")
    assert sim1.to_dict() == sim2.to_dict()


def test_p3_20_conflicting_constraints():
    """20. Conflicting constraints handling (ML-DSA-65 signature size vs MTU)."""
    a = make_asset("ECDSA", "digital_signature")
    ctx = AssetContext.from_dict({"internet_exposed": True, "environment": "PRODUCTION"})
    rec = generate_migration_recommendation(a, context=ctx)
    assert rec.constraints.packet_fragmentation_risk is True
    assert rec.constraints.deployment_complexity == "HIGH"


# ==============================================================================
# PHASE 3 REST API INTEGRATION TESTS
# ==============================================================================

def test_phase3_api_endpoints(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "auth.py").write_text("from Crypto.PublicKey import RSA\nkey = RSA.generate(2048)\n", encoding="utf-8")

    # 1. Run scan
    scan_resp = client.post("/api/v1/scan", json={"target_path": str(repo)})
    assert scan_resp.status_code == 200
    data = scan_resp.json()
    finding = data["findings"][0]
    asset_id = finding["finding_id"]

    assert "migration_intelligence" in finding
    assert "migration_priority_counts" in data["summary"]

    # 2. GET /api/v1/assets/{asset_id}/migration
    mig_resp = client.get(f"/api/v1/assets/{asset_id}/migration")
    assert mig_resp.status_code == 200
    assert mig_resp.json()["migration_intelligence"]["recommendation"]["recommended_algorithm"] == "ML-KEM-768"

    # 3. GET /api/v1/assets/{asset_id}/recommendations
    rec_resp = client.get(f"/api/v1/assets/{asset_id}/recommendations")
    assert rec_resp.status_code == 200
    assert rec_resp.json()["recommendation"]["recommended_algorithm"] == "ML-KEM-768"

    # 4. POST /api/v1/assets/{asset_id}/simulate-migration
    sim_resp = client.post(f"/api/v1/assets/{asset_id}/simulate-migration", json={"candidate_algorithm": "ML-KEM-768"})
    assert sim_resp.status_code == 200
    sim_data = sim_resp.json()["simulation"]
    assert sim_data["candidate_algorithm"] == "ML-KEM-768"
    assert "PROJECTED / SIMULATED" in sim_data["simulation_disclaimer"]

    # 5. GET /api/v1/migration/summary
    sum_resp = client.get("/api/v1/migration/summary")
    assert sum_resp.status_code == 200
    assert "migration_priority_counts" in sum_resp.json()["summary"]

    # 6. GET /api/v1/migration/roadmap
    road_resp = client.get("/api/v1/migration/roadmap")
    assert road_resp.status_code == 200
    assert road_resp.json()["total_assets"] >= 1

    # 7. PATCH /api/v1/assets/{asset_id}/migration-status
    patch_resp = client.patch(f"/api/v1/assets/{asset_id}/migration-status", json={"new_state": "ASSESSED"})
    assert patch_resp.status_code == 200
    assert patch_resp.json()["lifecycle_record"]["current_state"] == "ASSESSED"

    # Reject invalid jump to VERIFIED
    invalid_patch = client.patch(f"/api/v1/assets/{asset_id}/migration-status", json={"new_state": "VERIFIED"})
    assert invalid_patch.status_code == 400
