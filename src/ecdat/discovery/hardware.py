"""Hardware crypto discovery (Phase 6, Track A) -- static evidence only.
Finds PKCS#11/HSM, TPM, smart-card and hw-acceleration references.
All findings are CONFIGURED or REFERENCE_ONLY; never LIVE_VERIFIED.
"""
from __future__ import annotations
import re
from pathlib import Path
from typing import Any, Dict, List
from .base import AdvancedDiscoveryResult, DiscoveryError, DiscoveryFinding, validate_file

_RULES: List[Dict[str, Any]] = [
    {"p": re.compile(r"pkcs11|p11-kit|pkcs#11|libpkcs11", re.I),
     "tech": "PKCS11", "asset": "HSM_PKCS11", "obs": "CONFIGURED", "c": 0.82, "rule": "hw-pkcs11"},
    {"p": re.compile(r"softhsm|module\s*=\s*\S+\.so", re.I),
     "tech": "SoftHSM", "asset": "HSM_PKCS11", "obs": "CONFIGURED", "c": 0.88, "rule": "hw-softhsm"},
    {"p": re.compile(r"lunasa|safenet|thales|utimaco|ncipher|yubihsm", re.I),
     "tech": "VendorHSM", "asset": "HSM_VENDOR", "obs": "REFERENCE_ONLY", "c": 0.70, "rule": "hw-vendor-hsm"},
    {"p": re.compile(r"tpm2[-_]tools|tpm2[-_]tss|libtss2|tpmutil", re.I),
     "tech": "TPM2", "asset": "TPM", "obs": "REFERENCE_ONLY", "c": 0.80, "rule": "hw-tpm2"},
    {"p": re.compile(r"/dev/tpm|TrouSerS", re.I),
     "tech": "TPM", "asset": "TPM", "obs": "CONFIGURED", "c": 0.85, "rule": "hw-tpm-device"},
    {"p": re.compile(r"pcscd|pcsc-lite|opensc|libpcsclite|smart.?card", re.I),
     "tech": "SmartCard", "asset": "SMART_CARD", "obs": "REFERENCE_ONLY", "c": 0.72, "rule": "hw-smartcard"},
    {"p": re.compile(r"aesni|aes.?ni|AES-NI", re.I),
     "tech": "AES-NI", "asset": "HW_ACCEL", "obs": "REFERENCE_ONLY", "c": 0.65, "rule": "hw-aesni"},
    {"p": re.compile(r"intel.*qat|quickassist", re.I),
     "tech": "Intel-QAT", "asset": "HW_ACCEL", "obs": "REFERENCE_ONLY", "c": 0.72, "rule": "hw-qat"},
    {"p": re.compile(r"/dev/crypto|af_alg|AF_ALG", re.I),
     "tech": "KernelCrypto", "asset": "HW_ACCEL", "obs": "CONFIGURED", "c": 0.78, "rule": "hw-kernel-crypto"},
    {"p": re.compile(r"arm.?crypto|ARMv8.*crypto", re.I),
     "tech": "ARM-Crypto", "asset": "HW_ACCEL", "obs": "REFERENCE_ONLY", "c": 0.65, "rule": "hw-arm-crypto"},
]
_FNAME: List[Dict[str, Any]] = [
    {"p": re.compile(r"softhsm2?\.conf$", re.I), "tech": "SoftHSM", "asset": "HSM_PKCS11", "obs": "CONFIGURED", "c": 0.90, "rule": "hw-softhsm-file"},
    {"p": re.compile(r"p11-kit.*\.conf$|pkcs11.*\.conf$", re.I), "tech": "PKCS11", "asset": "HSM_PKCS11", "obs": "CONFIGURED", "c": 0.88, "rule": "hw-p11kit-file"},
    {"p": re.compile(r"tpm.*\.conf$|tcsd\.conf$", re.I), "tech": "TPM", "asset": "TPM", "obs": "CONFIGURED", "c": 0.85, "rule": "hw-tpm-file"},
    {"p": re.compile(r"opensc\.conf$", re.I), "tech": "SmartCard", "asset": "SMART_CARD", "obs": "CONFIGURED", "c": 0.87, "rule": "hw-opensc-file"},
]

def _mk(src: Path, rule: Dict[str, Any], snippet: str, line: int) -> DiscoveryFinding:
    return DiscoveryFinding(
        source_type="hardware", source_location=src.as_posix(),
        indicator=rule["tech"], evidence=snippet,
        confidence=rule["c"], detection_mechanism="hardware_config_scan",
        rule_id=rule["rule"],
        metadata={"asset_type": rule["asset"], "technology": rule["tech"],
                  "observation_type": rule["obs"], "line": line,
                  "path": src.as_posix(), "provenance": "hardware_config"},
        identity_inputs=[src.as_posix(), rule["rule"], str(line)],
        observation_type=rule["obs"])

class HardwareScanner:
    """Static hardware crypto reference scanner. Never executes code."""
    MAX_FILE_SIZE = 4 * 1024 * 1024

    def scan(self, path: str) -> AdvancedDiscoveryResult:
        src = validate_file(path, self.MAX_FILE_SIZE)
        result = AdvancedDiscoveryResult("hardware", src.as_posix())
        for rule in _FNAME:
            if rule["p"].search(src.name):
                result.add_finding(_mk(src, rule, f"filename:{src.name}", 0))
        try:
            lines = src.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError as exc:
            raise DiscoveryError(str(exc)) from exc
        for lineno, txt in enumerate(lines, 1):
            for rule in _RULES:
                if rule["p"].search(txt):
                    result.add_finding(_mk(src, rule, txt.strip()[:200], lineno))
        return result
