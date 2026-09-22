"""Phase 6: Hardware crypto discovery tests."""
import pathlib, textwrap, tempfile, pytest
from ecdat.discovery.hardware import HardwareScanner, _RULES, _FNAME

def make_file(tmp_path, name, content):
    p = tmp_path / name
    p.write_text(textwrap.dedent(content), encoding="utf-8")
    return str(p)

class TestHardwareScannerPKCS11:
    def test_pkcs11_reference_detected(self, tmp_path):
        f = make_file(tmp_path, "openssl.cnf", "openssl_conf = openssl_init\n[pkcs11_sect]\nengine_id = pkcs11\n")
        result = HardwareScanner().scan(f)
        assert any("PKCS11" in fi.indicator or "pkcs11" in fi.rule_id for fi in result.findings)

    def test_softhsm_config_file_detected(self, tmp_path):
        f = make_file(tmp_path, "softhsm2.conf", "directories.tokendir = /var/lib/softhsm/tokens/\n")
        result = HardwareScanner().scan(f)
        assert any("SoftHSM" in fi.indicator for fi in result.findings)

    def test_vendor_hsm_reference(self, tmp_path):
        f = make_file(tmp_path, "cfg.conf", "hsm_provider=lunasa\n")
        result = HardwareScanner().scan(f)
        assert any("VendorHSM" in fi.indicator for fi in result.findings)

    def test_vendor_hsm_observation_type(self, tmp_path):
        f = make_file(tmp_path, "cfg.conf", "provider=safenet\n")
        result = HardwareScanner().scan(f)
        finding = next(fi for fi in result.findings if "VendorHSM" in fi.indicator)
        assert finding.observation_type == "REFERENCE_ONLY"

class TestHardwareScannerTPM:
    def test_tpm2_reference(self, tmp_path):
        f = make_file(tmp_path, "install.sh", "apt install tpm2-tools tpm2-tss\n")
        result = HardwareScanner().scan(f)
        assert any("TPM" in fi.indicator for fi in result.findings)

    def test_tpm_device_path(self, tmp_path):
        f = make_file(tmp_path, "tpm.conf", "device=/dev/tpm0\n")
        result = HardwareScanner().scan(f)
        assert any("TPM" in fi.indicator for fi in result.findings)

class TestHardwareScannerSmartCard:
    def test_opensc_reference(self, tmp_path):
        f = make_file(tmp_path, "app.conf", "pkcs11_module=opensc-pkcs11.so\n")
        result = HardwareScanner().scan(f)
        assert len(result.findings) > 0

class TestHardwareScannerAcceleration:
    def test_aesni_reference(self, tmp_path):
        f = make_file(tmp_path, "build.sh", "CFLAGS=-maes -mAES-NI\n")
        result = HardwareScanner().scan(f)
        assert any("AES-NI" in fi.indicator for fi in result.findings)

    def test_kernel_crypto_device(self, tmp_path):
        f = make_file(tmp_path, "setup.py", "fd = open('/dev/crypto', 'rb')\n")
        result = HardwareScanner().scan(f)
        assert any("KernelCrypto" in fi.indicator for fi in result.findings)

class TestHardwareScannerSecurity:
    def test_nonexistent_file_raises(self, tmp_path):
        with pytest.raises(ValueError):
            HardwareScanner().scan(str(tmp_path / "nonexistent.conf"))

    def test_oversized_file_raises(self, tmp_path):
        f = tmp_path / "big.conf"
        f.write_bytes(b"pkcs11 " * 1000000)
        scanner = HardwareScanner()
        scanner.MAX_FILE_SIZE = 100
        with pytest.raises(ValueError):
            scanner.scan(str(f))

    def test_findings_are_configured_or_reference_only(self, tmp_path):
        f = make_file(tmp_path, "crypto.conf",
            "pkcs11\ntpm2-tools\nopensc\nAES-NI\n/dev/crypto\nlunasa\n")
        result = HardwareScanner().scan(f)
        allowed = {"CONFIGURED", "REFERENCE_ONLY"}
        for fi in result.findings:
            assert fi.observation_type in allowed, f"Bad obs: {fi.observation_type}"

    def test_deduplication_same_rule_same_line(self, tmp_path):
        f = make_file(tmp_path, "dup.conf", "pkcs11\n")
        result = HardwareScanner().scan(f)
        ids = [fi.finding_id for fi in result.findings]
        assert len(ids) == len(set(ids))

    def test_confidence_bounds(self, tmp_path):
        f = make_file(tmp_path, "cfg.conf", "pkcs11\ntpm2-tools\nopensc\n")
        result = HardwareScanner().scan(f)
        for fi in result.findings:
            assert 0.0 <= fi.confidence <= 1.0
