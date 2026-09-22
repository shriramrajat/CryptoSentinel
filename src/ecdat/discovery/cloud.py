"""Cloud crypto reference discovery (Phase 6, Track B).
Detects AWS KMS/CloudHSM/ACM, Azure Key Vault/Managed HSM,
GCP Cloud KMS/HSM from static source code, IaC, config files.
All findings are REFERENCE_ONLY or CONFIGURED. NEVER LIVE_VERIFIED.
No credentials are collected or required.
"""
from __future__ import annotations
import re
from pathlib import Path
from typing import Any, Dict, List
from .base import AdvancedDiscoveryResult, DiscoveryError, DiscoveryFinding, validate_file

_RULES: List[Dict[str, Any]] = [
    # AWS
    {"p": re.compile(r"kms\.amazonaws\.com|aws_kms|KMSClient|aws-kms|AWSKMSClient", re.I),
     "provider": "AWS", "service": "KMS", "obs": "REFERENCE_ONLY", "c": 0.85, "rule": "cloud-aws-kms"},
    {"p": re.compile(r"cloudhsm|CloudHSMClient|aws-cloudhsm", re.I),
     "provider": "AWS", "service": "CloudHSM", "obs": "REFERENCE_ONLY", "c": 0.85, "rule": "cloud-aws-cloudhsm"},
    {"p": re.compile(r"acm\.amazonaws\.com|CertificateManagerClient|aws-acm|ACMClient", re.I),
     "provider": "AWS", "service": "ACM", "obs": "REFERENCE_ONLY", "c": 0.82, "rule": "cloud-aws-acm"},
    {"p": re.compile(r"secretsmanager\.amazonaws\.com|SecretsManagerClient", re.I),
     "provider": "AWS", "service": "SecretsManager", "obs": "REFERENCE_ONLY", "c": 0.75, "rule": "cloud-aws-sm"},
    {"p": re.compile(r"arn:aws:kms:[\w-]+:\d+:key/[\w-]+", re.I),
     "provider": "AWS", "service": "KMS", "obs": "CONFIGURED", "c": 0.92, "rule": "cloud-aws-kms-arn"},
    {"p": re.compile(r"arn:aws:acm:", re.I),
     "provider": "AWS", "service": "ACM", "obs": "CONFIGURED", "c": 0.92, "rule": "cloud-aws-acm-arn"},
    # Azure
    {"p": re.compile(r"azurerm_key_vault|vault\.azure\.net|KeyVaultClient|azure-keyvault|AzureKeyVault", re.I),
     "provider": "Azure", "service": "KeyVault", "obs": "REFERENCE_ONLY", "c": 0.85, "rule": "cloud-azure-kv"},
    {"p": re.compile(r"managedhsm\.azure\.net|ManagedHsmClient", re.I),
     "provider": "Azure", "service": "ManagedHSM", "obs": "REFERENCE_ONLY", "c": 0.85, "rule": "cloud-azure-mhsm"},
    {"p": re.compile(r"Microsoft\.KeyVault|azure\.keyvault", re.I),
     "provider": "Azure", "service": "KeyVault", "obs": "REFERENCE_ONLY", "c": 0.80, "rule": "cloud-azure-kv-sdk"},
    # GCP
    {"p": re.compile(r"cloudkms\.googleapis\.com|CloudKMSClient|google-cloud-kms", re.I),
     "provider": "GCP", "service": "CloudKMS", "obs": "REFERENCE_ONLY", "c": 0.85, "rule": "cloud-gcp-kms"},
    {"p": re.compile(r"privateca\.googleapis\.com|CertificateManagerClient.*google", re.I),
     "provider": "GCP", "service": "CertificateManager", "obs": "REFERENCE_ONLY", "c": 0.80, "rule": "cloud-gcp-certmgr"},
    {"p": re.compile(r"projects/[\w-]+/locations/[\w-]+/keyRings/", re.I),
     "provider": "GCP", "service": "CloudKMS", "obs": "CONFIGURED", "c": 0.92, "rule": "cloud-gcp-kms-ref"},
]

def _mk(src: Path, rule: Dict[str, Any], snippet: str, line: int) -> DiscoveryFinding:
    return DiscoveryFinding(
        source_type="cloud", source_location=src.as_posix(),
        indicator=f"{rule['provider']}.{rule['service']}", evidence=snippet,
        confidence=rule["c"], detection_mechanism="cloud_reference_scan",
        rule_id=rule["rule"],
        metadata={"provider": rule["provider"], "service": rule["service"],
                  "observation_type": rule["obs"], "line": line,
                  "path": src.as_posix(), "provenance": "cloud_iac",
                  "asset_type": "CLOUD_CRYPTO_SERVICE"},
        identity_inputs=[src.as_posix(), rule["rule"], str(line)],
        observation_type=rule["obs"])

class CloudScanner:
    """Static cloud crypto reference scanner. Never contacts cloud APIs or collects credentials."""
    MAX_FILE_SIZE = 8 * 1024 * 1024

    def scan(self, path: str) -> AdvancedDiscoveryResult:
        src = validate_file(path, self.MAX_FILE_SIZE)
        result = AdvancedDiscoveryResult("cloud", src.as_posix())
        try:
            lines = src.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError as exc:
            raise DiscoveryError(str(exc)) from exc
        for lineno, txt in enumerate(lines, 1):
            for rule in _RULES:
                if rule["p"].search(txt):
                    result.add_finding(_mk(src, rule, txt.strip()[:200], lineno))
        return result
