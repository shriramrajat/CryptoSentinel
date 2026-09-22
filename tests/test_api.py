import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from api.main import app

client = TestClient(app)


@pytest.fixture
def temp_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "encrypt.py").write_text(
        "from Crypto.PublicKey import RSA\nprivate_key = RSA.generate(2048)\n",
        encoding="utf-8",
    )
    (repo / "legacy.py").write_text(
        "import hashlib\ndigest = hashlib.md5(b'legacy')\n",
        encoding="utf-8",
    )
    return repo


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_version_endpoint():
    response = client.get("/version")
    assert response.status_code == 200
    assert response.json()["version"] == "0.1.0"


def test_invalid_target_path():
    response = client.post("/api/v1/scan", json={"target_path": "/does/not/exist"})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_INPUT"


def test_scan_response_shape(temp_repo):
    response = client.post("/api/v1/scan", json={"target_path": str(temp_repo)})
    assert response.status_code == 200
    data = response.json()
    assert {"summary", "findings", "errors", "skipped_files", "metadata"} <= data.keys()
    assert data["summary"]["total_crypto_assets"] >= 2
    assert data["metadata"]["scanner_version"] == "0.2.0"

    for finding in data["findings"]:
        assert {"finding_id", "algorithm", "category", "file_location", "evidence", "risk"} <= finding.keys()
        assert {"file_path", "line_number", "code_snippet", "detection_mechanism", "matched_rule_id"} <= finding["evidence"].keys()
        assert {"severity", "reason", "confidence", "quantum_threat", "pqc_recommendation"} <= finding["risk"].keys()


def test_language_filter(temp_repo):
    response = client.post(
        "/api/v1/scan",
        json={"target_path": str(temp_repo), "language_filters": ["python"]},
    )
    assert response.status_code == 200
    assert all(f["file_location"]["file_path"].endswith(".py") for f in response.json()["findings"])


from unittest.mock import patch
from ecdat.service import ScannerError, AnalysisError

def test_scanner_error_handler():
    local_client = TestClient(app, raise_server_exceptions=False)
    with patch("api.routes.ScanService.run_scan", side_effect=ScannerError("mock_scanner_error")):
        response = local_client.post("/api/v1/scan", json={"target_path": "/fake/path"})
        assert response.status_code == 500
        assert response.json()["error"]["code"] == "SCANNER_FAILURE"
        assert "mock_scanner_error" not in response.json()["error"]["message"]

def test_analysis_error_handler():
    local_client = TestClient(app, raise_server_exceptions=False)
    with patch("api.routes.ScanService.run_scan", side_effect=AnalysisError("mock_analysis_error")):
        response = local_client.post("/api/v1/scan", json={"target_path": "/fake/path"})
        assert response.status_code == 500
        assert response.json()["error"]["code"] == "ANALYSIS_FAILURE"
        assert "mock_analysis_error" not in response.json()["error"]["message"]

def test_global_exception_handler():
    local_client = TestClient(app, raise_server_exceptions=False)
    with patch("api.routes.ScanService.run_scan", side_effect=Exception("mock_generic_error")):
        response = local_client.post("/api/v1/scan", json={"target_path": "/fake/path"})
        assert response.status_code == 500
        assert response.json()["error"]["code"] == "INTERNAL_ERROR"
        assert "mock_generic_error" not in response.json()["error"]["message"]


def test_successful_scan_then_invalid_scan_clears_active_cache_and_preserves_inventory(temp_repo):
    # 1. Successful scan
    resp1 = client.post("/api/v1/scan", json={"target_path": str(temp_repo)})
    assert resp1.status_code == 200
    assert resp1.json()["summary"]["total_crypto_assets"] >= 2

    # Verify active cache has findings
    summary_resp1 = client.get("/api/v1/risk/summary")
    assert summary_resp1.status_code == 200

    # 2. Invalid scan
    resp2 = client.post("/api/v1/scan", json={"target_path": "/invalid/nonexistent/directory"})
    assert resp2.status_code == 400
    assert resp2.json()["error"]["code"] == "INVALID_INPUT"

    # 3. Active cache must be cleared (no stale active results)
    summary_resp2 = client.get("/api/v1/risk/summary")
    assert summary_resp2.status_code == 200
    assert summary_resp2.json().get("status") == "no_scan_performed"


    # 4. Enterprise Inventory must preserve the previous successful scan assets
    inv_resp = client.get("/api/v1/inventory")
    assert inv_resp.status_code == 200
    assert inv_resp.json().get("total_assets", 0) >= 2



def test_invalid_scan_then_successful_scan(temp_repo):
    # 1. Invalid scan
    resp1 = client.post("/api/v1/scan", json={"target_path": "/invalid/path/first"})
    assert resp1.status_code == 400

    # 2. Subsequent successful scan populates active result state correctly
    resp2 = client.post("/api/v1/scan", json={"target_path": str(temp_repo)})
    assert resp2.status_code == 200
    assert resp2.json()["summary"]["total_crypto_assets"] >= 2

    summary_resp = client.get("/api/v1/risk/summary")
    assert summary_resp.status_code == 200
