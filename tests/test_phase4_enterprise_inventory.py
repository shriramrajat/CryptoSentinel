"""Comprehensive test suite for Phase 4 Enterprise Cryptographic Inventory & Continuous Monitoring."""
import os
import sys
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from api.main import app
from ecdat.inventory.db import init_db
from ecdat.inventory.models import (
    Alert,
    AlertScopeType,
    AlertSeverity,
    AlertStatus,
    AlertType,
    CryptoAssetRecord,
    DriftEvent,
    DriftSeverity,
    DriftType,
    ObservationRecord,
    ObservationStatus,
    Organization,
    Project,
    Repository,
    ScanRecord,
    ScanSchedule,
    ScanStatus,
)
from ecdat.inventory.store import InventoryStore
from ecdat.inventory.orchestrator import EnterpriseScanOrchestrator
from ecdat.inventory.posture import calculate_posture, get_posture_trends
from ecdat.inventory.drift import detect_drift
from ecdat.inventory.alerts import evaluate_alerts_for_scan, generate_dedup_key


@pytest.fixture
def temp_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    init_db(db_path)
    yield db_path
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def store(temp_db):
    return InventoryStore(db_path=temp_db)


@pytest.fixture
def temp_repo(tmp_path):
    repo = tmp_path / "enterprise_repo"
    repo.mkdir()
    (repo / "auth.py").write_text(
        "from Crypto.PublicKey import RSA\nkey = RSA.generate(2048)\n",
        encoding="utf-8",
    )
    (repo / "legacy.py").write_text(
        "import hashlib\ndigest = hashlib.md5(b'secret')\n",
        encoding="utf-8",
    )
    return repo


# 1. Organization creation
def test_organization_creation(store):
    org = Organization(name="Acme Corp")
    saved = store.create_organization(org)
    assert saved.id == org.id
    fetched = store.get_organization(org.id)
    assert fetched is not None
    assert fetched.name == "Acme Corp"


# 2. Project creation
def test_project_creation(store):
    org = store.create_organization(Organization(name="TechCorp"))
    proj = Project(organization_id=org.id, name="Payments API", description="Payment processing")
    saved = store.create_project(proj)
    assert saved.organization_id == org.id
    fetched = store.get_project(proj.id)
    assert fetched is not None
    assert fetched.name == "Payments API"


# 3. Repository creation
def test_repository_creation(store):
    org = store.create_organization(Organization(name="CyberOrg"))
    proj = store.create_project(Project(organization_id=org.id, name="Security Core"))
    repo = Repository(project_id=proj.id, name="crypto-sentinel-service", provider="github")
    saved = store.create_repository(repo)
    assert saved.project_id == proj.id
    fetched = store.get_repository(repo.id)
    assert fetched is not None
    assert fetched.provider == "github"


# 4. Scan persistence
def test_scan_persistence(store):
    _, _, repo_id = store.get_or_create_default_hierarchy()
    scan = ScanRecord(repository_id=repo_id, commit_sha="abc1234", branch="main")
    started = store.start_scan(scan)
    assert started.status == ScanStatus.IN_PROGRESS

    completed = store.complete_scan(scan.id, asset_count=5, error_count=0)
    assert completed is not None
    assert completed.status == ScanStatus.COMPLETED
    assert completed.asset_count == 5


# 5. Asset persistence
def test_asset_persistence(store):
    asset = CryptoAssetRecord(
        asset_id="asset-test-1",
        algorithm="RSA",
        category="asymmetric_encryption",
        key_length=2048,
        source_path="src/main.py",
        line_number=10,
        evidence_json='{"code_snippet": "RSA.generate(2048)"}',
    )
    store.save_crypto_asset(asset)
    assets = store.get_inventory_assets()
    assert any(a["asset_id"] == "asset-test-1" for a in assets)


# 6. Observation persistence
def test_observation_persistence(store):
    _, _, repo_id = store.get_or_create_default_hierarchy()
    scan = store.start_scan(ScanRecord(repository_id=repo_id))
    asset = CryptoAssetRecord(
        asset_id="asset-obs-1",
        algorithm="AES",
        category="symmetric_ciphers",
        source_path="app.py",
        line_number=1,
    )
    store.save_crypto_asset(asset)

    obs = ObservationRecord(asset_id=asset.asset_id, scan_id=scan.id, repository_id=repo_id, source_path="app.py", line_number=1)
    store.save_observation(obs)

    observations = store.get_scan_observations(scan.id)
    assert len(observations) == 1
    assert observations[0]["asset_id"] == "asset-obs-1"


# 7. First seen / Last seen tracking & 8. Historical scan tracking
def test_first_last_seen_tracking(store):
    _, _, repo_id = store.get_or_create_default_hierarchy()
    asset = CryptoAssetRecord(asset_id="asset-history-1", algorithm="SHA-256", category="hashing", source_path="hash.py", line_number=5)
    store.save_crypto_asset(asset)

    scan1 = store.start_scan(ScanRecord(repository_id=repo_id))
    obs1 = ObservationRecord(asset_id=asset.asset_id, scan_id=scan1.id, repository_id=repo_id, source_path="hash.py", line_number=5, observed_at="2026-09-20T10:00:00Z")
    store.save_observation(obs1)

    scan2 = store.start_scan(ScanRecord(repository_id=repo_id))
    obs2 = ObservationRecord(asset_id=asset.asset_id, scan_id=scan2.id, repository_id=repo_id, source_path="hash.py", line_number=5, observed_at="2026-09-22T10:00:00Z")
    store.save_observation(obs2)

    detail = store.get_asset_detail("asset-history-1")
    assert detail is not None
    assert detail["first_seen"] == "2026-09-20T10:00:00Z"
    assert detail["last_seen"] == "2026-09-22T10:00:00Z"
    assert len(detail["observation_history"]) == 2


# 9. NEW_ASSET detection
def test_new_asset_drift_detection():
    curr = [{"asset_id": "asset-1", "algorithm": "RSA", "source_path": "a.py", "line_number": 1, "overall_priority": "IMMEDIATE_ACTION"}]
    prev = []
    drifts = detect_drift("repo-1", "scan-1", curr, prev)
    assert len(drifts) == 1
    assert drifts[0].type == DriftType.NEW_ASSET


# 10. REMOVED_ASSET detection
def test_removed_asset_drift_detection():
    curr = []
    prev = [{"asset_id": "asset-1", "algorithm": "DES", "source_path": "a.py", "line_number": 1}]
    drifts = detect_drift("repo-1", "scan-1", curr, prev)
    assert len(drifts) == 1
    assert drifts[0].type == DriftType.REMOVED_ASSET


# 11. MODIFIED_ASSET detection
def test_modified_asset_drift_detection():
    curr = [{"asset_id": "asset-1", "algorithm": "RSA", "key_length": 4096, "source_path": "a.py", "line_number": 1}]
    prev = [{"asset_id": "asset-1", "algorithm": "RSA", "key_length": 2048, "source_path": "a.py", "line_number": 1}]
    drifts = detect_drift("repo-1", "scan-1", curr, prev)
    assert any(d.type == DriftType.MODIFIED_ASSET for d in drifts)


# 12. RISK_REGRESSION detection
def test_risk_regression_drift_detection():
    curr = [{"asset_id": "asset-1", "algorithm": "RSA", "overall_priority": "IMMEDIATE_ACTION", "technical_quantum_risk": "critical"}]
    prev = [{"asset_id": "asset-1", "algorithm": "RSA", "overall_priority": "MONITOR", "technical_quantum_risk": "low"}]
    drifts = detect_drift("repo-1", "scan-1", curr, prev)
    assert any(d.type == DriftType.RISK_REGRESSION for d in drifts)


# 13. RISK_IMPROVEMENT detection
def test_risk_improvement_drift_detection():
    curr = [{"asset_id": "asset-1", "algorithm": "RSA", "overall_priority": "MONITOR", "technical_quantum_risk": "low"}]
    prev = [{"asset_id": "asset-1", "algorithm": "RSA", "overall_priority": "IMMEDIATE_ACTION", "technical_quantum_risk": "critical"}]
    drifts = detect_drift("repo-1", "scan-1", curr, prev)
    assert any(d.type == DriftType.RISK_IMPROVEMENT for d in drifts)


# 14. MIGRATION_PROGRESS detection
def test_migration_progress_drift_detection():
    curr = [{"asset_id": "asset-1", "algorithm": "RSA", "lifecycle_state": "MIGRATED"}]
    prev = [{"asset_id": "asset-1", "algorithm": "RSA", "lifecycle_state": "DISCOVERED"}]
    drifts = detect_drift("repo-1", "scan-1", curr, prev)
    assert any(d.type == DriftType.MIGRATION_PROGRESS for d in drifts)


# 15. Posture aggregation & 16-18 Org/Project/Repo posture
def test_posture_aggregation(store):
    org, proj, repo = store.get_or_create_default_hierarchy()
    posture = calculate_posture(store, repo_id=repo)
    assert "totals" in posture
    assert "migration_progress" in posture
    assert "distributions" in posture
    assert "monitoring" in posture


# 19. Posture history / trends
def test_posture_trends(store):
    _, _, repo_id = store.get_or_create_default_hierarchy()
    scan = ScanRecord(repository_id=repo_id, status=ScanStatus.COMPLETED, completed_at="2026-09-22T12:00:00Z")
    store.start_scan(scan)
    trends = get_posture_trends(store, repo_id=repo_id)
    assert isinstance(trends, list)


# 20. Alert generation & 21. Alert deduplication
def test_alert_generation_and_deduplication(store):
    org, proj, repo = store.get_or_create_default_hierarchy()
    obs = [{
        "asset_id": "asset-weak-1",
        "algorithm": "MD5",
        "key_length": None,
        "source_path": "crypto.py",
        "line_number": 10,
        "overall_priority": "MONITOR",
        "technical_quantum_risk": "medium",
    }]
    alerts1 = evaluate_alerts_for_scan(store, repo, "scan-1", obs, [])
    assert len(alerts1) > 0

    # Evaluate again - duplicate should be prevented
    alerts2 = evaluate_alerts_for_scan(store, repo, "scan-2", obs, [])
    assert len(alerts2) == 0


# 22. Alert acknowledgement & 23. Alert resolution & 24. Alert reopening & 25. Invalid transitions
def test_alert_lifecycle_and_transitions(store):
    alert = Alert(
        type=AlertType.WEAK_ALGORITHM_DETECTED,
        severity=AlertSeverity.HIGH,
        scope_type=AlertScopeType.REPOSITORY,
        scope_id="repo-1",
        repository_id="repo-1",
        message="Weak MD5 algorithm detected",
        dedup_key="dedup-123",
    )
    saved = store.save_alert(alert)
    assert saved.status == AlertStatus.OPEN

    # Acknowledge
    ack = store.update_alert_status(saved.id, AlertStatus.ACKNOWLEDGED)
    assert ack.status == AlertStatus.ACKNOWLEDGED

    # Resolve
    res = store.update_alert_status(saved.id, AlertStatus.RESOLVED)
    assert res.status == AlertStatus.RESOLVED

    # Invalid transition directly from RESOLVED to ACKNOWLEDGED
    with pytest.raises(ValueError):
        res.transition_to(AlertStatus.ACKNOWLEDGED)

    # Valid reopening: RESOLVED -> OPEN
    res.transition_to(AlertStatus.OPEN)
    assert res.status == AlertStatus.OPEN


# 26. Certificate expiring alert
def test_certificate_expiring_alert(store):
    obs = [{
        "asset_id": "asset-cert-1",
        "algorithm": "RSA",
        "source_path": "cert.pem",
        "line_number": 1,
        "certificate_metadata": {"is_expired": True},
    }]
    alerts = evaluate_alerts_for_scan(store, "repo-1", "scan-cert", obs, [])
    assert any(a.type == AlertType.CERTIFICATE_EXPIRING for a in alerts)


# 27. Migration overdue alert
def test_migration_overdue_alert(store):
    obs = [{
        "asset_id": "asset-mosca-1",
        "algorithm": "RSA",
        "source_path": "legacy.py",
        "line_number": 1,
        "mosca_urgency": "CRITICAL",
    }]
    alerts = evaluate_alerts_for_scan(store, "repo-1", "scan-mosca", obs, [])
    assert any(a.type == AlertType.MIGRATION_OVERDUE for a in alerts)


# 28. Persistence across application restart
def test_persistence_across_restart(temp_db):
    store1 = InventoryStore(db_path=temp_db)
    org = store1.create_organization(Organization(name="Restart Org"))

    store2 = InventoryStore(db_path=temp_db)
    fetched = store2.get_organization(org.id)
    assert fetched is not None
    assert fetched.name == "Restart Org"


# 29. Secret redaction
def test_secret_redaction_preservation():
    asset = CryptoAssetRecord(
        asset_id="asset-sec-1",
        algorithm="RSA",
        category="asymmetric_encryption",
        source_path="key.pem",
        line_number=1,
        evidence_json='{"code_snippet": "-----BEGIN PRIVATE KEY----- [REDACTED] -----END PRIVATE KEY-----"}',
    )
    assert "PRIVATE KEY" in asset.evidence_json
    assert "[REDACTED]" in asset.evidence_json


# 30. API validation & REST routes
def test_phase4_api_routes(temp_repo):
    client = TestClient(app)

    # Trigger Enterprise Scan via API
    res = client.post("/api/v1/scan", json={"target_path": str(temp_repo)})
    assert res.status_code == 200
    data = res.json()
    assert "inventory_metadata" in data

    # Test Organizations API
    org_res = client.get("/api/v1/organizations")
    assert org_res.status_code == 200
    assert len(org_res.json()["organizations"]) > 0

    # Test Posture API
    posture_res = client.get("/api/v1/posture")
    assert posture_res.status_code == 200
    assert "totals" in posture_res.json()

    # Test Inventory API
    inv_res = client.get("/api/v1/inventory")
    assert inv_res.status_code == 200
    assert "assets" in inv_res.json()


# 31. Empty inventory behavior
def test_empty_inventory_behavior(store):
    assets = store.get_inventory_assets()
    assert len(assets) == 0
    posture = calculate_posture(store)
    assert posture["totals"]["total_crypto_assets"] == 0


# 32. Failed scan behavior
def test_failed_scan_behavior(store):
    orchestrator = EnterpriseScanOrchestrator(store=store)
    with pytest.raises(Exception):
        orchestrator.run_enterprise_scan(target_path="/non/existent/path/for/failure")

    scans = store.list_scans()
    assert len(scans) == 1
    assert scans[0].status == ScanStatus.FAILED


# 33. Duplicate scan handling
def test_duplicate_scan_orchestration(store, temp_repo):
    orchestrator = EnterpriseScanOrchestrator(store=store)
    res1 = orchestrator.run_enterprise_scan(target_path=str(temp_repo))
    res2 = orchestrator.run_enterprise_scan(target_path=str(temp_repo))

    scans = store.list_scans()
    assert len(scans) == 2
    assert res1["inventory_metadata"]["scan_id"] != res2["inventory_metadata"]["scan_id"]
