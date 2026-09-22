"""
Migration Constraints Engine for CryptoSentinel Phase 3.

Evaluates performance, key size, signature overhead, network packet fragmentation,
library availability, and deployment complexity constraints.
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional

from ecdat.context import AssetContext
from ecdat.models import CryptoAsset
from ecdat.pqc_kb import PQCAlgorithmInfo


@dataclass(frozen=True)
class MigrationConstraints:
    """Structured evaluation of constraints affecting a PQC migration."""
    key_size_overhead: bool
    ciphertext_or_sig_overhead: bool
    packet_fragmentation_risk: bool
    protocol_compatibility_risk: bool
    library_availability_risk: bool
    deployment_complexity: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    constraint_items: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def evaluate_migration_constraints(
    asset: CryptoAsset,
    context: AssetContext,
    target_pqc: Optional[PQCAlgorithmInfo],
) -> MigrationConstraints:
    """Evaluates constraints for migrating a CryptoAsset to target_pqc."""
    constraint_items: List[str] = []
    key_size_overhead = False
    ciphertext_or_sig_overhead = False
    packet_frag = False
    protocol_risk = False
    library_risk = False
    complexity = "LOW"

    if target_pqc is None:
        return MigrationConstraints(
            key_size_overhead=False,
            ciphertext_or_sig_overhead=False,
            packet_fragmentation_risk=False,
            protocol_compatibility_risk=False,
            library_availability_risk=False,
            deployment_complexity="LOW",
            constraint_items=["No PQC replacement candidate specified."],
        )

    # 1. Key Size & Signature Overhead Analysis
    pk_bytes = target_pqc.public_key_size_bytes
    sig_bytes = target_pqc.ciphertext_or_signature_size_bytes

    if pk_bytes > 500:
        key_size_overhead = True
        constraint_items.append(f"Public key size ({pk_bytes} B) is significantly larger than classical keys (64-512 B).")

    if sig_bytes > 1000:
        ciphertext_or_sig_overhead = True
        constraint_items.append(f"{'Signature' if target_pqc.primitive == 'signature' else 'Ciphertext'} size ({sig_bytes} B) causes memory & storage expansion.")

    if pk_bytes + sig_bytes > 1400:
        packet_frag = True
        constraint_items.append("Combined key/signature size exceeds typical 1,500 byte Ethernet MTU, risking IP packet fragmentation.")

    # 2. Language & Library Support Risk
    lang = asset.language.lower()
    lib = asset.library.lower()

    if lang in {"c", "cpp"} and "openssl" not in lib:
        library_risk = True
        constraint_items.append(f"C/C++ codebase using library '{asset.library}' requires OpenSSL 3.5+ or liboqs bindings for {target_pqc.name}.")
    elif lang in {"python", "java"}:
        library_risk = False
        constraint_items.append(f"Native or wrapper library bindings for {target_pqc.name} required in {lang.upper()}.")

    # 3. Environment & Internet Exposure Complexity
    env = context.environment.value
    exposed = context.internet_exposed.value

    if exposed is True:
        protocol_risk = True
        constraint_items.append("Internet-facing service requires external client/partner protocol negotiation before disabling classical cipher suites.")

    if env == "PRODUCTION" and exposed is True:
        complexity = "HIGH"
    elif env in ("PRODUCTION", "STAGING"):
        complexity = "MEDIUM"
    else:
        complexity = "LOW"

    if target_pqc.family == "SLH-DSA":
        complexity = "CRITICAL"
        constraint_items.append("SLH-DSA hash-based signatures exhibit high signing latency; performance profiling mandatory.")

    return MigrationConstraints(
        key_size_overhead=key_size_overhead,
        ciphertext_or_sig_overhead=ciphertext_or_sig_overhead,
        packet_fragmentation_risk=packet_frag,
        protocol_compatibility_risk=protocol_risk,
        library_availability_risk=library_risk,
        deployment_complexity=complexity,
        constraint_items=constraint_items,
    )
