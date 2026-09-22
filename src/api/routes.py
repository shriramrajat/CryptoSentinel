from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Query
from .schemas import ScanRequest, ContextUpdateRequest, SimulationRequest, LifecycleUpdateRequest, ErrorResponse
from .config import settings
from ecdat.service import ScanService, ScannerError, AnalysisError, _LIFECYCLE_RECORD_STORE
from ecdat.context import AssetContext, ContextResolver
from ecdat.config_policy import RiskPolicyConfig
from ecdat.models import CryptoAsset
from ecdat.migration_lifecycle import LifecycleState, generate_migration_roadmap
from ecdat.migration_simulator import simulate_migration

router = APIRouter()

# Global memory cache for the latest scan result to serve asset-level GET endpoints
_LATEST_SCAN_CACHE: Dict[str, Any] = {}
_USER_CONTEXT_STORE: Dict[str, Dict[str, Any]] = {}


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/version")
def version() -> dict:
    return {"version": settings.version}


@router.post(
    "/api/v1/scan",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid Input"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def scan_endpoint(request: ScanRequest) -> dict:
    """
    Scan a target path for cryptographic assets.

    - `target_path`: Absolute or relative path to scan.
    - `language_filters`: Optional list of language names to restrict scanning (e.g. ["python", "java"]).
    - `generate_cbom`: If true, include a CycloneDX v1.6 CBOM in the response under the `cbom` key.
    """
    service = ScanService()
    
    # Merge existing user context store with incoming request context
    merged_context_map = dict(_USER_CONTEXT_STORE)
    if request.user_context_map:
        merged_context_map.update(request.user_context_map)

    result = service.run_scan(
        target_path=request.target_path,
        language_filters=request.language_filters,
        generate_cbom=request.generate_cbom or False,
        user_context_map=merged_context_map if merged_context_map else None,
        policy_config=request.policy_config,
    )

    # Store findings in memory cache indexed by finding_id
    _LATEST_SCAN_CACHE.clear()
    _LATEST_SCAN_CACHE["summary"] = result.get("summary", {})
    _LATEST_SCAN_CACHE["metadata"] = result.get("metadata", {})
    _LATEST_SCAN_CACHE["findings"] = {
        f["finding_id"]: f for f in result.get("findings", [])
    }

    return result


@router.post(
    "/api/v1/cbom",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid Input"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def cbom_endpoint(request: ScanRequest) -> dict:
    """
    Scan a target path and return ONLY the CycloneDX v1.6 CBOM JSON.
    The full findings payload is not returned — use /api/v1/scan for full results.
    """
    service = ScanService()
    try:
        result = service.run_scan(
            request.target_path,
            request.language_filters,
            generate_cbom=True,
        )
        cbom = result.get("cbom")
        if cbom is None:
            cbom_error = result.get("cbom_error", "CBOM generation failed with no error details.")
            raise HTTPException(status_code=500, detail=f"CBOM generation error: {cbom_error}")
        return cbom
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except (ScannerError, AnalysisError) as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/api/v1/context")
def update_context_endpoint(request: ContextUpdateRequest) -> dict:
    """Store or override context attributes for a specific asset_id or default repo."""
    _USER_CONTEXT_STORE[request.asset_id] = request.context
    ctx = AssetContext.from_dict(request.context)
    ctx_dict = ctx.to_dict()

    # Update cache if asset is in latest scan
    findings_cache = _LATEST_SCAN_CACHE.get("findings", {})
    if request.asset_id in findings_cache:
        findings_cache[request.asset_id]["context"] = ctx_dict

    return {
        "status": "success",
        "asset_id": request.asset_id,
        "context": ctx_dict,
    }


@router.get("/api/v1/assets/{asset_id}/context")
def get_asset_context_endpoint(asset_id: str) -> dict:
    """Get context for a specific asset_id from the latest scan or stored context."""
    finding = _LATEST_SCAN_CACHE.get("findings", {}).get(asset_id)
    if finding and "context" in finding:
        return {"asset_id": asset_id, "context": finding["context"]}

    user_ctx = _USER_CONTEXT_STORE.get(asset_id)
    if user_ctx:
        return {"asset_id": asset_id, "context": AssetContext.from_dict(user_ctx).to_dict()}

    return {"asset_id": asset_id, "context": AssetContext().to_dict()}


@router.get("/api/v1/assets/{asset_id}/risk")
def get_asset_risk_endpoint(asset_id: str) -> dict:
    """Get Phase 2 Quantum Risk Assessment for a specific asset_id."""
    finding = _LATEST_SCAN_CACHE.get("findings", {}).get(asset_id)
    if not finding:
        raise HTTPException(status_code=404, detail=f"Asset '{asset_id}' not found in latest scan.")

    return {
        "asset_id": asset_id,
        "algorithm": finding.get("algorithm"),
        "file_location": finding.get("file_location"),
        "risk": finding.get("risk"),
        "quantum_risk_intelligence": finding.get("quantum_risk_intelligence"),
    }


@router.get("/api/v1/risk/summary")
def get_risk_summary_endpoint() -> dict:
    """Get aggregated risk summary metrics from the latest scan."""
    summary = _LATEST_SCAN_CACHE.get("summary")
    if not summary:
        return {
            "status": "no_scan_performed",
            "message": "No scan results currently cached. Run a scan first via POST /api/v1/scan.",
        }
    return {"summary": summary}


@router.get("/api/v1/risk/quantum")
def get_quantum_risk_summary_endpoint() -> dict:
    """Get quantum threat breakdown from the latest scan."""
    findings = list(_LATEST_SCAN_CACHE.get("findings", {}).values())
    shor_findings = [f for f in findings if f.get("risk", {}).get("quantum_threat") == "shor"]
    grover_findings = [f for f in findings if f.get("risk", {}).get("quantum_threat") == "grover"]

    return {
        "total_assets": len(findings),
        "total_quantum_vulnerable": len(shor_findings) + len(grover_findings),
        "shor_vulnerable_count": len(shor_findings),
        "grover_vulnerable_count": len(grover_findings),
        "shor_assets": [
            {
                "finding_id": f["finding_id"],
                "algorithm": f["algorithm"],
                "file_location": f["file_location"],
                "pqc_recommendation": f["risk"].get("pqc_recommendation"),
            }
            for f in shor_findings
        ],
        "grover_assets": [
            {
                "finding_id": f["finding_id"],
                "algorithm": f["algorithm"],
                "key_length": f.get("key_length"),
                "file_location": f["file_location"],
            }
            for f in grover_findings
        ],
    }


@router.get("/api/v1/risk/hndl")
def get_hndl_risk_summary_endpoint() -> dict:
    """Get Harvest-Now-Decrypt-Later exposure breakdown from the latest scan."""
    findings = list(_LATEST_SCAN_CACHE.get("findings", {}).values())
    hndl_candidates = []

    for f in findings:
        qri = f.get("quantum_risk_intelligence", {})
        hndl_assess = qri.get("hndl_assessment", {})
        status = hndl_assess.get("status")
        if status in ("CRITICAL", "HIGH", "MEDIUM", "UNKNOWN"):
            hndl_candidates.append({
                "finding_id": f["finding_id"],
                "algorithm": f["algorithm"],
                "file_location": f["file_location"],
                "hndl_status": status,
                "exposure_summary": hndl_assess.get("exposure_summary"),
                "reasons": hndl_assess.get("reasons", []),
            })

    return {
        "total_assets": len(findings),
        "hndl_candidates_count": len(hndl_candidates),
        "hndl_candidates": hndl_candidates,
    }


# ==============================================================================
# PHASE 3 ENDPOINTS
# ==============================================================================

@router.get("/api/v1/assets/{asset_id}/migration")
def get_asset_migration_endpoint(asset_id: str) -> dict:
    """Get Phase 3 PQC Migration Intelligence for a specific asset_id."""
    finding = _LATEST_SCAN_CACHE.get("findings", {}).get(asset_id)
    if not finding or "migration_intelligence" not in finding:
        raise HTTPException(status_code=404, detail=f"Asset '{asset_id}' not found in latest scan.")

    return {
        "asset_id": asset_id,
        "algorithm": finding.get("algorithm"),
        "category": finding.get("category"),
        "file_location": finding.get("file_location"),
        "migration_intelligence": finding.get("migration_intelligence"),
    }


@router.get("/api/v1/assets/{asset_id}/recommendations")
def get_asset_recommendations_endpoint(asset_id: str) -> dict:
    """Get PQC recommendation and alternative candidates for a specific asset_id."""
    finding = _LATEST_SCAN_CACHE.get("findings", {}).get(asset_id)
    if not finding or "migration_intelligence" not in finding:
        raise HTTPException(status_code=404, detail=f"Asset '{asset_id}' not found in latest scan.")

    mig_intel = finding.get("migration_intelligence", {})
    return {
        "asset_id": asset_id,
        "algorithm": finding.get("algorithm"),
        "recommendation": mig_intel.get("recommendation"),
        "migration_priority": mig_intel.get("migration_priority"),
    }


@router.post("/api/v1/assets/{asset_id}/simulate-migration")
def simulate_migration_endpoint(asset_id: str, request: SimulationRequest) -> dict:
    """Simulates the projected impact of migrating an asset to candidate_algorithm."""
    finding = _LATEST_SCAN_CACHE.get("findings", {}).get(asset_id)
    if not finding:
        # Construct dummy asset for simulation if asset_id is not in latest scan cache
        fake_asset = CryptoAsset.create(
            name=f"Asset {asset_id}",
            category="asymmetric_encryption",
            algorithm="RSA",
            file_path="src/sim.py",
            line_number=1,
            code_snippet="key = RSA.generate(2048)",
            library="cryptography",
            confidence=0.9,
            key_length=2048,
            asset_id=asset_id,
        )
        ctx = AssetContext()
        sim_res = simulate_migration(fake_asset, request.candidate_algorithm, context=ctx)
        return {"asset_id": asset_id, "simulation": sim_res.to_dict()}

    # Construct CryptoAsset from finding
    evidence_dict = finding.get("evidence", {})
    asset = CryptoAsset.create(
        name=f"Asset {asset_id}",
        category=finding.get("category", "asymmetric_encryption"),
        algorithm=finding.get("algorithm", "RSA"),
        file_path=finding.get("file_location", {}).get("file_path", "unknown.py"),
        line_number=finding.get("file_location", {}).get("line_number", 1),
        code_snippet=evidence_dict.get("code_snippet", ""),
        library="cryptography",
        confidence=finding.get("risk", {}).get("confidence", 0.9),
        key_length=finding.get("key_length"),
        asset_id=asset_id,
    )
    ctx = AssetContext.from_dict(finding.get("context"))

    sim_res = simulate_migration(asset, request.candidate_algorithm, context=ctx)
    return {"asset_id": asset_id, "simulation": sim_res.to_dict()}


@router.get("/api/v1/migration/summary")
def get_migration_summary_endpoint() -> dict:
    """Get Phase 3 aggregated migration summary metrics."""
    summary = _LATEST_SCAN_CACHE.get("summary")
    if not summary:
        return {
            "status": "no_scan_performed",
            "message": "No scan results currently cached. Run a scan first via POST /api/v1/scan.",
        }
    return {
        "summary": {
            "total_crypto_assets": summary.get("total_crypto_assets", 0),
            "migration_priority_counts": summary.get("migration_priority_counts", {}),
            "migration_type_counts": summary.get("migration_type_counts", {}),
            "readiness_state_counts": summary.get("readiness_state_counts", {}),
        }
    }


@router.get("/api/v1/migration/roadmap")
def get_migration_roadmap_endpoint() -> dict:
    """Get overall migration roadmaps for all findings from the latest scan."""
    findings = list(_LATEST_SCAN_CACHE.get("findings", {}).values())
    roadmaps = []

    for f in findings:
        mig_intel = f.get("migration_intelligence", {})
        roadmaps.append({
            "asset_id": f["finding_id"],
            "algorithm": f["algorithm"],
            "category": f["category"],
            "file_location": f["file_location"],
            "migration_priority": mig_intel.get("migration_priority"),
            "current_state": mig_intel.get("lifecycle_record", {}).get("current_state"),
            "recommended_algorithm": mig_intel.get("recommendation", {}).get("recommended_algorithm"),
            "roadmap_steps": mig_intel.get("roadmap", []),
        })

    return {
        "total_assets": len(findings),
        "roadmaps": roadmaps,
    }


@router.patch("/api/v1/assets/{asset_id}/migration-status")
def update_migration_status_endpoint(asset_id: str, request: LifecycleUpdateRequest) -> dict:
    """Updates the migration lifecycle state for a specific asset_id."""
    try:
        target_state = LifecycleState(request.new_state.upper())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid lifecycle state '{request.new_state}'. Allowed states: {[s.value for s in LifecycleState]}")

    record = _LIFECYCLE_RECORD_STORE.get(asset_id)
    if not record:
        record = MigrationRecord(asset_id=asset_id, current_state=LifecycleState.DISCOVERED)
        _LIFECYCLE_RECORD_STORE[asset_id] = record

    try:
        record.transition_to(target_state, actor="user_api", notes=request.notes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # Update cache if finding is in latest scan
    finding = _LATEST_SCAN_CACHE.get("findings", {}).get(asset_id)
    if finding and "migration_intelligence" in finding:
        finding["migration_intelligence"]["lifecycle_record"] = record.to_dict()

    return {
        "status": "success",
        "asset_id": asset_id,
        "lifecycle_record": record.to_dict(),
    }
