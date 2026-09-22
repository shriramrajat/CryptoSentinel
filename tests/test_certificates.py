import sys
from pathlib import Path
import pytest

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ecdat.scanner import Scanner
from ecdat.detectors.certificates import scan_certificate_file, _parse_certificate
from ecdat.models import CryptoAsset, CertificateMetadata, KeyMetadata

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def test_certificate_parser_invalid_data():
    sample_path = Path("fake_path.pem")
    assets = scan_certificate_file(sample_path, "invalid pem data")
    assert assets == []


def test_certificate_parser_with_sample_pem():
    sample_pem = FIXTURES_DIR / "sample_keys.pem"
    # Mandatory assertion: fixture must exist and fail loudly if missing
    assert sample_pem.exists(), f"Required fixture missing: {sample_pem}"

    scanner = Scanner(root_dir=sample_pem.parent)
    assets = scanner.scan_file(sample_pem)

    assert len(assets) >= 2
    for asset in assets:
        assert asset.category == "certificate_or_key"
        assert asset.language == "pem"
        assert asset.file_path == "sample_keys.pem"


def test_substantive_x509_certificate_metadata():
    """Verify rich X.509 certificate metadata extraction and risk signals."""
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID
    import datetime

    # Generate synthetic in-memory test X.509 certificate
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, "test.sentinel.internal"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "CryptoSentinel Test Org"),
    ])
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(days=1))
        .not_valid_after(now + datetime.timedelta(days=365))
        .add_extension(
            x509.SubjectAlternativeName([x509.DNSName("test.sentinel.internal")]),
            critical=False,
        )
        .sign(private_key, hashes.SHA256())
    )

    cert_pem = cert.public_bytes(serialization.Encoding.PEM).decode("utf-8")
    key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")

    combined_pem = f"{cert_pem}\n{key_pem}"
    fake_path = Path("test_cert.pem")

    assets = scan_certificate_file(fake_path, combined_pem)
    assert len(assets) == 2

    cert_asset = next(a for a in assets if a.crypto_role == "certificate")
    assert cert_asset.certificate_metadata is not None
    cm = cert_asset.certificate_metadata

    assert "test.sentinel.internal" in cm.subject
    assert "CryptoSentinel Test Org" in cm.subject
    assert "test.sentinel.internal" in cm.issuer
    assert "CryptoSentinel Test Org" in cm.issuer
    assert cm.serial_number is not None
    assert cm.public_key_algorithm == "RSA"
    assert cm.public_key_size == 2048
    assert cm.fingerprint_sha256 is not None
    assert cm.is_expired is False
    assert cm.is_weak_key is False
    assert cm.is_weak_sig is False
    assert "test.sentinel.internal" in cm.subject_alt_names

    key_asset = next(a for a in assets if a.crypto_role == "key")
    assert key_asset.key_metadata is not None
    km = key_asset.key_metadata
    assert km.key_type == "RSA"
    assert km.key_size == 2048
    assert km.private_material == "not_stored"  # Security invariant


def test_malformed_certificate_input_degrades_gracefully():
    malformed_pem = """
    -----BEGIN CERTIFICATE-----
    ThisIsNotValidBase64Data12345!@#$%
    -----END CERTIFICATE-----
    """
    assets = scan_certificate_file(Path("bad.pem"), malformed_pem)
    assert assets == []
