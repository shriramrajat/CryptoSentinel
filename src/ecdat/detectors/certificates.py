"""
Certificate Intelligence Detector for ECDAT.
Parses X.509 certificates and cryptographic key files to extract structured metadata.
Raw private key material is never stored in the output.
"""

from pathlib import Path
from typing import List, Optional, Union
from datetime import datetime, timezone


def scan_certificate_file(
    file_path: Path,
    content: str,
    root_dir: Optional[Union[str, Path]] = None,
) -> List:
    """
    Parse a PEM/DER/CRT/KEY file and return CryptoAsset objects with rich metadata.
    Falls back to regex-based detection if the cryptography library is unavailable
    or the file cannot be parsed as a valid X.509 certificate.
    Raw private key bytes are never included in any output field.
    """
    from ecdat.models import CryptoAsset, CertificateMetadata, KeyMetadata

    assets: List[CryptoAsset] = []

    try:
        from cryptography import x509
        from cryptography.hazmat.primitives import serialization, hashes
        from cryptography.hazmat.primitives.asymmetric import rsa, ec, dsa, dh
        from cryptography.x509 import NameOID
        from cryptography.exceptions import InvalidSignature
        import hashlib
    except ImportError:
        # cryptography library not available — fallback handled by scanner.py
        return []

    pem_blocks = _split_pem_blocks(content)

    for lineno, pem_type, pem_data in pem_blocks:
        if pem_type == "CERTIFICATE":
            asset = _parse_certificate(file_path, content, pem_data, lineno, root_dir)
            if asset:
                assets.append(asset)

        elif pem_type in ("RSA PRIVATE KEY", "EC PRIVATE KEY", "PRIVATE KEY", "DSA PRIVATE KEY",
                          "OPENSSH PRIVATE KEY", "PUBLIC KEY", "RSA PUBLIC KEY"):
            asset = _parse_key_file(file_path, content, pem_data, pem_type, lineno, root_dir)
            if asset:
                assets.append(asset)

    return assets


def _split_pem_blocks(content: str) -> List[tuple]:
    """
    Extract (line_number, pem_type, pem_bytes) from a PEM file that may contain multiple blocks.
    """
    import base64

    blocks = []
    lines = content.splitlines()
    current_type = None
    current_b64_lines = []
    start_lineno = 1

    for lineno, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("-----BEGIN "):
            current_type = stripped[11:].rstrip("-").strip()
            current_b64_lines = []
            start_lineno = lineno
        elif stripped.startswith("-----END "):
            if current_type and current_b64_lines:
                try:
                    raw = base64.b64decode("".join(current_b64_lines))
                    blocks.append((start_lineno, current_type, raw))
                except Exception:
                    pass
            current_type = None
            current_b64_lines = []
        elif current_type:
            # Skip PEM headers (e.g. Proc-Type, DEK-Info)
            if ":" not in stripped:
                current_b64_lines.append(stripped)

    return blocks


def _parse_certificate(
    file_path: Path,
    raw_content: str,
    der_bytes: bytes,
    lineno: int,
    root_dir: Optional[Union[str, Path]],
) -> Optional[object]:
    """Parse a single DER-encoded X.509 certificate and return a CryptoAsset."""
    from ecdat.models import CryptoAsset, CertificateMetadata
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa, ec, dsa
    from cryptography.x509.oid import SignatureAlgorithmOID
    import hashlib

    try:
        cert = x509.load_der_x509_certificate(der_bytes)
    except Exception:
        return None

    # Extract subject / issuer
    subject = _name_to_str(cert.subject)
    issuer = _name_to_str(cert.issuer)
    serial_number = str(cert.serial_number)

    # Validity window
    not_before = cert.not_valid_before_utc.isoformat() if hasattr(cert, "not_valid_before_utc") else _compat_dt(cert.not_valid_before)
    not_after = cert.not_valid_after_utc.isoformat() if hasattr(cert, "not_valid_after_utc") else _compat_dt(cert.not_valid_after)
    now_utc = datetime.now(timezone.utc)
    is_expired = cert.not_valid_after_utc < now_utc if hasattr(cert, "not_valid_after_utc") else False

    # Signature algorithm
    sig_algo = _sig_algo_name(cert)
    is_weak_sig = sig_algo.upper() in {"SHA1WITHRSAENCRYPTION", "MD5WITHRSAENCRYPTION",
                                        "SHA-1", "SHA1", "MD5", "MD2"}

    # Public key analysis
    pub_key = cert.public_key()
    pk_algo, pk_size = _pub_key_info(pub_key)
    is_weak_key = _is_weak_key(pub_key, pk_algo, pk_size)

    # Subject Alternative Names
    sans: List[str] = []
    try:
        san_ext = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName)
        sans = [str(gn.value) for gn in san_ext.value]
    except x509.ExtensionNotFound:
        pass
    except Exception:
        pass

    # Fingerprint (SHA-256 of DER bytes)
    fingerprint = hashlib.sha256(der_bytes).hexdigest()

    # Risk signals
    cert_meta = CertificateMetadata(
        subject=subject,
        issuer=issuer,
        serial_number=serial_number,
        not_before=not_before,
        not_after=not_after,
        signature_algorithm=sig_algo,
        public_key_algorithm=pk_algo,
        public_key_size=pk_size,
        subject_alt_names=sans,
        fingerprint_sha256=fingerprint,
        is_expired=is_expired,
        is_weak_sig=is_weak_sig,
        is_weak_key=is_weak_key,
    )

    # Choose appropriate algorithm label and confidence
    # If cert uses a weak algorithm or has a weak key, flag it prominently
    algorithm = pk_algo if pk_algo else "Certificate"
    confidence = 0.95

    # Evidence snippet: first line of the PEM block
    lines = raw_content.splitlines()
    snippet = lines[lineno - 1].strip() if lineno <= len(lines) else "-----BEGIN CERTIFICATE-----"

    return CryptoAsset.create(
        name=f"X.509 Certificate ({pk_algo})",
        category="certificate_or_key",
        algorithm=algorithm,
        file_path=str(file_path),
        line_number=lineno,
        code_snippet=snippet,
        library="X.509",
        confidence=confidence,
        language="pem",
        detection_mechanism="x509_parse",
        matched_rule_id="PEM-CERTIFICATE-001",
        root_dir=root_dir,
        purpose="certificate_or_public_key",
        key_length=pk_size,
        certificate_metadata=cert_meta,
        crypto_role="certificate",
        detection_rule="PEM-CERTIFICATE-001",
    )


def _parse_key_file(
    file_path: Path,
    raw_content: str,
    der_bytes: bytes,
    pem_type: str,
    lineno: int,
    root_dir: Optional[Union[str, Path]],
) -> Optional[object]:
    """Parse a key file and return a CryptoAsset with metadata. Private material is never stored."""
    from ecdat.models import CryptoAsset, KeyMetadata
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa, ec, dsa

    key_type = "unknown"
    key_size = None

    # Load public key (safe, no private material)
    try:
        if pem_type in ("PUBLIC KEY", "RSA PUBLIC KEY"):
            pub_key = serialization.load_der_public_key(der_bytes)
            pk_algo, pk_size = _pub_key_info(pub_key)
            key_type = pk_algo
            key_size = pk_size
        else:
            # Private key: load to extract metadata ONLY; no bytes are stored
            priv_key = serialization.load_der_private_key(der_bytes, password=None)
            pub_key = priv_key.public_key()
            pk_algo, pk_size = _pub_key_info(pub_key)
            key_type = pk_algo
            key_size = pk_size
            # Immediately dereference — no raw material stored
            del priv_key
    except Exception:
        # Detect key type from PEM header if parsing fails
        if "RSA" in pem_type:
            key_type = "RSA"
        elif "EC" in pem_type:
            key_type = "ECC"
        elif "DSA" in pem_type:
            key_type = "DSA"
        elif "OPENSSH" in pem_type:
            key_type = "Ed25519"

    key_meta = KeyMetadata(
        key_type=key_type,
        key_size=key_size,
        private_material="not_stored",  # Security invariant: raw key bytes are never stored
    )

    # Algorithm for risk classification
    algorithm = key_type if key_type and key_type != "unknown" else "RSA"

    # Map PEM type to rule ID
    pem_rule_map = {
        "RSA PRIVATE KEY": "PEM-RSA-PRIVATE-KEY-001",
        "EC PRIVATE KEY": "PEM-EC-PRIVATE-KEY-001",
        "PRIVATE KEY": "PEM-PRIVATE-KEY-PKCS8-001",
        "DSA PRIVATE KEY": "PEM-DSA-PRIVATE-KEY-001",
        "OPENSSH PRIVATE KEY": "PEM-ED25519-PRIVATE-KEY-001",
        "PUBLIC KEY": "PEM-PUBLIC-KEY-001",
        "RSA PUBLIC KEY": "PEM-PUBLIC-KEY-001",
    }
    rule_id = pem_rule_map.get(pem_type, "PEM-RSA-PRIVATE-KEY-001")

    lines = raw_content.splitlines()
    snippet = lines[lineno - 1].strip() if lineno <= len(lines) else f"-----BEGIN {pem_type}-----"

    return CryptoAsset.create(
        name=f"Cryptographic Key ({key_type})",
        category="certificate_or_key",
        algorithm=algorithm,
        file_path=str(file_path),
        line_number=lineno,
        code_snippet=snippet,
        library="PEM",
        confidence=0.90,
        language="pem",
        detection_mechanism="x509_parse",
        matched_rule_id=rule_id,
        root_dir=root_dir,
        purpose="unknown",
        key_length=key_size,
        key_metadata=key_meta,
        crypto_role="key",
        detection_rule=rule_id,
    )


def _name_to_str(name) -> str:
    """Convert an X.509 Name to a human-readable string."""
    try:
        return name.rfc4514_string()
    except Exception:
        try:
            attrs = []
            for attr in name:
                attrs.append(f"{attr.oid.dotted_string}={attr.value}")
            return ", ".join(attrs)
        except Exception:
            return str(name)


def _sig_algo_name(cert) -> str:
    """Get a human-readable signature algorithm name from an X.509 certificate."""
    try:
        # Try the signature_algorithm_oid / hash_algorithm properties
        sig = cert.signature_hash_algorithm
        if sig:
            return sig.name.upper()
    except Exception:
        pass

    try:
        return cert.signature_algorithm_oid.dotted_string
    except Exception:
        return "unknown"


def _pub_key_info(pub_key) -> tuple:
    """Return (algorithm_name, key_size_bits) for a public key. Does not expose private material."""
    from cryptography.hazmat.primitives.asymmetric import rsa, ec, dsa, ed25519, ed448, x25519, x448
    try:
        if isinstance(pub_key, rsa.RSAPublicKey):
            return "RSA", pub_key.key_size
        elif isinstance(pub_key, ec.EllipticCurvePublicKey):
            return "ECC", pub_key.key_size
        elif isinstance(pub_key, dsa.DSAPublicKey):
            return "DSA", pub_key.key_size
        elif isinstance(pub_key, ed25519.Ed25519PublicKey):
            return "Ed25519", 256
        elif isinstance(pub_key, ed448.Ed448PublicKey):
            return "Ed448", 448
        elif isinstance(pub_key, x25519.X25519PublicKey):
            return "X25519", 255
        elif isinstance(pub_key, x448.X448PublicKey):
            return "X448", 448
    except Exception:
        pass
    return "unknown", None


def _is_weak_key(pub_key, algo: str, key_size: Optional[int]) -> bool:
    """Detect keys that are cryptographically weak."""
    if algo == "RSA" and key_size and key_size < 2048:
        return True
    if algo in ("DSA",) and key_size and key_size < 2048:
        return True
    return False


def _compat_dt(dt) -> str:
    """Compatibility wrapper for Python <3.11 datetime handling."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()
