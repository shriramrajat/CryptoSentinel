from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Query
from .schemas import ScanRequest, ContextUpdateRequest, ErrorResponse
from .config import settings
from ecdat.service import ScanService, ScannerError, AnalysisError
from ecdat.context import AssetContext, ContextResolver
from ecdat.config_policy import RiskPolicyConfig

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

    try:
        result = service.run_scan(
            target_path=request.target_path,
            language_filters=request.language_filters,
            generate_cbom=request.generate_cbom or False,
            user_context_map=merged_context_map if merged_context_map else None,
            policy_config=request.policy_config,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except (ScannerError, AnalysisError) as exc:
        raise HTTPException(status_code=500, detail=str(exc))

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
