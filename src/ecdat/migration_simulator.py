"""
What-If Migration Simulator Engine for CryptoSentinel Phase 3.

Provides deterministic simulation of candidate algorithm migration without mutating
production source code. Projects security posture, performance delta, key/signature overhead,
and remaining risks.
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional

from ecdat.context import AssetContext
from ecdat.models import CryptoAsset
from ecdat.pqc_kb import PQCAlgorithmInfo, PQC_KNOWLEDGE_BASE, get_pqc_algorithm
from ecdat.risk import QuantumRiskAssessment


@dataclass(frozen=True)
class SimulationResult:
    """Modeled projection resulting from a what-if migration simulation."""
    asset_id: str
    current_algorithm: str
    candidate_algorithm: str
    candidate_pqc_info: Optional[PQCAlgorithmInfo]
    projected_security_posture: str
    projected_quantum_risk: str
    key_size_delta_bytes: int
    ciphertext_or_sig_delta_bytes: int
    bandwidth_latency_impact: str
    compatibility_risk: str
    remaining_uncertainties: List[str]
    simulation_disclaimer: str = "PROJECTED / SIMULATED: This is a modeled projection and does not mutate production source code."

    def to_dict(self) -> Dict[str, Any]:
        res = asdict(self)
        if self.candidate_pqc_info:
            res["candidate_pqc_info"] = self.candidate_pqc_info.to_dict()
        return res


def simulate_migration(
    asset: CryptoAsset,
    candidate_algorithm: str,
    context: Optional[AssetContext] = None,
    current_risk: Optional[QuantumRiskAssessment] = None,
) -> SimulationResult:
    """Simulates the projected impact of migrating an asset to a candidate algorithm."""
    if context is None:
        context = AssetContext()

    cand_clean = candidate_algorithm.strip().lower().replace("_", "-")
    pqc_info = get_pqc_algorithm(cand_clean)

    curr_algo = asset.algorithm.strip().upper()
    remaining_uncertainties: List[str] = []

    if pqc_info is None:
        # Candidate algorithm is unknown or unsupported
        return SimulationResult(
            asset_id=asset.asset_id,
            current_algorithm=asset.algorithm,
            candidate_algorithm=candidate_algorithm,
            candidate_pqc_info=None,
            projected_security_posture="UNKNOWN",
            projected_quantum_risk="UNKNOWN",
            key_size_delta_bytes=0,
            ciphertext_or_sig_delta_bytes=0,
            bandwidth_latency_impact="Unknown algorithm",
            compatibility_risk="Unsupported candidate algorithm",
            remaining_uncertainties=[f"Candidate algorithm '{candidate_algorithm}' is not in the PQC Knowledge Base."],
        )

    # Calculate Key Size & Signature / Ciphertext Deltas
    # Estimate classical sizes: RSA-2048 public key ~256B, sig/ciphertext ~256B; ECDSA P-256 ~64B, sig ~64B
    if curr_algo == "RSA":
        classical_pk = (asset.key_length or 2048) // 8
        classical_sig = classical_pk
    elif curr_algo in ("ECDSA", "ECDH", "ECC", "EC"):
        classical_pk = 64
        classical_sig = 64
    else:
        classical_pk = 32
        classical_sig = 16

    pk_delta = pqc_info.public_key_size_bytes - classical_pk
    sig_delta = pqc_info.ciphertext_or_signature_size_bytes - classical_sig

    # Security Posture Projection
    if pqc_info.primitive in ("kem", "signature"):
        projected_posture = f"QUANTUM_SAFE ({pqc_info.nist_standard} Category {pqc_info.security_category})"
        projected_quantum_risk = "NONE"
    elif pqc_info.primitive == "symmetric" and pqc_info.security_category >= 5:
        projected_posture = "QUANTUM_RESISTANT_SYMMETRIC"
        projected_quantum_risk = "NONE"
    else:
        projected_posture = "STANDARD"
        projected_quantum_risk = "LOW"

    # Bandwidth & Latency Impact
    if sig_delta > 3000:
        impact = "High bandwidth overhead; TCP/UDP packet fragmentation risk."
        remaining_uncertainties.append("Signature size (3,300+ B) requires MTU and X.509 buffer validation.")
    elif sig_delta > 800:
        impact = "Moderate bandwidth overhead; requires memory buffer adjustment."
    else:
        impact = "Negligible bandwidth impact."

    # Compatibility Risk
    lang = asset.language.lower()
    if lang in ("c", "cpp"):
        compat = f"Requires OpenSSL 3.5+ or liboqs bindings in {lang.upper()}."
        remaining_uncertainties.append(f"C/C++ build toolchain must link liboqs for {pqc_info.name}.")
    else:
        compat = f"Requires PQC wrapper library for {lang.upper()}."

    if context.business_criticality.source == "unknown":
        remaining_uncertainties.append("Application business criticality is UNKNOWN; production impact unconfirmed.")

    return SimulationResult(
        asset_id=asset.asset_id,
        current_algorithm=asset.algorithm,
        candidate_algorithm=pqc_info.name,
        candidate_pqc_info=pqc_info,
        projected_security_posture=projected_posture,
        projected_quantum_risk=projected_quantum_risk,
        key_size_delta_bytes=pk_delta,
        ciphertext_or_sig_delta_bytes=sig_delta,
        bandwidth_latency_impact=impact,
        compatibility_risk=compat,
        remaining_uncertainties=remaining_uncertainties,
    )
