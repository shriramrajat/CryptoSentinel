"""
Classical-to-PQC and Hybrid Algorithm Mapping Engine for CryptoSentinel Phase 3.

Implements purpose-aware classical-to-PQC algorithm mapping while avoiding
incorrect PQC assignments to symmetric/hash primitives or unknown algorithms.
"""

from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, Any, List, Optional

from ecdat.models import CryptoAsset
from ecdat.pqc_kb import PQCAlgorithmInfo, PQC_KNOWLEDGE_BASE, get_default_pqc_for_primitive


class MigrationType(str, Enum):
    """Categorization of PQC migration strategy type."""
    DIRECT = "DIRECT"                      # Direct replacement with PQC primitive
    HYBRID = "HYBRID"                      # Dual classical + PQC transition mechanism
    INDIRECT = "INDIRECT"                  # Key size / mode upgrade (e.g. AES-128 -> AES-256)
    NO_DIRECT_EQUIVALENT = "NO_DIRECT_EQUIVALENT"  # Algorithm has no direct PQC equivalent
    NO_PQC_REPLACEMENT_NEEDED = "NO_PQC_REPLACEMENT_NEEDED"  # Primitive is quantum-resistant
    REVIEW_REQUIRED = "REVIEW_REQUIRED"    # Custom / unknown primitive requiring manual security review


@dataclass(frozen=True)
class HybridStrategy:
    """Structured dual classical + PQC hybrid migration strategy."""
    classical_component: str
    pqc_component: str
    combined_public_key_bytes: int
    combined_ciphertext_or_sig_bytes: int
    rationale: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MappingResult:
    """Result of deterministic classical-to-PQC algorithm and purpose mapping."""
    migration_type: MigrationType
    target_pqc_info: Optional[PQCAlgorithmInfo]
    hybrid_strategy: Optional[HybridStrategy]
    rationale: str
    alternative_pqc_info: Optional[PQCAlgorithmInfo] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "migration_type": self.migration_type.value,
            "target_pqc_info": self.target_pqc_info.to_dict() if self.target_pqc_info else None,
            "hybrid_strategy": self.hybrid_strategy.to_dict() if self.hybrid_strategy else None,
            "rationale": self.rationale,
            "alternative_pqc_info": self.alternative_pqc_info.to_dict() if self.alternative_pqc_info else None,
        }


def map_asset_to_pqc(asset: CryptoAsset) -> MappingResult:
    """Deterministically maps a CryptoAsset to an appropriate PQC / Hybrid target based on algorithm and purpose."""
    algo = asset.algorithm.strip().upper()
    cat = asset.category.strip().lower()

    # 1. Asymmetric Public-Key Cryptography (Shor targets)
    if algo in {"RSA", "ECC", "EC", "ECDSA", "ECDH", "DSA", "DH", "DIFFIE-HELLMAN"}:
        # Determine cryptographic purpose: Digital Signature vs Key Establishment / Encryption
        is_signature = (
            cat == "digital_signature" or
            algo in {"ECDSA", "DSA"}
        )
        is_key_exchange = (
            cat in {"asymmetric_encryption", "key_exchange", "hybrid_encryption", "certificate_or_key"} or
            algo in {"ECDH", "DH", "DIFFIE-HELLMAN"}
        )

        if is_signature:
            target_pqc = get_default_pqc_for_primitive("signature", category=3) # ML-DSA-65
            alt_pqc = PQC_KNOWLEDGE_BASE.get("slh-dsa-128s") # State-free fallback

            hybrid = HybridStrategy(
                classical_component=f"{algo} Signature",
                pqc_component="ML-DSA-65",
                combined_public_key_bytes=64 + 1952,
                combined_ciphertext_or_sig_bytes=64 + 3309,
                rationale="Dual ECDSA/RSA + ML-DSA-65 signature concatenation during transition phase.",
            )

            return MappingResult(
                migration_type=MigrationType.DIRECT,
                target_pqc_info=target_pqc,
                hybrid_strategy=hybrid,
                rationale=f"{algo} used for digital signatures is vulnerable to Shor's algorithm. Replace with NIST FIPS 204 ML-DSA-65.",
                alternative_pqc_info=alt_pqc,
            )

        elif is_key_exchange:
            target_pqc = get_default_pqc_for_primitive("kem", category=3) # ML-KEM-768
            alt_pqc = PQC_KNOWLEDGE_BASE.get("ml-kem-1024")

            hybrid = HybridStrategy(
                classical_component=f"ECDH (P-256)",
                pqc_component="ML-KEM-768",
                combined_public_key_bytes=64 + 1184,
                combined_ciphertext_or_sig_bytes=64 + 1088,
                rationale="Dual ECDH + ML-KEM-768 shared secret derivation (X25519MLKEM768 hybrid pattern).",
            )

            return MappingResult(
                migration_type=MigrationType.HYBRID if algo in {"ECDH", "DH"} else MigrationType.DIRECT,
                target_pqc_info=target_pqc,
                hybrid_strategy=hybrid,
                rationale=f"{algo} used for key establishment/encryption is vulnerable to Shor's algorithm. Migrate to NIST FIPS 203 ML-KEM-768 (or ECDH + ML-KEM-768 hybrid).",
                alternative_pqc_info=alt_pqc,
            )
        else: # Generic ECC/RSA without explicit category
            target_pqc = get_default_pqc_for_primitive("kem", category=3)
            return MappingResult(
                migration_type=MigrationType.DIRECT,
                target_pqc_info=target_pqc,
                hybrid_strategy=None,
                rationale=f"{algo} is an asymmetric primitive vulnerable to Shor's algorithm. Recommend ML-KEM-768 (Key Exchange) or ML-DSA-65 (Signature) depending on callsite role.",
                alternative_pqc_info=PQC_KNOWLEDGE_BASE.get("ml-dsa-65"),
            )

    # 2. Symmetric Ciphers (AES, 3DES, DES, RC4)
    if algo == "AES":
        if asset.key_length is not None and asset.key_length < 256:
            pqc_sym = PQC_KNOWLEDGE_BASE.get("aes-256-gcm")
            return MappingResult(
                migration_type=MigrationType.INDIRECT,
                target_pqc_info=pqc_sym,
                hybrid_strategy=None,
                rationale=f"AES-{asset.key_length} provides a reduced post-quantum security margin under Grover's algorithm. Upgrade key size to 256 bits (AES-256-GCM).",
            )
        else: # AES-256
            pqc_sym = PQC_KNOWLEDGE_BASE.get("aes-256-gcm")
            return MappingResult(
                migration_type=MigrationType.NO_PQC_REPLACEMENT_NEEDED,
                target_pqc_info=pqc_sym,
                hybrid_strategy=None,
                rationale="AES-256 retains 128 bits of security under Grover's algorithm; no post-quantum replacement algorithm is needed.",
            )

    if algo in {"DES", "3DES", "TRIPLE-DES", "RC4"}:
        pqc_sym = PQC_KNOWLEDGE_BASE.get("aes-256-gcm")
        return MappingResult(
            migration_type=MigrationType.INDIRECT,
            target_pqc_info=pqc_sym,
            hybrid_strategy=None,
            rationale=f"{algo} is a cryptographically broken classical cipher. Replace directly with classical AES-256-GCM.",
        )

    # 3. Hash Functions (SHA-256, SHA-512, SHA-3, MD5, SHA-1)
    if algo in {"SHA-256", "SHA256", "SHA-512", "SHA512", "SHA-3", "SHA3"}:
        return MappingResult(
            migration_type=MigrationType.NO_PQC_REPLACEMENT_NEEDED,
            target_pqc_info=None,
            hybrid_strategy=None,
            rationale=f"{algo} is a modern collision-resistant hash function that remains quantum-resistant under Grover's search speedup.",
        )

    if algo in {"MD5", "SHA-1", "SHA1"}:
        return MappingResult(
            migration_type=MigrationType.INDIRECT,
            target_pqc_info=None,
            hybrid_strategy=None,
            rationale=f"{algo} is classically compromised. Upgrade to SHA-256 or SHA-3-256 (no PQC algorithm required).",
        )

    # 4. Unknown / Custom Primitives
    return MappingResult(
        migration_type=MigrationType.NO_DIRECT_EQUIVALENT,
        target_pqc_info=None,
        hybrid_strategy=None,
        rationale=f"No direct PQC mapping exists for primitive '{algo}'. Manual cryptographic review required.",
    )
