"""
PQC Knowledge Base for CryptoSentinel Phase 3.

Provides deterministic, authoritative parameters for NIST-standardized Post-Quantum
Cryptography algorithms under FIPS 203 (ML-KEM), FIPS 204 (ML-DSA), FIPS 205 (SLH-DSA),
and FIPS 197 (AES-256).
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional


@dataclass(frozen=True)
class PQCAlgorithmInfo:
    """Authoritative cryptographic metadata for a Post-Quantum algorithm."""
    id: str
    name: str
    family: str
    primitive: str  # "kem", "signature", "symmetric", "hash"
    nist_standard: str
    security_category: int  # 1 (AES-128 equivalent), 3 (AES-192), 5 (AES-256)
    public_key_size_bytes: int
    private_key_size_bytes: int
    ciphertext_or_signature_size_bytes: int
    supported_purposes: List[str]
    performance_profile: str
    migration_constraints: List[str]
    notes: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


PQC_KNOWLEDGE_BASE: Dict[str, PQCAlgorithmInfo] = {
    "ml-kem-768": PQCAlgorithmInfo(
        id="ml-kem-768",
        name="ML-KEM-768",
        family="ML-KEM",
        primitive="kem",
        nist_standard="FIPS 203",
        security_category=3,
        public_key_size_bytes=1184,
        private_key_size_bytes=2400,
        ciphertext_or_signature_size_bytes=1088,
        supported_purposes=["asymmetric_encryption", "key_exchange", "hybrid_encryption"],
        performance_profile="Fast encapsulation/decapsulation; modest memory requirement; recommended default for key establishment.",
        migration_constraints=["Public key size (1,184 B) and ciphertext (1,088 B) exceed classical ECDH (64 B).", "Requires KEM API refactoring for legacy direct RSA encryption calls."],
        notes="Primary NIST FIPS 203 Module-Lattice Key Encapsulation Mechanism standard."
    ),
    "ml-kem-512": PQCAlgorithmInfo(
        id="ml-kem-512",
        name="ML-KEM-512",
        family="ML-KEM",
        primitive="kem",
        nist_standard="FIPS 203",
        security_category=1,
        public_key_size_bytes=800,
        private_key_size_bytes=1632,
        ciphertext_or_signature_size_bytes=768,
        supported_purposes=["asymmetric_encryption", "key_exchange", "hybrid_encryption"],
        performance_profile="Lowest bandwidth ML-KEM variant; NIST Security Category 1.",
        migration_constraints=["Lower security margin than ML-KEM-768.", "Key/ciphertext size overhead compared to classical ECC."],
        notes="Targeted for constrained network or hardware environments requiring Category 1 security."
    ),
    "ml-kem-1024": PQCAlgorithmInfo(
        id="ml-kem-1024",
        name="ML-KEM-1024",
        family="ML-KEM",
        primitive="kem",
        nist_standard="FIPS 203",
        security_category=5,
        public_key_size_bytes=1568,
        private_key_size_bytes=3168,
        ciphertext_or_signature_size_bytes=1568,
        supported_purposes=["asymmetric_encryption", "key_exchange", "hybrid_encryption"],
        performance_profile="Highest security margin (Category 5); larger key overhead.",
        migration_constraints=["Public key and ciphertext overhead (1,568 B) may impact MTU-constrained UDP/TCP packets."],
        notes="Targeted for ultra-high security requirements matching AES-256 strength."
    ),
    "ml-dsa-65": PQCAlgorithmInfo(
        id="ml-dsa-65",
        name="ML-DSA-65",
        family="ML-DSA",
        primitive="signature",
        nist_standard="FIPS 204",
        security_category=3,
        public_key_size_bytes=1952,
        private_key_size_bytes=4032,
        ciphertext_or_signature_size_bytes=3309,
        supported_purposes=["digital_signature", "authentication"],
        performance_profile="Excellent signing speed; large signature size (3,309 B).",
        migration_constraints=["Signature size (3,309 B) is ~50x larger than ECDSA (64 B).", "X.509 certificate chain size will expand significantly."],
        notes="Primary NIST FIPS 204 Module-Lattice Digital Signature Standard."
    ),
    "ml-dsa-44": PQCAlgorithmInfo(
        id="ml-dsa-44",
        name="ML-DSA-44",
        family="ML-DSA",
        primitive="signature",
        nist_standard="FIPS 204",
        security_category=1,
        public_key_size_bytes=1312,
        private_key_size_bytes=2560,
        ciphertext_or_signature_size_bytes=2420,
        supported_purposes=["digital_signature", "authentication"],
        performance_profile="Category 1 digital signature; smaller signature than ML-DSA-65 (2,420 B).",
        migration_constraints=["Signature size (2,420 B) overhead.", "Lower security level than Category 3/5."],
        notes="Module-Lattice signature for Category 1 security compliance."
    ),
    "ml-dsa-87": PQCAlgorithmInfo(
        id="ml-dsa-87",
        name="ML-DSA-87",
        family="ML-DSA",
        primitive="signature",
        nist_standard="FIPS 204",
        security_category=5,
        public_key_size_bytes=2592,
        private_key_size_bytes=4896,
        ciphertext_or_signature_size_bytes=4627,
        supported_purposes=["digital_signature", "authentication"],
        performance_profile="Category 5 digital signature; maximum security margin.",
        migration_constraints=["Signature size (4,627 B) causes heavy network packet fragmentation."],
        notes="High-assurance digital signature standard."
    ),
    "slh-dsa-128s": PQCAlgorithmInfo(
        id="slh-dsa-128s",
        name="SLH-DSA-SHAKE-128s",
        family="SLH-DSA",
        primitive="signature",
        nist_standard="FIPS 205",
        security_category=1,
        public_key_size_bytes=32,
        private_key_size_bytes=64,
        ciphertext_or_signature_size_bytes=7856,
        supported_purposes=["digital_signature", "authentication", "firmware_signing"],
        performance_profile="State-free hash-based signature; compact keys (32 B); large signature size (7,856 B); slower signing.",
        migration_constraints=["Very large signature size (7,856 B).", "Slower signing throughput than lattice primitives."],
        notes="Conservative fallback signature standard based purely on hash security assumptions (Sphincs+)."
    ),
    "aes-256-gcm": PQCAlgorithmInfo(
        id="aes-256-gcm",
        name="AES-256-GCM",
        family="AES",
        primitive="symmetric",
        nist_standard="FIPS 197",
        security_category=5,
        public_key_size_bytes=0,
        private_key_size_bytes=32,
        ciphertext_or_signature_size_bytes=16,
        supported_purposes=["symmetric_encryption", "bulk_encryption"],
        performance_profile="Hardware accelerated (AES-NI); 128-bit quantum security floor under Grover attack.",
        migration_constraints=["Requires 256-bit key management.", "Requires 96-bit unique IV/nonce management for GCM."],
        notes="Approved post-quantum symmetric encryption standard."
    ),
}


def get_pqc_algorithm(alg_id: str) -> Optional[PQCAlgorithmInfo]:
    """Retrieves PQC algorithm info by case-insensitive ID."""
    return PQC_KNOWLEDGE_BASE.get(alg_id.strip().lower())


def get_default_pqc_for_primitive(primitive: str, category: int = 3) -> Optional[PQCAlgorithmInfo]:
    """Returns the default NIST PQC algorithm info for a given primitive ('kem' or 'signature')."""
    p = primitive.strip().lower()
    if p in ("kem", "key_exchange", "asymmetric_encryption"):
        if category == 1:
            return PQC_KNOWLEDGE_BASE.get("ml-kem-512")
        elif category == 5:
            return PQC_KNOWLEDGE_BASE.get("ml-kem-1024")
        return PQC_KNOWLEDGE_BASE.get("ml-kem-768")
    elif p in ("signature", "digital_signature", "authentication"):
        if category == 1:
            return PQC_KNOWLEDGE_BASE.get("ml-dsa-44")
        elif category == 5:
            return PQC_KNOWLEDGE_BASE.get("ml-dsa-87")
        return PQC_KNOWLEDGE_BASE.get("ml-dsa-65")
    elif p == "symmetric":
        return PQC_KNOWLEDGE_BASE.get("aes-256-gcm")
    return None
