# SIH26164 Traceability Matrix

This matrix maps each requirement of problem statement **SIH26164** ("Enterprise Cryptographic Asset Discovery & Analysis Tool") directly to its architectural phase, backend module, API endpoint, automated test suite, and operational boundaries.

---

| Requirement ID | Requirement Title & Scope | Status | Phase | Backend Module | Primary API Endpoint | Test File | Operational Boundaries & Limitations |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **REQ-01** | Cryptographic Discovery | `IMPLEMENTED` | Phase 1 | `src/ecdat/discovery/` | `POST /api/v1/scan` | `tests/test_phase1_cbom.py` | Static code analysis & file parsing. |
| **REQ-02** | Standardized CBOM Generation | `IMPLEMENTED` | Phase 1 | `src/ecdat/cbom/generator.py` | `GET /api/v1/cbom` | `tests/test_phase6_cbom.py` | CycloneDX 1.5 JSON formatted CBOM output. |
| **REQ-03** | Context-Aware Quantum Risk | `IMPLEMENTED` | Phase 2 | `src/ecdat/quantum_risk.py` | `POST /api/v1/quantum-risk` | `tests/test_phase2_quantum_risk.py` | HNDL + Mosca lifecycle risk scoring. |
| **REQ-04** | PQC Migration Intelligence | `IMPLEMENTED` | Phase 3 | `src/ecdat/pqc_recommendation.py` | `GET /api/v1/migration/recommendations` | `tests/test_phase3_pqc_migration.py` | NIST standard algorithms & algorithm mappings. |
| **REQ-05** | Enterprise Cryptographic Inventory | `IMPLEMENTED` | Phase 4 | `src/ecdat/inventory/` | `GET /api/v1/inventory/summary` | `tests/test_phase4_inventory.py` | SQLite persistent inventory store. |
| **REQ-06** | Historical Observation Tracking | `IMPLEMENTED` | Phase 4 | `src/ecdat/inventory/observations.py` | `GET /api/v1/inventory/observations` | `tests/test_phase4_observations.py` | Tracks inventory transitions & diffs. |
| **REQ-07** | Binary & Container Discovery | `IMPLEMENTED` | Phase 5 | `src/ecdat/discovery/` | `POST /api/v1/discovery/{source}` | `tests/test_phase5_discovery.py` | Symbol string matching without native execution. |
| **REQ-08** | Dependency & Protocol Discovery | `IMPLEMENTED` | Phase 5 | `src/ecdat/discovery/` | `POST /api/v1/discovery/dependency` | `tests/test_phase5_inventory_integration.py` | Package manifest & config analysis. |
| **REQ-09** | Graph & Enterprise Search | `IMPLEMENTED` | Phase 5 | `src/ecdat/graph.py` | `POST /api/v1/graph/query` | `tests/test_phase5_search.py` | In-memory graph builder & bounded search. |
| **REQ-10** | Hardware Crypto Discovery | `IMPLEMENTED` | Phase 6 | `src/ecdat/discovery/hardware.py` | `POST /api/v1/discovery/hardware` | `tests/test_phase6_hardware_discovery.py` | Config/header/library static detection (no PKCS#11 lib loading). |
| **REQ-11** | Cloud Crypto Intelligence | `IMPLEMENTED` | Phase 6 | `src/ecdat/discovery/cloud.py` | `POST /api/v1/discovery/cloud` | `tests/test_phase6_cloud_discovery.py` | IaC & code static references (zero cloud API/network calls). |
| **REQ-12** | Evidence Hardening Engine | `IMPLEMENTED` | Phase 6 | `src/ecdat/evidence.py` | `GET /api/v1/compliance` | `tests/test_phase6_evidence_model.py` | Canonical provenance model: OBSERVED, INFERRED, CONFIGURED, REFERENCE_ONLY, LIVE_VERIFIED. |

---

## Provenance Model Mapping

In accordance with Phase 6 evidence hardening rules:
1. **OBSERVED**: Direct evidence extracted from source code ASTs, binary string tables, or certificate subjects.
2. **INFERRED**: Derived findings resulting from cryptographic heuristic rules or dependency graph analysis.
3. **CONFIGURED**: Static detection of hardware (PKCS#11 config files, TPM device nodes, `/etc/ksmtuned`) or cloud IaC resources (`azurerm_key_vault`, `aws_kms_key`).
4. **REFERENCE_ONLY**: Static references to cloud SDK imports, hardware library headers (`pkcs11.h`), or driver references.
5. **LIVE_VERIFIED**: Reserved for runtime socket inspections or authenticated API queries (intentionally disabled for safe static discovery).
