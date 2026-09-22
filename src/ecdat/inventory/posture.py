"""Enterprise posture aggregation and trend engine for Phase 4."""
from typing import Any, Dict, List, Optional
from ecdat.inventory.store import InventoryStore


def calculate_posture(
    store: InventoryStore,
    repo_id: Optional[str] = None,
    project_id: Optional[str] = None,
    org_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Calculate aggregate enterprise posture metrics strictly from stored observations and snapshots."""
    assets = store.get_inventory_assets(repo_id=repo_id, project_id=project_id, org_id=org_id)
    alerts = store.list_alerts(repo_id=repo_id)

    repos = store.list_repositories(project_id=project_id)
    scans = store.list_scans(repo_id=repo_id)

    quantum_vulnerable = 0
    hndl_sensitive = 0
    critical_high_priority = 0
    ready_for_migration = 0
    partially_ready = 0
    not_ready = 0
    currently_migrating = 0
    migrated_assets = 0

    priority_counts = {"IMMEDIATE_ACTION": 0, "PLANNING_REQUIRED": 0, "NEEDS_CONTEXT": 0, "MONITOR": 0, "LOW_PRIORITY": 0}
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    hndl_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "NOT_APPLICABLE": 0, "UNKNOWN": 0}

    for a in assets:
        prio = a.get("overall_priority") or "MONITOR"
        sev = (a.get("technical_quantum_risk") or "info").lower()
        hndl = a.get("hndl_status") or "NOT_APPLICABLE"
        readiness = a.get("readiness_state") or "UNKNOWN"
        life = a.get("lifecycle_state") or "DISCOVERED"

        priority_counts[prio] = priority_counts.get(prio, 0) + 1
        severity_counts[sev] = severity_counts.get(sev, 0) + 1
        hndl_counts[hndl] = hndl_counts.get(hndl, 0) + 1

        if prio in ("IMMEDIATE_ACTION", "PLANNING_REQUIRED"):
            critical_high_priority += 1

        if hndl in ("CRITICAL", "HIGH", "MEDIUM"):
            hndl_sensitive += 1

        if sev in ("critical", "high"):
            quantum_vulnerable += 1

        if readiness == "READY_FOR_MIGRATION":
            ready_for_migration += 1
        elif readiness == "PARTIALLY_READY":
            partially_ready += 1
        elif readiness == "NOT_READY":
            not_ready += 1

        if life in ("IN_PROGRESS", "MIGRATING", "TESTING"):
            currently_migrating += 1
        elif life in ("COMPLETED", "MIGRATED"):
            migrated_assets += 1

    drifts = store.list_drift_events(repo_id=repo_id)

    open_alerts = [a for a in alerts if a.status.value in ("OPEN", "ACKNOWLEDGED")]
    high_critical_open_alerts = [a for a in open_alerts if a.severity.value in ("CRITICAL", "HIGH")]

    return {
        "scope": {
            "organization_id": org_id,
            "project_id": project_id,
            "repository_id": repo_id,
        },
        "totals": {
            "total_repositories": len(repos),
            "total_scans": len(scans),
            "total_crypto_assets": len(assets),
            "unique_crypto_assets": len(set(a["asset_id"] for a in assets)),
            "quantum_vulnerable_assets": quantum_vulnerable,
            "hndl_sensitive_assets": hndl_sensitive,
            "critical_high_priority_assets": critical_high_priority,
        },
        "migration_progress": {
            "ready_for_migration": ready_for_migration,
            "partially_ready": partially_ready,
            "not_ready": not_ready,
            "currently_migrating": currently_migrating,
            "migrated_assets": migrated_assets,
        },
        "distributions": {
            "priority_counts": priority_counts,
            "severity_counts": severity_counts,
            "hndl_counts": hndl_counts,
        },
        "monitoring": {
            "open_drift_events_count": len(drifts),
            "active_alerts_count": len(open_alerts),
            "unresolved_high_risk_alerts_count": len(high_critical_open_alerts),
        },
    }


def get_posture_trends(store: InventoryStore, repo_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get historical posture snapshot trends derived from completed scans over time."""
    scans = store.list_scans(repo_id=repo_id)
    trends = []

    # Sort scans in chronological order
    completed_scans = [s for s in scans if s.status.value == "COMPLETED" and s.completed_at]
    completed_scans.sort(key=lambda x: x.started_at)

    for scan in completed_scans:
        obs = store.get_scan_observations(scan.id)
        qv = sum(1 for o in obs if (o.get("technical_quantum_risk") or "").lower() in ("critical", "high"))
        hp = sum(1 for o in obs if o.get("overall_priority") in ("IMMEDIATE_ACTION", "PLANNING_REQUIRED"))
        migrated = sum(1 for o in obs if o.get("lifecycle_state") in ("COMPLETED", "MIGRATED"))

        trends.append({
            "scan_id": scan.id,
            "repository_id": scan.repository_id,
            "timestamp": scan.completed_at or scan.started_at,
            "total_crypto_assets": len(obs),
            "quantum_vulnerable_count": qv,
            "high_priority_count": hp,
            "migrated_count": migrated,
        })

    return trends
