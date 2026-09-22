from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from .schemas import (
    ScanRequest,
    ContextUpdateRequest,
    SimulationRequest,
    LifecycleUpdateRequest,
    OrganizationCreateRequest,
    ProjectCreateRequest,
    RepositoryCreateRequest,
    AlertPatchRequest,
    ScheduleCreateRequest,
    SchedulePatchRequest,
    ErrorResponse,
    AdvancedDiscoveryRequest,
    GitCompareRequest,
    CopilotQueryRequest,
    CopilotEvidenceRequest,
)
from .config import settings
from ecdat.service import ScanService, ScannerError, AnalysisError, _LIFECYCLE_RECORD_STORE
from ecdat.context import AssetContext, ContextResolver
from ecdat.config_policy import RiskPolicyConfig
from ecdat.models import CryptoAsset
from ecdat.migration_lifecycle import LifecycleState, MigrationRecord, generate_migration_roadmap
from ecdat.migration_simulator import simulate_migration
from ecdat.discovery import DiscoveryRegistry
from ecdat.phase5_graph import CryptoGraph
from ecdat.phase5_git import GitInspector
from ecdat.phase5_query import SecurityQueryEngine
from ecdat.phase5_copilot import EvidenceCopilot
from ecdat.phase5_inventory import AdvancedDiscoveryInventoryAdapter
from ecdat.phase6_stores import add_hardware, get_hardware, add_cloud, get_cloud

from ecdat.inventory.orchestrator import EnterpriseScanOrchestrator
from ecdat.inventory.store import InventoryStore
from ecdat.inventory.posture import calculate_posture, get_posture_trends
from ecdat.inventory.models import (
    Organization,
    Project,
    Repository,
    ScanSchedule,
    AlertStatus,
    AlertSeverity,
    AlertType,
)

router = APIRouter()
inventory_store = InventoryStore()

# Global memory cache for the latest scan result to serve asset-level GET endpoints
_LATEST_SCAN_CACHE: Dict[str, Any] = {}
_USER_CONTEXT_STORE: Dict[str, Dict[str, Any]] = {}
_DISCOVERY_REGISTRY = DiscoveryRegistry()
_QUERY_ENGINE = SecurityQueryEngine()
_COPILOT = EvidenceCopilot()


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


# ==============================================================================
# PHASE 6 ENDPOINTS: HARDWARE CRYPTO & CLOUD CRYPTO
# ==============================================================================

@router.post("/api/v1/discovery/hardware")
def hardware_discovery_endpoint(request: AdvancedDiscoveryRequest) -> dict:
    """Scan a file for hardware crypto module references (PKCS#11, TPM, smart-card, HW accel).
    All findings are CONFIGURED or REFERENCE_ONLY; never LIVE_VERIFIED."""
    try:
        result = _DISCOVERY_REGISTRY.scan("hardware", request.path)
        payload = result.to_dict()
        add_hardware([f.to_dict() for f in result.findings])
        return payload
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/api/v1/hardware-crypto")
def list_hardware_crypto() -> dict:
    """Return all hardware crypto references discovered in this session."""
    findings = get_hardware()
    return {"total": len(findings), "findings": findings}


@router.post("/api/v1/discovery/cloud")
def cloud_discovery_endpoint(request: AdvancedDiscoveryRequest) -> dict:
    """Scan a file for cloud crypto service references (AWS KMS/ACM, Azure Key Vault, GCP KMS).
    All findings are REFERENCE_ONLY or CONFIGURED. No cloud credentials are collected."""
    try:
        result = _DISCOVERY_REGISTRY.scan("cloud", request.path)
        payload = result.to_dict()
        add_cloud([f.to_dict() for f in result.findings])
        return payload
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/api/v1/cloud-crypto")
def list_cloud_crypto() -> dict:
    """Return all cloud crypto references discovered in this session."""
    findings = get_cloud()
    return {"total": len(findings), "findings": findings}


# ==============================================================================
# PHASE 5 DISCOVERY (pre-existing)
# ==============================================================================

@router.post("/api/v1/discovery/{source_type}")
def advanced_discovery_endpoint(source_type: str, request: AdvancedDiscoveryRequest) -> dict:
    """Run one bounded advanced discovery adapter; artifacts are never executed."""
    if source_type.lower() not in {"binary", "container", "dependency", "protocol"}:
        raise HTTPException(status_code=400, detail="Unsupported discovery source")
    try:
        result = _DISCOVERY_REGISTRY.scan(source_type, request.path)
        payload = result.to_dict()
        if request.repo_id:
            payload["inventory"] = AdvancedDiscoveryInventoryAdapter(inventory_store).ingest(
                result, request.repo_id, request.repo_name or "default-repo", request.org_id or "default-org", request.project_id or "default-project"
            )
        return payload
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/api/v1/graph")
def get_phase5_graph() -> dict:
    return CryptoGraph(inventory_store).to_dict()


@router.get("/api/v1/query")
def query_phase5_inventory(q: str, page: int = 1, page_size: int = 50, repo_id: Optional[str] = None) -> dict:
    assets = inventory_store.get_canonical_assets(repo_id=repo_id)
    return _QUERY_ENGINE.execute(q, assets, inventory_store.get_certificates(repo_id=repo_id), page=page, page_size=page_size, repo_id=repo_id)


@router.post("/api/v1/git/compare")
def compare_git_commits(request: GitCompareRequest) -> dict:
    try:
        return GitInspector().compare(request.repository, request.baseline, request.current)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/api/v1/copilot/query")
def copilot_query(request: CopilotQueryRequest) -> dict:
    return _COPILOT.query(request.prompt, inventory_store.get_canonical_assets(repo_id=None))


@router.post("/api/v1/copilot/explain")
def copilot_explain(finding: CopilotEvidenceRequest) -> dict:
    return _COPILOT.explain(finding.model_dump(exclude_none=True))


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
    Scan a target path for cryptographic assets and persist results in Enterprise Inventory.

    - `target_path`: Absolute or relative path to scan.
    - `language_filters`: Optional list of language names to restrict scanning (e.g. ["python", "java"]).
    - `generate_cbom`: If true, include a CycloneDX v1.6 CBOM in the response under the `cbom` key.
    """
    orchestrator = EnterpriseScanOrchestrator(store=inventory_store)
    
    # Merge existing user context store with incoming request context
    merged_context_map = dict(_USER_CONTEXT_STORE)
    if request.user_context_map:
        merged_context_map.update(request.user_context_map)

    result = orchestrator.run_enterprise_scan(
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


# ==============================================================================
# PHASE 4 ENDPOINTS: ENTERPRISE INVENTORY & CONTINUOUS MONITORING
# ==============================================================================

# 1. Organizations, Projects, Repositories
@router.post("/api/v1/organizations")
def create_organization_endpoint(request: OrganizationCreateRequest) -> dict:
    org = Organization(name=request.name)
    saved = inventory_store.create_organization(org)
    return {"organization": saved.to_dict()}


@router.get("/api/v1/organizations")
def list_organizations_endpoint() -> dict:
    orgs = inventory_store.list_organizations()
    return {"organizations": [o.to_dict() for o in orgs]}


@router.post("/api/v1/projects")
def create_project_endpoint(request: ProjectCreateRequest) -> dict:
    if not inventory_store.get_organization(request.organization_id):
        raise HTTPException(status_code=404, detail=f"Organization '{request.organization_id}' not found.")
    proj = Project(
        organization_id=request.organization_id,
        name=request.name,
        description=request.description or "",
        business_criticality=request.business_criticality or "high",
    )
    saved = inventory_store.create_project(proj)
    return {"project": saved.to_dict()}


@router.get("/api/v1/projects")
def list_projects_endpoint(organization_id: Optional[str] = Query(None)) -> dict:
    projs = inventory_store.list_projects(org_id=organization_id)
    return {"projects": [p.to_dict() for p in projs]}


@router.post("/api/v1/repositories")
def create_repository_endpoint(request: RepositoryCreateRequest) -> dict:
    if not inventory_store.get_project(request.project_id):
        raise HTTPException(status_code=404, detail=f"Project '{request.project_id}' not found.")
    repo = Repository(
        project_id=request.project_id,
        name=request.name,
        provider=request.provider or "git",
        url=request.url or "",
        default_branch=request.default_branch or "main",
        environment=request.environment or "production",
    )
    saved = inventory_store.create_repository(repo)
    return {"repository": saved.to_dict()}


@router.get("/api/v1/repositories")
def list_repositories_endpoint(project_id: Optional[str] = Query(None)) -> dict:
    repos = inventory_store.list_repositories(project_id=project_id)
    return {"repositories": [r.to_dict() for r in repos]}


# 2. Scans
@router.post("/api/v1/repositories/{repository_id}/scans")
def trigger_repository_scan_endpoint(repository_id: str, request: ScanRequest) -> dict:
    orchestrator = EnterpriseScanOrchestrator(store=inventory_store)
    merged_context_map = dict(_USER_CONTEXT_STORE)
    if request.user_context_map:
        merged_context_map.update(request.user_context_map)

    result = orchestrator.run_enterprise_scan(
        target_path=request.target_path,
        repository_id=repository_id,
        language_filters=request.language_filters,
        generate_cbom=request.generate_cbom or False,
        user_context_map=merged_context_map if merged_context_map else None,
        policy_config=request.policy_config,
    )
    return result


@router.get("/api/v1/scans/{scan_id}")
def get_scan_endpoint(scan_id: str) -> dict:
    scan = inventory_store.get_scan(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail=f"Scan '{scan_id}' not found.")
    obs = inventory_store.get_scan_observations(scan_id)
    return {
        "scan": scan.to_dict(),
        "observations_count": len(obs),
        "observations": obs,
    }


@router.get("/api/v1/repositories/{repository_id}/scans")
def list_repository_scans_endpoint(repository_id: str) -> dict:
    scans = inventory_store.list_scans(repo_id=repository_id)
    return {"repository_id": repository_id, "scans": [s.to_dict() for s in scans]}


# 3. Inventory & History
@router.get("/api/v1/inventory")
def get_inventory_endpoint(
    repository_id: Optional[str] = Query(None),
    project_id: Optional[str] = Query(None),
    organization_id: Optional[str] = Query(None),
) -> dict:
    assets = inventory_store.get_inventory_assets(repo_id=repository_id, project_id=project_id, org_id=organization_id)
    return {
        "total_assets": len(assets),
        "assets": assets,
    }


@router.get("/api/v1/inventory/assets/{asset_id}")
def get_inventory_asset_detail_endpoint(asset_id: str) -> dict:
    detail = inventory_store.get_asset_detail(asset_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Asset '{asset_id}' not found in inventory.")
    return detail


@router.get("/api/v1/inventory/history")
def get_inventory_history_endpoint(
    asset_id: Optional[str] = Query(None),
    repository_id: Optional[str] = Query(None),
) -> dict:
    obs = inventory_store.get_historical_observations(asset_id=asset_id, repo_id=repository_id) if hasattr(inventory_store, "get_historical_observations") else inventory_store.get_scan_observations(repository_id or "")
    return {
        "total_history_records": len(obs),
        "observations": obs,
    }


# 4. Drift
@router.get("/api/v1/drift")
def list_drift_events_endpoint(
    repository_id: Optional[str] = Query(None),
    asset_id: Optional[str] = Query(None),
) -> dict:
    events = inventory_store.list_drift_events(repo_id=repository_id, asset_id=asset_id)
    return {
        "total_drift_events": len(events),
        "drift_events": events,
    }


@router.get("/api/v1/drift/{drift_id}")
def get_drift_event_endpoint(drift_id: str) -> dict:
    events = inventory_store.list_drift_events()
    for e in events:
        if e["id"] == drift_id:
            return {"drift_event": e}
    raise HTTPException(status_code=404, detail=f"Drift event '{drift_id}' not found.")


# 5. Posture & Trends
@router.get("/api/v1/posture")
def get_global_posture_endpoint() -> dict:
    return calculate_posture(inventory_store)


@router.get("/api/v1/posture/organization/{organization_id}")
def get_org_posture_endpoint(organization_id: str) -> dict:
    return calculate_posture(inventory_store, org_id=organization_id)


@router.get("/api/v1/posture/project/{project_id}")
def get_project_posture_endpoint(project_id: str) -> dict:
    return calculate_posture(inventory_store, project_id=project_id)


@router.get("/api/v1/posture/repository/{repository_id}")
def get_repository_posture_endpoint(repository_id: str) -> dict:
    return calculate_posture(inventory_store, repo_id=repository_id)


@router.get("/api/v1/posture/trends")
def get_posture_trends_endpoint(repository_id: Optional[str] = Query(None)) -> dict:
    trends = get_posture_trends(inventory_store, repo_id=repository_id)
    return {"trends": trends}


# 6. Alerts
@router.get("/api/v1/alerts")
def list_alerts_endpoint(
    repository_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
) -> dict:
    alerts = inventory_store.list_alerts(repo_id=repository_id, status=status, severity=severity)
    return {
        "total_alerts": len(alerts),
        "alerts": [a.to_dict() for a in alerts],
    }


@router.patch("/api/v1/alerts/{alert_id}")
def update_alert_status_endpoint(alert_id: str, request: AlertPatchRequest) -> dict:
    try:
        new_status = AlertStatus(request.status.upper())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid alert status '{request.status}'. Allowed values: {[s.value for s in AlertStatus]}")

    try:
        updated = inventory_store.update_alert_status(alert_id, new_status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {
        "status": "success",
        "alert": updated.to_dict(),
    }


# 7. Schedules
@router.get("/api/v1/schedules")
def list_schedules_endpoint(repository_id: Optional[str] = Query(None)) -> dict:
    schedules = inventory_store.list_schedules(repo_id=repository_id)
    return {"schedules": [s.to_dict() for s in schedules]}


@router.post("/api/v1/schedules")
def create_schedule_endpoint(request: ScheduleCreateRequest) -> dict:
    if not inventory_store.get_repository(request.repository_id):
        raise HTTPException(status_code=404, detail=f"Repository '{request.repository_id}' not found.")
    sched = ScanSchedule(
        repository_id=request.repository_id,
        enabled=request.enabled if request.enabled is not None else True,
        interval_hours=request.interval_hours or 24,
    )
    saved = inventory_store.create_schedule(sched)
    return {"schedule": saved.to_dict()}


@router.patch("/api/v1/schedules/{schedule_id}")
def update_schedule_endpoint(schedule_id: str, request: SchedulePatchRequest) -> dict:
    try:
        updated = inventory_store.update_schedule(
            schedule_id,
            enabled=request.enabled,
            interval_hours=request.interval_hours,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    return {"schedule": updated.to_dict()}
