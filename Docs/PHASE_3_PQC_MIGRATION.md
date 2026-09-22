# CryptoSentinel Phase 3 — PQC & Hybrid Migration Intelligence Methodology & Documentation

## Executive Overview

CryptoSentinel Phase 3 transforms the platform from identifying cryptographic risk into an **actionable Post-Quantum Cryptography (PQC) and Hybrid Migration Intelligence engine**.

Phase 1 established *what* cryptographic assets exist (`CryptoAsset`). Phase 2 established *context and quantum/HNDL risk* (`QuantumRiskAssessment`). Phase 3 answers:
- **What** NIST-standardized PQC or hybrid algorithm should replace each vulnerable primitive?
- **Why** is a specific PQC candidate recommended (considering cryptographic purpose, NIST standards FIPS 203/204/205, and performance)?
- **What constraints** (signature size explosion, key overhead, packet limits, library support) exist?
- **How ready** is the asset/application for migration across 5 explicit dimensions?
- **What if** a user simulates migrating to candidate X (projected security posture, key/signature delta, bandwidth impact)?
- **How to track** migration lifecycle states (`DISCOVERED` → `ASSESSED` → `PLANNED` → `READY` → `IN_PROGRESS` → `MIGRATED` → `VERIFIED`)?

---

## 1. PQC Knowledge Base (`src/ecdat/pqc_kb.py`)

CryptoSentinel Phase 3 incorporates an authoritative knowledge base of NIST-standardized PQC algorithms published under FIPS 203, FIPS 204, and FIPS 205 (August 2024).

### Supported Standards & Parameters
1. **Module-Lattice Key Encapsulation (ML-KEM, FIPS 203)**:
   - `ML-KEM-512`: Security Category 1 (AES-128 equivalent), Public Key: 800 B, Ciphertext: 768 B.
   - `ML-KEM-768`: Security Category 3 (AES-192 equivalent), Public Key: 1,184 B, Ciphertext: 1,088 B (Default KEM recommendation).
   - `ML-KEM-1024`: Security Category 5 (AES-256 equivalent), Public Key: 1,568 B, Ciphertext: 1,568 B.
2. **Module-Lattice Digital Signatures (ML-DSA, FIPS 204)**:
   - `ML-DSA-44`: Security Category 1, Public Key: 1,312 B, Signature: 2,420 B.
   - `ML-DSA-65`: Security Category 3, Public Key: 1,952 B, Signature: 3,309 B (Default signature recommendation).
   - `ML-DSA-87`: Security Category 5, Public Key: 2,592 B, Signature: 4,627 B.
3. **Stateless Hash-Based Digital Signatures (SLH-DSA, FIPS 205)**:
   - `SLH-DSA-SHAKE-128s`: Security Category 1, Public Key: 32 B, Signature: 7,856 B. Conservative hash-based fallback (Sphincs+).
4. **Quantum-Safe Symmetric Standard (FIPS 197)**:
   - `AES-256-GCM`: Retains 128 bits of security margin under Grover's search algorithm.

---

## 2. Classical-to-PQC Purpose-Aware Mapping (`src/ecdat/pqc_mapping.py`)

Migration recommendations are strictly **purpose-aware**:

| Classical Primitive | Category / Purpose | Recommended PQC Target | Strategy Type |
|---|---|---|---|
| RSA-2048/4096 | `digital_signature` | **ML-DSA-65** (FIPS 204) | DIRECT |
| RSA-2048/4096 | `asymmetric_encryption` / `key_exchange` | **ML-KEM-768** (FIPS 203) | DIRECT / HYBRID |
| ECDSA | `digital_signature` | **ML-DSA-65** (FIPS 204) | DIRECT (Hybrid option) |
| ECDH / DH | `key_exchange` | **ML-KEM-768** (FIPS 203) | HYBRID (ECDH + ML-KEM) |
| AES-128 / AES-192 | `symmetric_encryption` | **AES-256-GCM** (FIPS 197) | INDIRECT (Key size upgrade) |
| AES-256 | `symmetric_encryption` | None (Quantum safe) | NO_PQC_REPLACEMENT_NEEDED |
| SHA-256 / SHA-512 | `hashing` | None (Quantum resistant) | NO_PQC_REPLACEMENT_NEEDED |
| MD5 / SHA-1 | `hashing` | **SHA-256** (Classical) | INDIRECT |
| Custom / Unknown | Any | Manual Review | NO_DIRECT_EQUIVALENT |

---

## 3. Dual Classical + PQC Hybrid Migration Strategies

Hybrid migration enables dual classical and post-quantum mechanisms to operate concurrently during transition.

### Example Construction: ECDH + ML-KEM-768
- **Classical Component**: ECDH P-256 (64 B public key).
- **PQC Component**: ML-KEM-768 (1,184 B public key).
- **Shared Secret Derivation**: $$K = \text{HKDF-Extract}(\text{ECDH-Secret} \parallel \text{ML-KEM-Decapsulate}(\text{Ciphertext}))$$
- **Combined Key Overhead**: 1,248 Bytes.

---

## 4. Migration Constraints Engine (`src/ecdat/migration_constraints.py`)

Evaluates performance and deployment bottlenecks:
- **Key Size Overhead**: Flagged if public key exceeds 500 Bytes.
- **Signature Size Overhead**: Flagged if signature exceeds 1,000 Bytes (e.g. ML-DSA-65 signature is 3,309 B vs. ECDSA 64 B).
- **Packet Fragmentation Risk**: Flagged if combined key/sig > 1,400 Bytes MTU.
- **Library Availability Risk**: Flagged if C/C++ or language toolchain lacks OpenSSL 3.5+ or liboqs bindings.
- **Deployment Complexity**: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.

---

## 5. 5-Dimensional Migration Readiness (`src/ecdat/migration_readiness.py`)

Assesses readiness across 5 explicit dimensions:
1. **Discovery Completeness** (20%): Verified asset location & code snippet.
2. **Context Completeness** (25%): Operational sensitivity, lifetime, and environment parameters.
3. **Dependency & Library Support** (25%): Language PQC bindings.
4. **Protocol Compatibility** (15%): Packet fragmentation & buffer constraints.
5. **Testing Readiness** (15%): Staging / development environment availability.

Overall Score (0-100%):
- \(\ge 85\%\): `READY_FOR_MIGRATION`
- \(\ge 70\%\): `READY_FOR_PLANNING`
- \(\ge 50\%\): `PARTIALLY_READY`
- \(< 50\%\): `NOT_READY`

---

## 6. Migration Priority (`src/ecdat/migration_priority.py`)

Derived from Phase 2 Quantum Risk + HNDL + Mosca Urgency + Context Criticality:
- `CRITICAL`: Immediate migration priority (e.g., HNDL CRITICAL or Mosca CRITICAL + High Criticality).
- `HIGH`: High priority (Shor-vulnerable key exchange / signature).
- `MEDIUM`: Moderate priority (Grover symmetric key size upgrade).
- `LOW`: Low priority (Quantum safe or short data lifetime).
- `REVIEW_REQUIRED`: Incomplete context or unknown algorithm.

---

## 7. What-If Migration Simulator (`src/ecdat/migration_simulator.py`)

Allows security analysts to project the impact of candidate PQC algorithms without modifying production code.
Output includes: `projected_security_posture`, `key_size_delta_bytes`, `ciphertext_or_sig_delta_bytes`, `bandwidth_latency_impact`, `compatibility_risk`, and `remaining_uncertainties`. Outputs are strictly labeled `PROJECTED / SIMULATED`.

---

## 8. Migration Lifecycle State Machine (`src/ecdat/migration_lifecycle.py`)

State transitions strictly enforce step-by-step progress:
$$\text{DISCOVERED} \longrightarrow \text{ASSESSED} \longrightarrow \text{PLANNED} \longrightarrow \text{READY} \longrightarrow \text{IN\_PROGRESS} \longrightarrow \text{MIGRATED} \longrightarrow \text{VERIFIED}$$

*Illegal jumps (e.g. DISCOVERED \(\rightarrow\) VERIFIED) are rejected by state validation.*

---

## 9. API Specification

- `GET /api/v1/assets/{asset_id}/migration`
- `GET /api/v1/assets/{asset_id}/recommendations`
- `POST /api/v1/assets/{asset_id}/simulate-migration` (Body: `{"candidate_algorithm": "ML-DSA-65"}`)
- `GET /api/v1/migration/summary`
- `GET /api/v1/migration/roadmap`
- `PATCH /api/v1/assets/{asset_id}/migration-status` (Body: `{"new_state": "ASSESSED"}`)
