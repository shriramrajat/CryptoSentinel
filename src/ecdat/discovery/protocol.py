"""Deterministic protocol configuration and token discovery."""

import re
from pathlib import Path

from .base import AdvancedDiscoveryResult, DiscoveryError, DiscoveryFinding, validate_file


class ProtocolScanner:
    MAX_FILE_SIZE = 8 * 1024 * 1024
    TLS_RE = re.compile(r"TLS\s*(1\.[23])(?:\s+|[-:])([A-Z0-9-]+)?", re.I)
    SSH_RE = re.compile(r"(?:HostKeyAlgorithms|KexAlgorithms|Ciphers)\s*[= ]\s*([^\s#]+)", re.I)
    JWT_RE = re.compile(r"\b(JWS|JWE|JWT)\b|alg\s*[=:]\s*[\"']?([A-Za-z0-9_-]+)", re.I)

    def scan(self, path: str) -> AdvancedDiscoveryResult:
        source = validate_file(path, self.MAX_FILE_SIZE)
        text = source.read_text(encoding="utf-8", errors="replace")
        result = AdvancedDiscoveryResult("protocol", source.as_posix())
        for match in self.TLS_RE.finditer(text):
            suite = match.group(2) or "UNKNOWN"
            parts = suite.split("-")
            metadata = {"protocol": "TLS", "version": match.group(1), "cipher_suite": suite, "key_exchange": parts[0] if parts and parts[0] != "UNKNOWN" else "UNKNOWN", "authentication": "RSA" if "RSA" in parts else "UNKNOWN", "cipher": next((part for part in parts if part in {"AES256", "AES128", "CHACHA20"}), "UNKNOWN"), "hash": next((part for part in parts if part.startswith("SHA")), "UNKNOWN")}
            result.protocols.append(metadata)
            result.add_finding(DiscoveryFinding("protocol", source.as_posix(), "TLS", match.group(0), 0.9, "protocol_parser", "protocol-tls", metadata=metadata, identity_inputs=[match.group(0)]))
        for match in self.SSH_RE.finditer(text):
            metadata = {"protocol": "SSH", "configuration": match.group(0), "value": match.group(1)}
            result.protocols.append(metadata)
            result.add_finding(DiscoveryFinding("protocol", source.as_posix(), "SSH", match.group(0), 0.85, "protocol_parser", "protocol-ssh", metadata=metadata, identity_inputs=[match.group(0)]))
        for match in self.JWT_RE.finditer(text):
            indicator = match.group(1) or match.group(2)
            if indicator:
                metadata = {"protocol": indicator.upper(), "algorithm": match.group(2) or "UNKNOWN"}
                result.protocols.append(metadata)
                result.add_finding(DiscoveryFinding("protocol", source.as_posix(), indicator.upper(), match.group(0), 0.8, "protocol_parser", "protocol-jwt", metadata=metadata, identity_inputs=[match.group(0)]))
        return result
