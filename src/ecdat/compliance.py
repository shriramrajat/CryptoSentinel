"""SIH26164 requirement traceability engine (Phase 6, Track I + J).

Provides a structured mapping of every official SIH26164 requirement
to its current implementation status, module, API, test, and evidence.
Status values: IMPLEMENTED | PARTIALLY_IMPLEMENTED | NOT_IMPLEMENTED
"""
from __future__ import annotations
from typing import Any, Dict, List

REQUIREMENTS: List[Dict[str, Any]] = [
    {
        "id": "SIH-01",
        "requirement": (
            "Identify and catalogue cryptographic artefacts: algorithms, keys, "
            "certificates, protocols, libraries, hardware crypto modules, cloud services"
        ),
        "status": "PARTIALLY_IMPLEMENTED",
        "implementation": (
            "Phase 1 discovers algorithms/keys/certs/protocols via AST + regex. "
            "Phase 5 adds binary/container/dependency/protocol sources. "
            "Phase 6 adds hardware (PKCS11/TPM/SmartCard) and cloud (AWS/Azure/GCP) references. "
            "Hardware *active use* and cloud *live inventory* are NOT implemented (REFERENCE_ONLY/CONFIGURED)."
        ),
        "modules": ["ecdat.scanner", "ecdat.discovery.binary", "ecdat.discovery.container",
                    "ecdat.discovery.dependency", "ecdat.discovery.protocol",
                    "ecdat.discovery.hardware", "ecdat.discovery.cloud"],
        "apis": ["/api/v1/scan", "/api/v1/discovery/{source_type}",
                 "/api/v1/hardware-crypto", "/api/v1/cloud-crypto"],
        "frontend": ["FindingsPage", "AdvancedDiscoveryPage", "CompliancePage"],
        "tests": ["test_scanner.py", "test_phase5_binary.py", "test_phase5_container.py",
                  "test_phase6_hardware_discovery.py", "test_phase6_cloud_discovery.py"],
        "limitations": [
            "Hardware active-use detection requires runtime instrumentation (not implemented).",
            "Cloud live inventory requires authenticated API calls (not implemented by design).",
            "Binary analysis is string/symbol based; does not disassemble.",
        ],
    },
    {
        "id": "SIH-02",
        "requirement": "Perform comprehensive quantum risk assessment.",
        "status": "IMPLEMENTED",
        "implementation": (
            "Phase 2 implements deterministic quantum risk assessment: Shor/Grover threat "
            "classification, HNDL score, Mosca urgency, overall priority. All fields "
            "evidence-backed; AI cannot override."
        ),
        "modules": ["ecdat.quantum", "ecdat.hndl", "ecdat.risk"],
        "apis": ["/api/v1/assets/{id}/risk", "/api/v1/risk/summary", "/api/v1/risk/quantum"],
        "frontend": ["QuantumPage"],
        "tests": ["test_phase2_context_risk.py", "test_risk_classification.py"],
        "limitations": [],
    },
    {
        "id": "SIH-03",
        "requirement": "Identify systems potentially vulnerable to quantum attacks.",
        "status": "IMPLEMENTED",
        "implementation": (
            "Shor/Grover threat tagging on every asset. HNDL assessment identifies "
            "assets exposed to Harvest-Now-Decrypt-Later. Summary counts exposed."
        ),
        "modules": ["ecdat.quantum", "ecdat.hndl"],
        "apis": ["/api/v1/risk/quantum", "/api/v1/risk/hndl"],
        "frontend": ["QuantumPage"],
        "tests": ["test_phase2_context_risk.py"],
        "limitations": [],
    },
    {
        "id": "SIH-04",
        "requirement": "Highlight risks to sensitive data.",
        "status": "IMPLEMENTED",
        "implementation": (
            "Phase 2 context model captures data sensitivity (PII, financial, health, "
            "classified). Risk assessment weights context. HNDL identifies sensitive data "
            "exposure. Mosca lifecycle captures data lifetime."
        ),
        "modules": ["ecdat.context", "ecdat.hndl", "ecdat.lifecycle"],
        "apis": ["/api/v1/assets/{id}/risk", "/api/v1/risk/hndl"],
        "frontend": ["QuantumPage", "FindingsPage"],
        "tests": ["test_phase2_context_risk.py"],
        "limitations": ["User must provide business context; it is not auto-detected from code."],
    },
    {
        "id": "SIH-05",
        "requirement": "Classify artefacts by type, lifetime, and business criticality.",
        "status": "IMPLEMENTED",
        "implementation": (
            "Category/type on every CryptoAsset. Data lifetime and migration time in "
            "Phase 2 context. Business criticality in Phase 4 project/repo model."
        ),
        "modules": ["ecdat.models", "ecdat.context", "ecdat.lifecycle"],
        "apis": ["/api/v1/scan", "/api/v1/inventory"],
        "frontend": ["FindingsPage", "QuantumPage"],
        "tests": ["test_phase2_context_risk.py", "test_phase4_enterprise_inventory.py"],
        "limitations": ["Data lifetime must be user-provided; cannot be auto-inferred reliably."],
    },
    {
        "id": "SIH-06",
        "requirement": (
            "Apply Mosca's algorithm: data lifetime, migration time, "
            "expected arrival of CRQC."
        ),
        "status": "IMPLEMENTED",
        "implementation": (
            "Phase 2 implements full Mosca's algorithm. Inputs: data_lifetime_years, "
            "migration_lead_time_years, quantum_horizon_years (policy). "
            "Output: urgency + time-to-act."
        ),
        "modules": ["ecdat.lifecycle", "ecdat.risk"],
        "apis": ["/api/v1/assets/{id}/risk"],
        "frontend": ["QuantumPage"],
        "tests": ["test_phase2_context_risk.py"],
        "limitations": ["Quantum horizon is configurable estimate; not a prediction."],
    },
    {
        "id": "SIH-07",
        "requirement": "Recommend suitable PQC and hybrid alternatives.",
        "status": "IMPLEMENTED",
        "implementation": (
            "Phase 3 implements evidence-backed PQC recommendation engine: ML-KEM, "
            "ML-DSA, SLH-DSA, XMSS, hybrid AES-256 options. Per-algorithm NIST mapping."
        ),
        "modules": ["ecdat.pqc_recommendation", "ecdat.pqc_kb", "ecdat.pqc_mapping"],
        "apis": ["/api/v1/assets/{id}/recommendations", "/api/v1/migration/summary"],
        "frontend": ["MigrationPage"],
        "tests": ["test_phase3_pqc_migration.py"],
        "limitations": [],
    },
    {
        "id": "SIH-08",
        "requirement": "Recommendations consider risk, latency, cost.",
        "status": "PARTIALLY_IMPLEMENTED",
        "implementation": (
            "Risk: fully incorporated. Latency: qualitative category in recommendation. "
            "Cost: migration complexity captured. Numeric cost model not implemented."
        ),
        "modules": ["ecdat.pqc_recommendation", "ecdat.migration_constraints"],
        "apis": ["/api/v1/assets/{id}/recommendations"],
        "frontend": ["MigrationPage"],
        "tests": ["test_phase3_pqc_migration.py"],
        "limitations": ["Numeric latency benchmarks and cost models not implemented."],
    },
    {
        "id": "SIH-09",
        "requirement": "Produce a standardized CBOM.",
        "status": "IMPLEMENTED",
        "implementation": (
            "Phase 1 generates CycloneDX 1.6 CBOM JSON with cryptoProperties extension. "
            "Phase 6 extends to include hardware, cloud, binary, container assets."
        ),
        "modules": ["ecdat.cbom.generator"],
        "apis": ["/api/v1/cbom", "/api/v1/scan (generate_cbom=true)"],
        "frontend": ["ResultsPage"],
        "tests": ["test_cbom.py", "test_phase6_cbom.py"],
        "limitations": ["CycloneDX schema validation not performed at runtime (tested offline)."],
    },
    {
        "id": "SIH-10",
        "requirement": "Scan source code repos, binaries, libraries, container images.",
        "status": "IMPLEMENTED",
        "implementation": (
            "Source: Phase 1 AST + regex scanner. Binaries: Phase 5 BinaryScanner. "
            "Libraries: Phase 5 DependencyScanner. Containers: Phase 5 ContainerScanner "
            "(tar/zip/dir; never executed)."
        ),
        "modules": ["ecdat.scanner", "ecdat.discovery.binary",
                    "ecdat.discovery.dependency", "ecdat.discovery.container"],
        "apis": ["/api/v1/scan", "/api/v1/discovery/{source_type}"],
        "frontend": ["Home", "AdvancedDiscoveryPage"],
        "tests": ["test_scanner.py", "test_phase5_binary.py",
                  "test_phase5_container.py", "test_phase5_dependencies.py"],
        "limitations": [
            "Binary analysis is string/symbol; no disassembly or decompilation.",
            "Container analysis is static manifest + path scan; no layer execution.",
        ],
    },
    {
        "id": "SIH-11",
        "requirement": "Produce reports with crypto assets including versions and modes.",
        "status": "IMPLEMENTED",
        "implementation": (
            "Every CryptoAsset includes algorithm, key_length, mode, padding, evidence "
            "snippet, file_path, line_number, library, confidence. Version captured "
            "where evidence supports it (SONAME, embedded string, manifest version)."
        ),
        "modules": ["ecdat.models", "ecdat.scanner", "ecdat.cbom.generator"],
        "apis": ["/api/v1/scan", "/api/v1/cbom"],
        "frontend": ["ResultsPage", "FindingsPage"],
        "tests": ["test_scanner.py", "test_cbom.py"],
        "limitations": [
            "Version not always determinable (binary string evidence only).",
            "Mode requires explicit API or config; often UNKNOWN for compiled code.",
        ],
    },
    {
        "id": "SIH-12",
        "requirement": "Interactive GUI to visualize scans, risks, and results.",
        "status": "IMPLEMENTED",
        "implementation": (
            "React frontend with pages: Dashboard/Scan, Analysis Results, Crypto Inventory, "
            "Quantum/PQC Readiness, PQC Migration Intelligence, Enterprise Inventory, "
            "Advanced Discovery, Diagnostics, SIH Compliance Dashboard."
        ),
        "modules": ["frontend"],
        "apis": ["All /api/v1/* endpoints"],
        "frontend": ["Home", "ResultsPage", "FindingsPage", "QuantumPage",
                     "MigrationPage", "InventoryPage", "AdvancedDiscoveryPage",
                     "DiagnosticsPage", "CompliancePage"],
        "tests": ["test_api.py"],
        "limitations": ["Frontend is a SPA; no server-side rendering."],
    },
]

# Status constants
IMPLEMENTED = "IMPLEMENTED"
PARTIALLY_IMPLEMENTED = "PARTIALLY_IMPLEMENTED"
NOT_IMPLEMENTED = "NOT_IMPLEMENTED"


def get_summary() -> Dict[str, Any]:
    """Return a deterministic summary of requirement coverage."""
    counts: Dict[str, int] = {}
    for req in REQUIREMENTS:
        counts[req["status"]] = counts.get(req["status"], 0) + 1
    total = len(REQUIREMENTS)
    return {
        "total": total,
        "implemented": counts.get(IMPLEMENTED, 0),
        "partially_implemented": counts.get(PARTIALLY_IMPLEMENTED, 0),
        "not_implemented": counts.get(NOT_IMPLEMENTED, 0),
        "note": (
            "Counts are derived deterministically from the requirement matrix. "
            "Do not interpret as a percentage compliance score."
        ),
    }


def get_requirements() -> List[Dict[str, Any]]:
    return list(REQUIREMENTS)
