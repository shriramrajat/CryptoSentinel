"""
Internal Data Models for ECDAT Cryptographic Asset Discovery.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, Union
from pathlib import Path
import hashlib


def normalize_relative_path(file_path: Union[str, Path], root_dir: Optional[Union[str, Path]] = None) -> str:
    """
    Normalizes a file path to be relative to root_dir or CWD, using forward slashes.
    Ensures no machine-specific absolute paths (C:\\... or /home/...) remain.
    """
    path = Path(file_path)

    # 1. Try relative to root_dir if specified
    if root_dir:
        try:
            root_abs = Path(root_dir).resolve()
            path_abs = path.resolve()
            return path_abs.relative_to(root_abs).as_posix()
        except ValueError:
            pass

    # 2. Try relative to Current Working Directory (CWD)
    try:
        cwd = Path.cwd().resolve()
        path_abs = path.resolve()
        return path_abs.relative_to(cwd).as_posix()
    except ValueError:
        pass

    # 3. Fallback to posix path
    return path.as_posix()


@dataclass
class Evidence:
    """Structured evidence for a discovered cryptographic asset."""
    code_snippet: str
    detection_mechanism: str  # 'ast', 'regex', 'pem_header', 'x509_parse'
    matched_rule_id: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CertificateMetadata:
    """Structured metadata for X.509 certificates (no private key material stored)."""
    subject: Optional[str] = None
    issuer: Optional[str] = None
    serial_number: Optional[str] = None
    not_before: Optional[str] = None
    not_after: Optional[str] = None
    signature_algorithm: Optional[str] = None
    public_key_algorithm: Optional[str] = None
    public_key_size: Optional[int] = None
    subject_alt_names: Optional[list] = None
    fingerprint_sha256: Optional[str] = None
    is_expired: Optional[bool] = None
    is_weak_sig: Optional[bool] = None
    is_weak_key: Optional[bool] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if self.subject_alt_names is None:
            d["subject_alt_names"] = []
        return d


@dataclass
class KeyMetadata:
    """Metadata for cryptographic key files (raw private key material is never stored)."""
    key_type: Optional[str] = None
    key_size: Optional[int] = None
    private_material: str = "not_stored"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CryptoAsset:
    """Represents a discovered cryptographic asset in source code."""
    asset_id: str
    name: str
    category: str
    algorithm: str
    file_path: str
    line_number: int
    language: str
    library: str
    confidence: float
    evidence: Evidence

    # Optional algorithm parameters
    key_length: Optional[int] = None
    mode: Optional[str] = None
    padding: Optional[str] = None

    # Phase 1 extended context fields (all backward-compatible optional fields)
    purpose: Optional[str] = None          # e.g. 'encryption', 'signing', 'hashing', 'key_generation', 'unknown'
    protocol: Optional[str] = None         # e.g. 'TLS', 'SSH', 'JWT'
    crypto_role: Optional[str] = None      # e.g. 'primitive', 'protocol', 'key', 'certificate'
    detection_rule: Optional[str] = None   # Stable rule ID used for detection
    certificate_metadata: Optional[CertificateMetadata] = None
    key_metadata: Optional[KeyMetadata] = None

    @property
    def code_snippet(self) -> str:
        """Backward compatibility property returning the snippet from evidence."""
        return self.evidence.code_snippet if self.evidence else ""

    @classmethod
    def create(
        cls,
        name: str,
        category: str,
        algorithm: str,
        file_path: str,
        line_number: int,
        code_snippet: str,
        library: str,
        confidence: float,
        language: str = "python",
        detection_mechanism: str = "regex",
        matched_rule_id: str = "generic-rule",
        evidence: Optional[Evidence] = None,
        key_length: Optional[int] = None,
        mode: Optional[str] = None,
        padding: Optional[str] = None,
        asset_id: Optional[str] = None,
        root_dir: Optional[Union[str, Path]] = None,
        purpose: Optional[str] = None,
        protocol: Optional[str] = None,
        crypto_role: Optional[str] = None,
        detection_rule: Optional[str] = None,
        certificate_metadata: Optional[CertificateMetadata] = None,
        key_metadata: Optional[KeyMetadata] = None,
    ) -> "CryptoAsset":
        norm_path = normalize_relative_path(file_path, root_dir=root_dir)

        if evidence is None:
            evidence = Evidence(
                code_snippet=code_snippet.strip(),
                detection_mechanism=detection_mechanism,
                matched_rule_id=matched_rule_id,
            )

        if not asset_id:
            # Deterministic ID based on stable fields: path, line, algorithm, category, purpose, rule_id
            normalized_purpose = (purpose or "unknown").lower()
            raw_key = (
                f"{norm_path}:{line_number}:{algorithm.upper()}:"
                f"{category.lower()}:{normalized_purpose}:{evidence.matched_rule_id}"
            )
            digest = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:12]
            asset_id = f"crypto-{digest}"

        return cls(
            asset_id=asset_id,
            name=name,
            category=category,
            algorithm=algorithm,
            file_path=norm_path,
            line_number=line_number,
            language=language,
            library=library,
            confidence=round(confidence, 2),
            evidence=evidence,
            key_length=key_length,
            mode=mode,
            padding=padding,
            purpose=purpose,
            protocol=protocol,
            crypto_role=crypto_role,
            detection_rule=detection_rule or evidence.matched_rule_id,
            certificate_metadata=certificate_metadata,
            key_metadata=key_metadata,
        )

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["code_snippet"] = self.code_snippet
        # Flatten certificate/key metadata for easy consumption
        if self.certificate_metadata is not None:
            d["certificate_metadata"] = self.certificate_metadata.to_dict()
        if self.key_metadata is not None:
            d["key_metadata"] = self.key_metadata.to_dict()
        return d
