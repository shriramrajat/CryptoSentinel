"""Phase 6: Demo dataset exists and is scannable."""
import pathlib, pytest
from ecdat.discovery.hardware import HardwareScanner
from ecdat.discovery.cloud import CloudScanner
from ecdat.discovery.dependency import DependencyScanner
from ecdat.discovery.protocol import ProtocolScanner

DEMO = pathlib.Path("tests/fixtures/phase6_sih_demo")

def test_demo_dir_exists():
    assert DEMO.is_dir(), "Demo dataset directory missing"

def test_hardware_pkcs11_fixture_has_findings():
    f = DEMO / "hardware_pkcs11.conf"
    result = HardwareScanner().scan(str(f))
    assert len(result.findings) > 0

def test_hardware_tpm_fixture_has_findings():
    f = DEMO / "hardware_tpm.conf"
    result = HardwareScanner().scan(str(f))
    assert len(result.findings) > 0

def test_cloud_aws_fixture_has_findings():
    f = DEMO / "cloud_iac_aws.tf"
    result = CloudScanner().scan(str(f))
    assert any("AWS" in fi.indicator for fi in result.findings)

def test_cloud_azure_fixture_has_findings():
    f = DEMO / "cloud_iac_azure.tf"
    result = CloudScanner().scan(str(f))
    assert any("Azure" in fi.indicator for fi in result.findings)

def test_cloud_gcp_fixture_has_findings():
    f = DEMO / "cloud_iac_gcp.tf"
    result = CloudScanner().scan(str(f))
    assert any("GCP" in fi.indicator for fi in result.findings)

def test_requirements_fixture_parsed():
    f = DEMO / "requirements.txt"
    result = DependencyScanner().scan(str(f))
    assert len(result.dependencies) >= 3
    crypto_capable = [d for d in result.dependencies if d.get("capability") == "cryptographic"]
    assert len(crypto_capable) >= 2

def test_protocol_tls_fixture_parsed():
    f = DEMO / "protocol_tls.conf"
    result = ProtocolScanner().scan(str(f))
    assert len(result.protocols) > 0
