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
    assert data["metadata"]["scanner_version"] == "0.1.0"

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
