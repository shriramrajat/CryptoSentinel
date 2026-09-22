"""Phase 6: Cloud crypto reference discovery tests."""
import textwrap, pytest
from ecdat.discovery.cloud import CloudScanner

def make_file(tmp_path, name, content):
    p = tmp_path / name
    p.write_text(textwrap.dedent(content), encoding="utf-8")
    return str(p)

class TestAWSKMS:
    def test_kms_hostname_detected(self, tmp_path):
        f = make_file(tmp_path, "aws.py", "endpoint = 'kms.amazonaws.com'\n")
        result = CloudScanner().scan(f)
        assert any("KMS" in fi.indicator for fi in result.findings)

    def test_kms_arn_detected_as_configured(self, tmp_path):
        f = make_file(tmp_path, "tf.tf",
            "key_arn = \"arn:aws:kms:us-east-1:123456789012:key/abc-def\"\n")
        result = CloudScanner().scan(f)
        kms = next(fi for fi in result.findings if "KMS" in fi.indicator)
        assert kms.observation_type == "CONFIGURED"

    def test_acm_arn_detected(self, tmp_path):
        f = make_file(tmp_path, "tf.tf", "cert_arn = \"arn:aws:acm:us-east-1:123:certificate/xyz\"\n")
        result = CloudScanner().scan(f)
        assert any("ACM" in fi.indicator for fi in result.findings)

    def test_cloudhsm_reference(self, tmp_path):
        f = make_file(tmp_path, "infra.py", "import CloudHSMClient\n")
        result = CloudScanner().scan(f)
        assert any("CloudHSM" in fi.indicator for fi in result.findings)

class TestAzureKeyVault:
    def test_keyvault_hostname(self, tmp_path):
        f = make_file(tmp_path, "az.py", "url = \"https://myvault.vault.azure.net/\"\n")
        result = CloudScanner().scan(f)
        assert any("KeyVault" in fi.indicator for fi in result.findings)

    def test_managed_hsm(self, tmp_path):
        f = make_file(tmp_path, "mhsm.conf", "endpoint=https://myhsm.managedhsm.azure.net\n")
        result = CloudScanner().scan(f)
        assert any("ManagedHSM" in fi.indicator for fi in result.findings)

class TestGCPKMS:
    def test_cloudkms_hostname(self, tmp_path):
        f = make_file(tmp_path, "gcp.py", "cloudkms.googleapis.com\n")
        result = CloudScanner().scan(f)
        assert any("CloudKMS" in fi.indicator for fi in result.findings)

    def test_kms_resource_path_configured(self, tmp_path):
        f = make_file(tmp_path, "gcp.tf",
            "key = \"projects/my-proj/locations/us-east1/keyRings/kr/cryptoKeys/k\"\n")
        result = CloudScanner().scan(f)
        gcp = next(fi for fi in result.findings if "CloudKMS" in fi.indicator)
        assert gcp.observation_type == "CONFIGURED"

class TestCloudScannerSecurity:
    def test_no_credentials_in_metadata(self, tmp_path):
        f = make_file(tmp_path, "code.py",
            "client = boto3.client('kms', aws_access_key_id='AKIA...', aws_secret_access_key='secret')\n")
        result = CloudScanner().scan(f)
        for fi in result.findings:
            meta_str = str(fi.metadata)
            assert "secret" not in meta_str.lower() or "access_key" not in meta_str.lower()

    def test_all_findings_not_live_verified(self, tmp_path):
        f = make_file(tmp_path, "all.py",
            "kms.amazonaws.com\nvault.azure.net\ncloudkms.googleapis.com\n")
        result = CloudScanner().scan(f)
        for fi in result.findings:
            assert fi.observation_type != "LIVE_VERIFIED"

    def test_nonexistent_file_raises(self, tmp_path):
        with pytest.raises(ValueError):
            CloudScanner().scan(str(tmp_path / "nofile.tf"))

    def test_confidence_within_bounds(self, tmp_path):
        f = make_file(tmp_path, "multi.tf",
            "kms.amazonaws.com\narn:aws:kms:us-east-1:111:key/abc\nvault.azure.net\n")
        result = CloudScanner().scan(f)
        for fi in result.findings:
            assert 0.0 <= fi.confidence <= 1.0
