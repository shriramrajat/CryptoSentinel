"""Bounded binary indicator scanner; it never executes a binary."""

from pathlib import Path
from typing import Dict, List, Tuple

from .base import AdvancedDiscoveryResult, DiscoveryError, DiscoveryFinding, validate_file


class BinaryScanner:
    MAX_FILE_SIZE = 64 * 1024 * 1024
    CHUNK_SIZE = 1024 * 1024
    LIBRARIES = {
        b"libcrypto": "OpenSSL", b"libssl": "OpenSSL", b"LibreSSL": "LibreSSL",
        b"BoringSSL": "BoringSSL", b"libsodium": "libsodium", b"mbedTLS": "mbedTLS", b"wolfSSL": "wolfSSL",
    }
    SYMBOLS = {
        b"EVP_EncryptInit_ex": "AES", b"EVP_aes_256_gcm": "AES", b"EVP_sha1": "SHA-1",
        b"EVP_sha256": "SHA-256", b"RSA_generate_key_ex": "RSA", b"ECDH_compute_key": "ECDH",
        b"sodium_init": "libsodium", b"mbedtls_ssl_init": "mbedTLS",
    }

    def scan(self, path: str) -> AdvancedDiscoveryResult:
        binary = validate_file(path, self.MAX_FILE_SIZE)
        with binary.open("rb") as stream:
            header = stream.read(4)
        fmt = "ELF" if header == b"\x7fELF" else "PE" if header[:2] == b"MZ" else "UNKNOWN"
        result = AdvancedDiscoveryResult("binary", binary.as_posix())
        if fmt == "UNKNOWN":
            result.errors.append("UNSUPPORTED_BINARY_FORMAT")
            return result
        result.relationships.append({"type": "DISCOVERED_IN", "source": binary.as_posix(), "target": fmt})
        data = bytearray()
        with binary.open("rb") as stream:
            while chunk := stream.read(self.CHUNK_SIZE):
                data.extend(chunk)
        for marker, library in self.LIBRARIES.items():
            if marker in data:
                result.add_finding(self._finding(binary, marker.decode(errors="replace"), library, "library_reference", 0.65, fmt))
        for marker, algorithm in self.SYMBOLS.items():
            if marker in data:
                result.add_finding(self._finding(binary, marker.decode(errors="replace"), algorithm, "imported_symbol", 0.8, fmt, observed=True))
        for algorithm in ("AES", "RSA", "ECDSA", "SHA-1", "SHA-256", "SHA-512", "Ed25519", "ECDH"):
            if algorithm.encode() in data:
                result.add_finding(self._finding(binary, algorithm, algorithm, "algorithm_string", 0.55, fmt))
        for finding in result.findings:
            result.assets.append(finding_to_dict(finding))
        return result

    @staticmethod
    def _finding(path: Path, indicator: str, value: str, mechanism: str, confidence: float, fmt: str, observed: bool = False) -> DiscoveryFinding:
        from .base import stable_id
        return DiscoveryFinding("binary", path.as_posix(), indicator, indicator, confidence, mechanism,
            rule_id=f"binary-{mechanism}", metadata={"algorithm": value if value not in ("OpenSSL", "LibreSSL", "BoringSSL", "libsodium", "mbedTLS", "wolfSSL") else "UNKNOWN", "library": value, "format": fmt},
            identity_inputs=[fmt, mechanism, indicator], observation_type="DIRECTLY_OBSERVED" if observed else "INFERRED_FROM_BINARY_INDICATOR")


def finding_to_dict(finding: DiscoveryFinding) -> Dict[str, object]:
    return finding.to_dict()
