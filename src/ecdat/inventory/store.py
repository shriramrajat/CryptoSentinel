"""Storage and persistence layer for Phase 4 enterprise inventory."""
import json
import sqlite3
from typing import Any, Dict, List, Optional, Tuple

from ecdat.inventory.db import get_db_context, init_db
from ecdat.inventory.models import (
    Alert,
    AlertScopeType,
    AlertSeverity,
    AlertStatus,
    AlertType,
    CryptoAssetRecord,
    DriftEvent,
    DriftSeverity,
    DriftType,
    MigrationAssessmentSnapshot,
    ObservationRecord,
    ObservationStatus,
    Organization,
    Project,
    Repository,
    RiskAssessmentSnapshot,
    ScanRecord,
    ScanSchedule,
    ScanStatus,
    utc_now_iso,
)


class InventoryStore:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        init_db(self.db_path)

    def get_db_context(self):
        return get_db_context(self.db_path)

    def get_or_create_default_hierarchy(self) -> Tuple[str, str, str]:
        with get_db_context(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM repositories LIMIT 1;")
            row = cur.fetchone()
            if row:
                repo_id = row[0]
                cur.execute("SELECT project_id FROM repositories WHERE id = ?;", (repo_id,))
                proj_id = cur.fetchone()[0]
                cur.execute("SELECT organization_id FROM projects WHERE id = ?;", (proj_id,))
                org_id = cur.fetchone()[0]
                return org_id, proj_id, repo_id
            
            org = Organization(name="Default Enterprise")
            proj = Project(organization_id=org.id, name="Default Project")
            repo = Repository(project_id=proj.id, name="Default Repository")
            
            cur.execute(
                "INSERT INTO organizations (id, name, created_at, updated_at) VALUES (?, ?, ?, ?);",
                (org.id, org.name, org.created_at, org.updated_at),
            )
            cur.execute(
                "INSERT INTO projects (id, organization_id, name, description, business_criticality, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?);",
                (proj.id, proj.organization_id, proj.name, proj.description, proj.business_criticality, proj.created_at, proj.updated_at),
            )
            cur.execute(
                "INSERT INTO repositories (id, project_id, name, provider, url, default_branch, environment, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);",
                (repo.id, repo.project_id, repo.name, repo.provider, repo.url, repo.default_branch, repo.environment, repo.created_at, repo.updated_at),
            )
            return org.id, proj.id, repo.id

    # --------------------------------------------------------------------------
    # Organizations, Projects, Repositories
    # --------------------------------------------------------------------------
    def create_organization(self, org: Organization) -> Organization:
        with get_db_context(self.db_path) as conn:
            conn.execute(
                "INSERT INTO organizations (id, name, created_at, updated_at) VALUES (?, ?, ?, ?);",
                (org.id, org.name, org.created_at, org.updated_at),
            )
        return org

    def list_organizations(self) -> List[Organization]:
        with get_db_context(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM organizations ORDER BY created_at ASC;")
            return [
                Organization(id=r["id"], name=r["name"], created_at=r["created_at"], updated_at=r["updated_at"])
                for r in cur.fetchall()
            ]

    def get_organization(self, org_id: str) -> Optional[Organization]:
        with get_db_context(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM organizations WHERE id = ?;", (org_id,))
            r = cur.fetchone()
            if not r:
                return None
            return Organization(id=r["id"], name=r["name"], created_at=r["created_at"], updated_at=r["updated_at"])

    def create_project(self, proj: Project) -> Project:
        with get_db_context(self.db_path) as conn:
            conn.execute(
                "INSERT INTO projects (id, organization_id, name, description, business_criticality, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?);",
                (proj.id, proj.organization_id, proj.name, proj.description, proj.business_criticality, proj.created_at, proj.updated_at),
            )
        return proj

    def list_projects(self, org_id: Optional[str] = None) -> List[Project]:
        with get_db_context(self.db_path) as conn:
            cur = conn.cursor()
            if org_id:
                cur.execute("SELECT * FROM projects WHERE organization_id = ? ORDER BY created_at ASC;", (org_id,))
            else:
                cur.execute("SELECT * FROM projects ORDER BY created_at ASC;")
            return [
                Project(
                    id=r["id"],
                    organization_id=r["organization_id"],
                    name=r["name"],
                    description=r["description"] or "",
                    business_criticality=r["business_criticality"] or "high",
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                )
                for r in cur.fetchall()
            ]

    def get_project(self, proj_id: str) -> Optional[Project]:
        with get_db_context(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM projects WHERE id = ?;", (proj_id,))
            r = cur.fetchone()
            if not r:
                return None
            return Project(
                id=r["id"],
                organization_id=r["organization_id"],
                name=r["name"],
                description=r["description"] or "",
                business_criticality=r["business_criticality"] or "high",
                created_at=r["created_at"],
                updated_at=r["updated_at"],
            )

    def create_repository(self, repo: Repository) -> Repository:
        with get_db_context(self.db_path) as conn:
            conn.execute(
                "INSERT INTO repositories (id, project_id, name, provider, url, default_branch, environment, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);",
                (repo.id, repo.project_id, repo.name, repo.provider, repo.url, repo.default_branch, repo.environment, repo.created_at, repo.updated_at),
            )
        return repo

    def list_repositories(self, project_id: Optional[str] = None) -> List[Repository]:
        with get_db_context(self.db_path) as conn:
            cur = conn.cursor()
            if project_id:
                cur.execute("SELECT * FROM repositories WHERE project_id = ? ORDER BY created_at ASC;", (project_id,))
            else:
                cur.execute("SELECT * FROM repositories ORDER BY created_at ASC;")
            return [
                Repository(
                    id=r["id"],
                    project_id=r["project_id"],
                    name=r["name"],
                    provider=r["provider"] or "git",
                    url=r["url"] or "",
                    default_branch=r["default_branch"] or "main",
                    environment=r["environment"] or "production",
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                )
                for r in cur.fetchall()
            ]

    def get_repository(self, repo_id: str) -> Optional[Repository]:
        with get_db_context(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM repositories WHERE id = ?;", (repo_id,))
            r = cur.fetchone()
            if not r:
                return None
            return Repository(
                id=r["id"],
                project_id=r["project_id"],
                name=r["name"],
                provider=r["provider"] or "git",
                url=r["url"] or "",
                default_branch=r["default_branch"] or "main",
                environment=r["environment"] or "production",
                created_at=r["created_at"],
                updated_at=r["updated_at"],
            )

    # --------------------------------------------------------------------------
    # Scans & Observations
    # --------------------------------------------------------------------------
    def start_scan(self, scan_record: ScanRecord) -> ScanRecord:
        with get_db_context(self.db_path) as conn:
            conn.execute(
                "INSERT INTO scans (id, repository_id, started_at, completed_at, status, commit_sha, branch, scanner_version, source_type, asset_count, error_count) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
                (
                    scan_record.id,
                    scan_record.repository_id,
                    scan_record.started_at,
                    scan_record.completed_at,
                    scan_record.status.value if isinstance(scan_record.status, ScanStatus) else scan_record.status,
                    scan_record.commit_sha,
                    scan_record.branch,
                    scan_record.scanner_version,
                    scan_record.source_type,
                    scan_record.asset_count,
                    scan_record.error_count,
                ),
            )
        return scan_record

    def complete_scan(self, scan_id: str, asset_count: int, error_count: int, status: ScanStatus = ScanStatus.COMPLETED) -> Optional[ScanRecord]:
        now = utc_now_iso()
        with get_db_context(self.db_path) as conn:
            conn.execute(
                "UPDATE scans SET completed_at = ?, status = ?, asset_count = ?, error_count = ? WHERE id = ?;",
                (now, status.value if isinstance(status, ScanStatus) else status, asset_count, error_count, scan_id),
            )
        return self.get_scan(scan_id)

    def get_scan(self, scan_id: str) -> Optional[ScanRecord]:
        with get_db_context(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM scans WHERE id = ?;", (scan_id,))
            r = cur.fetchone()
            if not r:
                return None
            return ScanRecord(
                id=r["id"],
                repository_id=r["repository_id"],
                started_at=r["started_at"],
                completed_at=r["completed_at"],
                status=ScanStatus(r["status"]),
                commit_sha=r["commit_sha"],
                branch=r["branch"],
                scanner_version=r["scanner_version"],
                source_type=r["source_type"],
                asset_count=r["asset_count"],
                error_count=r["error_count"],
            )

    def list_scans(self, repo_id: Optional[str] = None) -> List[ScanRecord]:
        with get_db_context(self.db_path) as conn:
            cur = conn.cursor()
            if repo_id:
                cur.execute("SELECT * FROM scans WHERE repository_id = ? ORDER BY started_at DESC;", (repo_id,))
            else:
                cur.execute("SELECT * FROM scans ORDER BY started_at DESC;")
            return [
                ScanRecord(
                    id=r["id"],
                    repository_id=r["repository_id"],
                    started_at=r["started_at"],
                    completed_at=r["completed_at"],
                    status=ScanStatus(r["status"]),
                    commit_sha=r["commit_sha"],
                    branch=r["branch"],
                    scanner_version=r["scanner_version"],
                    source_type=r["source_type"],
                    asset_count=r["asset_count"],
                    error_count=r["error_count"],
                )
                for r in cur.fetchall()
            ]

    def save_crypto_asset(self, asset: CryptoAssetRecord) -> None:
        with get_db_context(self.db_path) as conn:
            conn.execute(
                """INSERT INTO crypto_assets (
                    asset_id, algorithm, category, purpose, language, library, key_length, mode, padding, source_path, line_number, evidence_json, detection_rule, confidence, certificate_metadata_json, key_metadata_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(asset_id) DO UPDATE SET
                    purpose=excluded.purpose,
                    language=excluded.language,
                    library=excluded.library,
                    key_length=excluded.key_length,
                    mode=excluded.mode,
                    padding=excluded.padding,
                    source_path=excluded.source_path,
                    line_number=excluded.line_number,
                    evidence_json=excluded.evidence_json,
                    certificate_metadata_json=excluded.certificate_metadata_json,
                    key_metadata_json=excluded.key_metadata_json;""",
                (
                    asset.asset_id,
                    asset.algorithm,
                    asset.category,
                    asset.purpose,
                    asset.language,
                    asset.library,
                    asset.key_length,
                    asset.mode,
                    asset.padding,
                    asset.source_path,
                    asset.line_number,
                    asset.evidence_json,
                    asset.detection_rule,
                    asset.confidence,
                    asset.certificate_metadata_json,
                    asset.key_metadata_json,
                    asset.created_at,
                ),
            )

    def save_observation(self, obs: ObservationRecord) -> None:
        with get_db_context(self.db_path) as conn:
            conn.execute(
                "INSERT INTO observations (id, asset_id, scan_id, repository_id, observed_at, source_path, line_number, status, fingerprint) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);",
                (
                    obs.id,
                    obs.asset_id,
                    obs.scan_id,
                    obs.repository_id,
                    obs.observed_at,
                    obs.source_path,
                    obs.line_number,
                    obs.status.value if isinstance(obs.status, ObservationStatus) else obs.status,
                    obs.fingerprint,
                ),
            )

    def save_risk_snapshot(self, snap: RiskAssessmentSnapshot) -> None:
        with get_db_context(self.db_path) as conn:
            conn.execute(
                "INSERT INTO risk_snapshots (id, observation_id, asset_id, scan_id, technical_quantum_risk, business_urgency, overall_priority, hndl_status, mosca_urgency, policy_json, assessed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
                (
                    snap.id,
                    snap.observation_id,
                    snap.asset_id,
                    snap.scan_id,
                    snap.technical_quantum_risk,
                    snap.business_urgency,
                    snap.overall_priority,
                    snap.hndl_status,
                    snap.mosca_urgency,
                    snap.policy_json,
                    snap.assessed_at,
                ),
            )

    def save_migration_snapshot(self, snap: MigrationAssessmentSnapshot) -> None:
        with get_db_context(self.db_path) as conn:
            conn.execute(
                "INSERT INTO migration_snapshots (id, observation_id, asset_id, scan_id, recommendation_type, target_algorithm, readiness_state, migration_priority, lifecycle_state, assessed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
                (
                    snap.id,
                    snap.observation_id,
                    snap.asset_id,
                    snap.scan_id,
                    snap.recommendation_type,
                    snap.target_algorithm,
                    snap.readiness_state,
                    snap.migration_priority,
                    snap.lifecycle_state,
                    snap.assessed_at,
                ),
            )

    def get_latest_scan_for_repo(self, repo_id: str, exclude_scan_id: Optional[str] = None) -> Optional[ScanRecord]:
        with get_db_context(self.db_path) as conn:
            cur = conn.cursor()
            if exclude_scan_id:
                cur.execute(
                    "SELECT * FROM scans WHERE repository_id = ? AND status = 'COMPLETED' AND id != ? ORDER BY started_at DESC LIMIT 1;",
                    (repo_id, exclude_scan_id),
                )
            else:
                cur.execute(
                    "SELECT * FROM scans WHERE repository_id = ? AND status = 'COMPLETED' ORDER BY started_at DESC LIMIT 1;",
                    (repo_id,),
                )
            r = cur.fetchone()
            if not r:
                return None
            return ScanRecord(
                id=r["id"],
                repository_id=r["repository_id"],
                started_at=r["started_at"],
                completed_at=r["completed_at"],
                status=ScanStatus(r["status"]),
                commit_sha=r["commit_sha"],
                branch=r["branch"],
                scanner_version=r["scanner_version"],
                source_type=r["source_type"],
                asset_count=r["asset_count"],
                error_count=r["error_count"],
            )

    def get_scan_observations(self, scan_id: str) -> List[Dict[str, Any]]:
        with get_db_context(self.db_path) as conn:
            cur = conn.cursor()
            query = """
            SELECT o.*, a.algorithm, a.category, a.purpose, a.language, a.library, a.key_length,
                   r.overall_priority, r.technical_quantum_risk, r.hndl_status, r.mosca_urgency,
                   m.recommendation_type, m.target_algorithm, m.readiness_state, m.lifecycle_state, m.migration_priority
            FROM observations o
            JOIN crypto_assets a ON o.asset_id = a.asset_id
            LEFT JOIN risk_snapshots r ON o.id = r.observation_id
            LEFT JOIN migration_snapshots m ON o.id = m.observation_id
            WHERE o.scan_id = ?;
            """
            cur.execute(query, (scan_id,))
            return [dict(r) for r in cur.fetchall()]

    def mark_absent_observations(self, repo_id: str, scan_id: str, active_asset_ids: List[str]) -> None:
        with get_db_context(self.db_path) as conn:
            cur = conn.cursor()
            # Mark previous active observations for this repo as REMOVED if not present in active_asset_ids
            if not active_asset_ids:
                cur.execute(
                    "UPDATE observations SET status = 'REMOVED' WHERE repository_id = ? AND scan_id != ? AND status = 'ACTIVE';",
                    (repo_id, scan_id),
                )
            else:
                placeholders = ",".join("?" for _ in active_asset_ids)
                params = [repo_id, scan_id] + list(active_asset_ids)
                cur.execute(
                    f"UPDATE observations SET status = 'REMOVED' WHERE repository_id = ? AND scan_id != ? AND status = 'ACTIVE' AND asset_id NOT IN ({placeholders});",
                    params,
                )

    def get_inventory_assets(
        self,
        repo_id: Optional[str] = None,
        project_id: Optional[str] = None,
        org_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        with get_db_context(self.db_path) as conn:
            cur = conn.cursor()
            query = """
            SELECT a.*, o.id as observation_id, o.scan_id, o.repository_id, o.observed_at, o.status as observation_status,
                   r.technical_quantum_risk, r.business_urgency, r.overall_priority, r.hndl_status, r.mosca_urgency,
                   m.recommendation_type, m.target_algorithm, m.readiness_state, m.migration_priority, m.lifecycle_state,
                   COALESCE((SELECT MIN(observed_at) FROM observations WHERE asset_id = a.asset_id), a.created_at) as first_seen,
                   COALESCE((SELECT MAX(observed_at) FROM observations WHERE asset_id = a.asset_id), a.created_at) as last_seen,
                   repo.name as repository_name
            FROM crypto_assets a
            LEFT JOIN observations o ON a.asset_id = o.asset_id AND (o.id IS NULL OR o.id IN (
                SELECT id FROM (
                    SELECT id, ROW_NUMBER() OVER(PARTITION BY asset_id ORDER BY observed_at DESC) as rn
                    FROM observations
                ) WHERE rn = 1
            ))
            LEFT JOIN repositories repo ON o.repository_id = repo.id
            LEFT JOIN projects proj ON repo.project_id = proj.id
            LEFT JOIN risk_snapshots r ON o.id = r.observation_id
            LEFT JOIN migration_snapshots m ON o.id = m.observation_id
            WHERE 1=1
            """
            params = []
            if repo_id:
                query += " AND (o.repository_id = ? OR o.repository_id IS NULL)"
                params.append(repo_id)
            elif project_id:
                query += " AND (repo.project_id = ? OR repo.project_id IS NULL)"
                params.append(project_id)
            elif org_id:
                query += " AND (proj.organization_id = ? OR proj.organization_id IS NULL)"
                params.append(org_id)

            query += " ORDER BY a.created_at DESC;"
            cur.execute(query, params)

            result = []
            for row in cur.fetchall():
                d = dict(row)
                d["evidence"] = json.loads(d["evidence_json"]) if d.get("evidence_json") else {}
                d["certificate_metadata"] = json.loads(d["certificate_metadata_json"]) if d.get("certificate_metadata_json") else None
                d["key_metadata"] = json.loads(d["key_metadata_json"]) if d.get("key_metadata_json") else None
                result.append(d)
            return result

    def get_asset_detail(self, asset_id: str) -> Optional[Dict[str, Any]]:
        with get_db_context(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM crypto_assets WHERE asset_id = ?;", (asset_id,))
            asset_row = cur.fetchone()
            if not asset_row:
                return None

            asset_dict = dict(asset_row)
            asset_dict["evidence"] = json.loads(asset_dict["evidence_json"]) if asset_dict.get("evidence_json") else {}
            asset_dict["certificate_metadata"] = json.loads(asset_dict["certificate_metadata_json"]) if asset_dict.get("certificate_metadata_json") else None
            asset_dict["key_metadata"] = json.loads(asset_dict["key_metadata_json"]) if asset_dict.get("key_metadata_json") else None

            # Fetch observation history
            cur.execute(
                """SELECT o.*, r.technical_quantum_risk, r.overall_priority, r.hndl_status, m.readiness_state, m.lifecycle_state
                   FROM observations o
                   LEFT JOIN risk_snapshots r ON o.id = r.observation_id
                   LEFT JOIN migration_snapshots m ON o.id = m.observation_id
                   WHERE o.asset_id = ?
                   ORDER BY o.observed_at DESC;""",
                (asset_id,),
            )
            obs_history = [dict(r) for r in cur.fetchall()]

            # Fetch drift history
            cur.execute("SELECT * FROM drift_events WHERE asset_id = ? ORDER BY detected_at DESC;", (asset_id,))
            drift_history = [dict(r) for r in cur.fetchall()]

            return {
                "asset": asset_dict,
                "first_seen": obs_history[-1]["observed_at"] if obs_history else asset_dict["created_at"],
                "last_seen": obs_history[0]["observed_at"] if obs_history else asset_dict["created_at"],
                "observation_history": obs_history,
                "drift_history": drift_history,
            }

    # --------------------------------------------------------------------------
    # Drift Events
    # --------------------------------------------------------------------------
    def save_drift_event(self, event: DriftEvent) -> DriftEvent:
        with get_db_context(self.db_path) as conn:
            conn.execute(
                "INSERT INTO drift_events (id, repository_id, scan_id, asset_id, type, severity, before_state_json, after_state_json, detected_at, explanation) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
                (
                    event.id,
                    event.repository_id,
                    event.scan_id,
                    event.asset_id,
                    event.type.value if isinstance(event.type, DriftType) else event.type,
                    event.severity.value if isinstance(event.severity, DriftSeverity) else event.severity,
                    event.before_state_json,
                    event.after_state_json,
                    event.detected_at,
                    event.explanation,
                ),
            )
        return event

    def list_drift_events(self, repo_id: Optional[str] = None, asset_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with get_db_context(self.db_path) as conn:
            cur = conn.cursor()
            query = "SELECT * FROM drift_events WHERE 1=1"
            params = []
            if repo_id:
                query += " AND repository_id = ?"
                params.append(repo_id)
            if asset_id:
                query += " AND asset_id = ?"
                params.append(asset_id)
            query += " ORDER BY detected_at DESC;"
            cur.execute(query, params)

            events = []
            for r in cur.fetchall():
                d = dict(r)
                d["before_state"] = json.loads(d["before_state_json"]) if d.get("before_state_json") else {}
                d["after_state"] = json.loads(d["after_state_json"]) if d.get("after_state_json") else {}
                events.append(d)
            return events

    # --------------------------------------------------------------------------
    # Alerts
    # --------------------------------------------------------------------------
    def save_alert(self, alert: Alert) -> Alert:
        with get_db_context(self.db_path) as conn:
            conn.execute(
                "INSERT INTO alerts (id, type, severity, scope_type, scope_id, repository_id, asset_id, message, created_at, updated_at, status, dedup_key) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
                (
                    alert.id,
                    alert.type.value if isinstance(alert.type, AlertType) else alert.type,
                    alert.severity.value if isinstance(alert.severity, AlertSeverity) else alert.severity,
                    alert.scope_type.value if isinstance(alert.scope_type, AlertScopeType) else alert.scope_type,
                    alert.scope_id,
                    alert.repository_id,
                    alert.asset_id,
                    alert.message,
                    alert.created_at,
                    alert.updated_at,
                    alert.status.value if isinstance(alert.status, AlertStatus) else alert.status,
                    alert.dedup_key,
                ),
            )
        return alert

    def find_active_alert_by_dedup_key(self, dedup_key: str) -> Optional[Alert]:
        with get_db_context(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM alerts WHERE dedup_key = ? AND status IN ('OPEN', 'ACKNOWLEDGED') ORDER BY created_at DESC LIMIT 1;",
                (dedup_key,),
            )
            r = cur.fetchone()
            if not r:
                return None
            return Alert(
                id=r["id"],
                type=AlertType(r["type"]),
                severity=AlertSeverity(r["severity"]),
                scope_type=AlertScopeType(r["scope_type"]),
                scope_id=r["scope_id"],
                repository_id=r["repository_id"],
                asset_id=r["asset_id"],
                message=r["message"],
                created_at=r["created_at"],
                updated_at=r["updated_at"],
                status=AlertStatus(r["status"]),
                dedup_key=r["dedup_key"],
            )

    def list_alerts(
        self,
        repo_id: Optional[str] = None,
        status: Optional[str] = None,
        severity: Optional[str] = None,
    ) -> List[Alert]:
        with get_db_context(self.db_path) as conn:
            cur = conn.cursor()
            query = "SELECT * FROM alerts WHERE 1=1"
            params = []
            if repo_id:
                query += " AND repository_id = ?"
                params.append(repo_id)
            if status:
                query += " AND status = ?"
                params.append(status)
            if severity:
                query += " AND severity = ?"
                params.append(severity)
            query += " ORDER BY created_at DESC;"
            cur.execute(query, params)
            return [
                Alert(
                    id=r["id"],
                    type=AlertType(r["type"]),
                    severity=AlertSeverity(r["severity"]),
                    scope_type=AlertScopeType(r["scope_type"]),
                    scope_id=r["scope_id"],
                    repository_id=r["repository_id"],
                    asset_id=r["asset_id"],
                    message=r["message"],
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                    status=AlertStatus(r["status"]),
                    dedup_key=r["dedup_key"],
                )
                for r in cur.fetchall()
            ]

    def get_alert(self, alert_id: str) -> Optional[Alert]:
        with get_db_context(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM alerts WHERE id = ?;", (alert_id,))
            r = cur.fetchone()
            if not r:
                return None
            return Alert(
                id=r["id"],
                type=AlertType(r["type"]),
                severity=AlertSeverity(r["severity"]),
                scope_type=AlertScopeType(r["scope_type"]),
                scope_id=r["scope_id"],
                repository_id=r["repository_id"],
                asset_id=r["asset_id"],
                message=r["message"],
                created_at=r["created_at"],
                updated_at=r["updated_at"],
                status=AlertStatus(r["status"]),
                dedup_key=r["dedup_key"],
            )

    def update_alert_status(self, alert_id: str, new_status: AlertStatus) -> Alert:
        alert = self.get_alert(alert_id)
        if not alert:
            raise ValueError(f"Alert with id '{alert_id}' not found.")
        
        alert.transition_to(new_status)
        with get_db_context(self.db_path) as conn:
            conn.execute(
                "UPDATE alerts SET status = ?, updated_at = ? WHERE id = ?;",
                (alert.status.value, alert.updated_at, alert.id),
            )
        return alert

    # --------------------------------------------------------------------------
    # Schedules
    # --------------------------------------------------------------------------
    def create_schedule(self, sched: ScanSchedule) -> ScanSchedule:
        with get_db_context(self.db_path) as conn:
            conn.execute(
                "INSERT INTO scan_schedules (id, repository_id, enabled, interval_hours, next_run_at, last_run_at, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?);",
                (
                    sched.id,
                    sched.repository_id,
                    1 if sched.enabled else 0,
                    sched.interval_hours,
                    sched.next_run_at,
                    sched.last_run_at,
                    sched.created_at,
                    sched.updated_at,
                ),
            )
        return sched

    def list_schedules(self, repo_id: Optional[str] = None) -> List[ScanSchedule]:
        with get_db_context(self.db_path) as conn:
            cur = conn.cursor()
            if repo_id:
                cur.execute("SELECT * FROM scan_schedules WHERE repository_id = ? ORDER BY created_at DESC;", (repo_id,))
            else:
                cur.execute("SELECT * FROM scan_schedules ORDER BY created_at DESC;")
            return [
                ScanSchedule(
                    id=r["id"],
                    repository_id=r["repository_id"],
                    enabled=bool(r["enabled"]),
                    interval_hours=r["interval_hours"],
                    next_run_at=r["next_run_at"],
                    last_run_at=r["last_run_at"],
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                )
                for r in cur.fetchall()
            ]

    def get_schedule(self, sched_id: str) -> Optional[ScanSchedule]:
        with get_db_context(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM scan_schedules WHERE id = ?;", (sched_id,))
            r = cur.fetchone()
            if not r:
                return None
            return ScanSchedule(
                id=r["id"],
                repository_id=r["repository_id"],
                enabled=bool(r["enabled"]),
                interval_hours=r["interval_hours"],
                next_run_at=r["next_run_at"],
                last_run_at=r["last_run_at"],
                created_at=r["created_at"],
                updated_at=r["updated_at"],
            )

    def update_schedule(self, sched_id: str, enabled: Optional[bool] = None, interval_hours: Optional[int] = None) -> ScanSchedule:
        sched = self.get_schedule(sched_id)
        if not sched:
            raise ValueError(f"ScanSchedule '{sched_id}' not found.")
        if enabled is not None:
            sched.enabled = enabled
        if interval_hours is not None:
            sched.interval_hours = interval_hours
        sched.updated_at = utc_now_iso()
        with get_db_context(self.db_path) as conn:
            conn.execute(
                "UPDATE scan_schedules SET enabled = ?, interval_hours = ?, updated_at = ? WHERE id = ?;",
                (1 if sched.enabled else 0, sched.interval_hours, sched.updated_at, sched.id),
            )
        return sched
