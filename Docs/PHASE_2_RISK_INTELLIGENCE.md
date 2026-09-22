# CryptoSentinel Phase 2 — Context + Quantum Risk Intelligence Methodology & Documentation

## Executive Overview

CryptoSentinel Phase 2 transforms the platform from raw cryptographic asset discovery into **context-aware cryptographic risk intelligence**. 

Phase 1 establishes *what* cryptographic assets exist in source code. Phase 2 answers:
- **Why** each asset matters to the enterprise.
- **How exposed** it is to adversary harvesting (Harvest-Now-Decrypt-Later / HNDL).
- **How urgent** its quantum and lifecycle risk is using Mosca's formula (\(C + M > Y\)).
- **What actions** must be taken toward Post-Quantum Cryptography (PQC) migration planning.

---

## 1. Asset Context Model & Provenance Engine

Asset context characterizes the operational and business environment hosting a cryptographic asset. Context is modeled deterministically via `AssetContext` with explicit provenance tracking.

### Context Fields
- `application`: Name of the application hosting the asset.
- `environment`: `UNKNOWN`, `DEVELOPMENT`, `TEST`, `STAGING`, `PRODUCTION`.
- `data_sensitivity`: `UNKNOWN`, `PUBLIC`, `INTERNAL`, `CONFIDENTIAL`, `RESTRICTED`, `CRITICAL`.
- `data_lifetime_years` (\(C\)): Required protection / confidentiality horizon in years.
- `business_criticality`: `UNKNOWN`, `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.
- `internet_exposed`: Boolean flag indicating if the asset operates in an internet-facing service.
- `owner_team`: Responsible engineering / security owner.
- `compliance_relevance`: Relevant regulatory frameworks (e.g. `PCI-DSS`, `HIPAA`, `GDPR`, `FIPS-140-3`).

### Context Provenance (`ContextSource`)
To prevent silent assumption fabrication, every context field records its provenance:
1. `OBSERVED`: Inferred directly from source code AST or evidence snippets.
2. `DERIVED`: Extracted from repository configuration files (`.cryptosentinel.yml` or `.cryptosentinel.json`).
3. `USER`: Explicitly provided by a security analyst via REST API or configuration override.
4. `UNKNOWN`: Unassigned / missing context parameter.

Precedence order during context resolution: `USER` > `DERIVED` > `OBSERVED` > `UNKNOWN`.

---

## 2. Deterministic Quantum Threat Classification

Quantum threat classification evaluates the exact mathematical hazard presented by a Cryptographically Relevant Quantum Computer (CRQC). Shor's algorithm and Grover's algorithm are treated as distinct threat models.

### Shor's Algorithm Threat (`SHOR`)
- **Target Primitives**: RSA, ECC, ECDSA, ECDH, Diffie-Hellman (DH), DSA.
- **Mathematical Impact**: Solves prime factorization and discrete logarithms in polynomial time. Completely breaks asymmetric confidentiality, digital signatures, and key exchange.
- **Security Margin**: 0 bits.
- **Action**: Algorithm replacement with NIST Module-Lattice standards (FIPS 203 ML-KEM for key exchange, FIPS 204 ML-DSA for signatures).

### Grover's Algorithm Threat (`GROVER`)
- **Target Primitives**: AES symmetric encryption, symmetric key length < 256 bits.
- **Mathematical Impact**: Provides quadratic speedup for unstructured brute-force search. Reduces effective security margin by half (e.g. AES-128 offers 64 bits of post-quantum security).
- **Action**: Key size upgrade to 256 bits (AES-256-GCM under FIPS 197 provides 128 bits of quantum security margin).

---

## 3. Harvest-Now-Decrypt-Later (HNDL) Methodology

Harvest-Now-Decrypt-Later (HNDL) occurs when an adversary passively records encrypted network traffic or key exchanges today with the intent to decrypt it once a CRQC becomes operational.

### HNDL Deterministic Rules
HNDL risk strictly requires:
1. **Shor-vulnerable public-key primitive** used for **confidentiality** or **key exchange** (e.g. RSA encryption, ECDH, DH). *Note: Digital signatures are NOT subject to HNDL data decryption.*
2. **High data sensitivity** (`CONFIDENTIAL`, `RESTRICTED`, `CRITICAL`).
3. **Long data lifetime** (\(C \ge 5.0\) years).
4. **Internet exposure**.

### HNDL Status Classifications
- `CRITICAL`: Internet-exposed service encrypting/exchanging keys for highly sensitive, long-lived data using quantum-vulnerable primitives.
- `HIGH`: Encrypting/exchanging keys for highly sensitive, long-lived data using quantum-vulnerable primitives.
- `MEDIUM`: Moderate confidentiality horizon or sensitivity requirement.
- `LOW`: Short data lifetime or low sensitivity.
- `NOT_APPLICABLE`: Symmetric primitive or digital-signature-only usage.
- `UNKNOWN`: Missing `data_lifetime_years` or `data_sensitivity` context.

---

## 4. Mosca-Style Lifecycle Analysis (\(C + M > Y\))

Dr. Michele Mosca's framework evaluates whether a cryptographic asset will remain exposed to quantum decryption during its required protection lifetime.

### Mosca Equation
$$\text{Protection Horizon } P = C + M$$
$$\text{Safety Margin } \Delta = Y - P = Y - (C + M)$$

Where:
- \(C\) = Data Lifetime / Confidentiality Requirement (in years).
- \(M\) = Migration Lead Time (in years, default = 3.0 yrs).
- \(Y\) = Quantum Planning Horizon (in years, default = 10.0 yrs).

### Mosca Urgency Classifications
- `CRITICAL`: \(P - Y \ge 5.0\) years. Data protection horizon exceeds quantum horizon by 5+ years.
- `HIGH`: \(P > Y\). Protection horizon exceeds quantum planning horizon; migration planning must start immediately.
- `MODERATE`: \(0 \le Y - P \le 2.0\) years. Safety margin is narrow.
- `LOW`: \(Y - P > 2.0\) years. Sufficient safety margin exists.
- `UNKNOWN`: Data lifetime \(C\) is unknown.

---

## 5. Configurable Risk Policy (`RiskPolicyConfig`)

Risk assumptions and planning horizons are fully configurable and documented:
```json
{
  "quantum_horizon_years": 10.0,
  "default_migration_lead_time_years": 3.0,
  "hndl_sensitivity_threshold": "HIGH",
  "hndl_min_lifetime_years": 5.0
}
```

---

## 6. Technical Risk vs. Business Urgency & Unknown Handling

CryptoSentinel Phase 2 decouples technical vulnerability from business urgency:
- **Technical Quantum Risk**: Determined strictly from primitive algorithms and key sizes (e.g. RSA-2048 is `CRITICAL` technical risk).
- **Business Urgency**: Derived from context, HNDL exposure, and Mosca lifecycle urgency.
- **Uncertainty Handling**: When context parameters are unknown, business urgency is classified as `UNKNOWN`, overall priority is set to `"NEEDS_CONTEXT"`, and missing context fields are explicitly itemized in `missing_information`.

---

## 7. API Specification

### Endpoints
- `POST /api/v1/scan`: Ingests `target_path`, `language_filters`, `user_context_map`, and `policy_config`. Returns enriched scan payload.
- `POST /api/v1/context`: Ingests context updates for asset IDs or repository defaults.
- `GET /api/v1/assets/{asset_id}/context`: Returns resolved `AssetContext`.
- `GET /api/v1/assets/{asset_id}/risk`: Returns full Phase 2 `QuantumRiskAssessment`.
- `GET /api/v1/risk/summary`: Aggregated risk summary metrics.
- `GET /api/v1/risk/quantum`: Detailed quantum threat breakdown.
- `GET /api/v1/risk/hndl`: Detailed HNDL exposure breakdown.

---

## 8. Verification & Test Suite

The Phase 2 engine is validated against 73 automated backend tests in `tests/test_phase2_context_risk.py`, covering all 18 mandatory edge cases.
