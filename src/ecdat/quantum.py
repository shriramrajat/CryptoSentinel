"""
Quantum Threat Classification Module for CryptoSentinel Phase 2.

Implements deterministic quantum classification distinguishing Shor's algorithm
vulnerabilities (asymmetric factorizing/DLP) from Grover's algorithm impact
(symmetric quadratic search speedup).
"""

from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, Any, Optional


class QuantumThreatType(str, Enum):
    """Specific quantum computing threat type."""
    SHOR = "shor"
    GROVER = "grover"
    NONE = "none"


@dataclass(frozen=True)
class QuantumThreatAssessment:
    """Structured assessment of quantum computing threat against a cryptographic asset."""
    threat_type: QuantumThreatType
    threat_name: str
    description: str
    impact_summary: str
    security_margin_bits: Optional[int]
    quantum_resistant: bool

    def to_dict(self) -> Dict[str, Any]:
        res = asdict(self)
        res["threat_type"] = self.threat_type.value
        return res


SHOR_ALGORITHMS = {"RSA", "ECC", "EC", "ECDSA", "ECDH", "DSA", "DH", "DIFFIE-HELLMAN"}


def evaluate_quantum_threat(algorithm: str, key_length: Optional[int] = None) -> QuantumThreatAssessment:
    """Evaluates the quantum threat level for an algorithm and optional key length.
    
    Does NOT treat Shor and Grover as equivalent. Explains the exact mathematical hazard:
    - Shor: Polynomial time reduction for factoring and discrete log (breaks RSA/ECC/DSA/DH).
    - Grover: Quadratic search speedup (halves effective symmetric key bits).
    """
    algo_upper = algorithm.strip().upper()

    # 1. Shor's Algorithm Threat (Asymmetric Public-Key Cryptography)
    if algo_upper in SHOR_ALGORITHMS:
        return QuantumThreatAssessment(
            threat_type=QuantumThreatType.SHOR,
            threat_name="Shor's Algorithm Threat",
            description=(
                "Shor's algorithm efficiently solves prime factorization and discrete logarithm problems "
                "in polynomial time on a Cryptographically Relevant Quantum Computer (CRQC). "
                "This fundamentally compromises public-key cryptography including RSA, ECC, ECDSA, ECDH, and Diffie-Hellman."
            ),
            impact_summary="Complete loss of confidentiality, authentication, and non-repudiation guarantees.",
            security_margin_bits=0,
            quantum_resistant=False,
        )

    # 2. Grover's Algorithm Threat (Symmetric Encryption & Hashes)
    if algo_upper == "AES":
        if key_length is not None and key_length < 256:
            effective_bits = key_length // 2
            return QuantumThreatAssessment(
                threat_type=QuantumThreatType.GROVER,
                threat_name="Grover's Algorithm Threat",
                description=(
                    f"Grover's algorithm provides a quadratic speedup for unstructured brute-force search. "
                    f"For AES-{key_length}, it reduces effective security from {key_length} bits to {effective_bits} bits, "
                    "falling below the 128-bit quantum security floor."
                ),
                impact_summary=f"Reduced security margin ({effective_bits} bits effective security under Grover attack).",
                security_margin_bits=effective_bits,
                quantum_resistant=False,
            )
        elif key_length == 256:
            return QuantumThreatAssessment(
                threat_type=QuantumThreatType.NONE,
                threat_name="No Critical Quantum Threat",
                description=(
                    "AES-256 retains 128 bits of security under Grover's algorithm quadratic search speedup, "
                    "meeting NIST requirements for post-quantum symmetric security margin."
                ),
                impact_summary="Quantum-resistant under the modeled threat assumptions.",
                security_margin_bits=128,
                quantum_resistant=True,
            )
        else: # Unknown key length
            return QuantumThreatAssessment(
                threat_type=QuantumThreatType.GROVER,
                threat_name="Potential Grover's Threat",
                description=(
                    "AES was detected without explicit key length. If key length is below 256 bits, "
                    "Grover's algorithm reduces effective security margin below 128 bits."
                ),
                impact_summary="Unverified symmetric security margin under Grover's attack.",
                security_margin_bits=None,
                quantum_resistant=False,
            )

    # 3. Legacy symmetric or hashing primitives (Not Shor/Grover primary targets, but classically weak)
    if algo_upper in {"MD5", "SHA-1", "SHA1", "DES", "3DES", "TRIPLE-DES", "RC4"}:
        return QuantumThreatAssessment(
            threat_type=QuantumThreatType.NONE,
            threat_name="Legacy Classical Weakness",
            description=f"{algorithm} is cryptographically compromised under classical cryptanalysis.",
            impact_summary="Legacy classical weakness (primary risk is classical, not quantum).",
            security_margin_bits=0,
            quantum_resistant=False,
        )

    # 4. Modern quantum-resistant primitives
    if algo_upper in {"SHA-256", "SHA256", "SHA-512", "SHA512", "SHA-3", "SHA3"}:
        return QuantumThreatAssessment(
            threat_type=QuantumThreatType.NONE,
            threat_name="Quantum-Resistant Hash",
            description=f"{algorithm} provides sufficient collision and preimage resistance against quantum attacks.",
            impact_summary="Quantum-resistant under the modeled threat assumptions.",
            security_margin_bits=128,
            quantum_resistant=True,
        )

    # Default / Unknown Primitive
    return QuantumThreatAssessment(
        threat_type=QuantumThreatType.NONE,
        threat_name="Unknown Primitive Threat",
        description=f"Quantum vulnerability for {algorithm} cannot be definitively categorized.",
        impact_summary="Unknown quantum impact.",
        security_margin_bits=None,
        quantum_resistant=False,
    )
