"""Database management and SQLite persistence initialization for Phase 4."""
import os
import sqlite3
import threading
from contextlib import contextmanager
from typing import Generator

def get_db_path() -> str:
    return os.getenv("AUDIT_DB_PATH", "crypto_inventory.db")


_local = threading.local()


def get_connection(db_path: str = None) -> sqlite3.Connection:
    if db_path is None:
        db_path = get_db_path()
    
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # Enable WAL mode and foreign keys for SQLite performance and reliability
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


@contextmanager
def get_db_context(db_path: str = None) -> Generator[sqlite3.Connection, None, None]:
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS organizations (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    business_criticality TEXT DEFAULT 'high',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS repositories (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    name TEXT NOT NULL,
    provider TEXT DEFAULT 'git',
    url TEXT,
    default_branch TEXT DEFAULT 'main',
    environment TEXT DEFAULT 'production',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS scans (
    id TEXT PRIMARY KEY,
    repository_id TEXT NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    status TEXT NOT NULL,
    commit_sha TEXT DEFAULT 'head',
    branch TEXT DEFAULT 'main',
    scanner_version TEXT DEFAULT '0.2.0',
    source_type TEXT DEFAULT 'repository',
    asset_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    FOREIGN KEY (repository_id) REFERENCES repositories(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS crypto_assets (
    asset_id TEXT PRIMARY KEY,
    algorithm TEXT NOT NULL,
    category TEXT NOT NULL,
    purpose TEXT,
    language TEXT,
    library TEXT,
    key_length INTEGER,
    mode TEXT,
    padding TEXT,
    source_path TEXT NOT NULL,
    line_number INTEGER NOT NULL,
    evidence_json TEXT NOT NULL,
    detection_rule TEXT DEFAULT 'unknown',
    confidence REAL DEFAULT 0.9,
    certificate_metadata_json TEXT,
    key_metadata_json TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS observations (
    id TEXT PRIMARY KEY,
    asset_id TEXT NOT NULL,
    scan_id TEXT NOT NULL,
    repository_id TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    source_path TEXT NOT NULL,
    line_number INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    fingerprint TEXT,
    FOREIGN KEY (asset_id) REFERENCES crypto_assets(asset_id) ON DELETE CASCADE,
    FOREIGN KEY (scan_id) REFERENCES scans(id) ON DELETE CASCADE,
    FOREIGN KEY (repository_id) REFERENCES repositories(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS risk_snapshots (
    id TEXT PRIMARY KEY,
    observation_id TEXT NOT NULL,
    asset_id TEXT NOT NULL,
    scan_id TEXT NOT NULL,
    technical_quantum_risk TEXT NOT NULL,
    business_urgency TEXT NOT NULL,
    overall_priority TEXT NOT NULL,
    hndl_status TEXT NOT NULL,
    mosca_urgency TEXT NOT NULL,
    policy_json TEXT NOT NULL,
    assessed_at TEXT NOT NULL,
    FOREIGN KEY (observation_id) REFERENCES observations(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS migration_snapshots (
    id TEXT PRIMARY KEY,
    observation_id TEXT NOT NULL,
    asset_id TEXT NOT NULL,
    scan_id TEXT NOT NULL,
    recommendation_type TEXT NOT NULL,
    target_algorithm TEXT,
    readiness_state TEXT NOT NULL,
    migration_priority TEXT NOT NULL,
    lifecycle_state TEXT NOT NULL,
    assessed_at TEXT NOT NULL,
    FOREIGN KEY (observation_id) REFERENCES observations(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS drift_events (
    id TEXT PRIMARY KEY,
    repository_id TEXT NOT NULL,
    scan_id TEXT NOT NULL,
    asset_id TEXT NOT NULL,
    type TEXT NOT NULL,
    severity TEXT NOT NULL,
    before_state_json TEXT NOT NULL,
    after_state_json TEXT NOT NULL,
    detected_at TEXT NOT NULL,
    explanation TEXT,
    FOREIGN KEY (repository_id) REFERENCES repositories(id) ON DELETE CASCADE,
    FOREIGN KEY (scan_id) REFERENCES scans(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS alerts (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    severity TEXT NOT NULL,
    scope_type TEXT NOT NULL,
    scope_id TEXT NOT NULL,
    repository_id TEXT NOT NULL,
    asset_id TEXT,
    message TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'OPEN',
    dedup_key TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS scan_schedules (
    id TEXT PRIMARY KEY,
    repository_id TEXT NOT NULL,
    enabled INTEGER NOT NULL DEFAULT 1,
    interval_hours INTEGER NOT NULL DEFAULT 24,
    next_run_at TEXT NOT NULL,
    last_run_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (repository_id) REFERENCES repositories(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS crypto_graph_nodes (
    node_id TEXT PRIMARY KEY,
    node_type TEXT NOT NULL,
    label TEXT NOT NULL,
    metadata_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS crypto_graph_relationships (
    relationship_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    relationship_type TEXT NOT NULL,
    metadata_json TEXT NOT NULL,
    UNIQUE(source_id, target_id, relationship_type)
);

CREATE INDEX IF NOT EXISTS idx_projects_org ON projects(organization_id);
CREATE INDEX IF NOT EXISTS idx_repos_project ON repositories(project_id);
CREATE INDEX IF NOT EXISTS idx_scans_repo ON scans(repository_id);
CREATE INDEX IF NOT EXISTS idx_obs_asset ON observations(asset_id);
CREATE INDEX IF NOT EXISTS idx_obs_scan ON observations(scan_id);
CREATE INDEX IF NOT EXISTS idx_obs_repo ON observations(repository_id);
CREATE INDEX IF NOT EXISTS idx_drift_repo ON drift_events(repository_id);
CREATE INDEX IF NOT EXISTS idx_alerts_dedup ON alerts(dedup_key);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);
"""


def init_db(db_path: str = None) -> None:
    """Initialize SQLite database, apply migrations, and create default organization/project/repository if empty."""
    with get_db_context(db_path) as conn:
        conn.executescript(SCHEMA_SQL)
        
        # Check migration version
        cur = conn.cursor()
        cur.execute("SELECT MAX(version) FROM schema_migrations;")
        row = cur.fetchone()
        current_version = row[0] if row and row[0] is not None else 0
        
        if current_version < 1:
            cur.execute("INSERT INTO schema_migrations (version, applied_at) VALUES (1, datetime('now'));")
            
        # Ensure default Organization, Project, and Repository exist
        cur.execute("SELECT COUNT(*) FROM organizations;")
        if cur.fetchone()[0] == 0:
            default_org_id = "org-default"
            default_proj_id = "proj-default"
            default_repo_id = "repo-default"
            
            cur.execute(
                "INSERT INTO organizations (id, name, created_at, updated_at) VALUES (?, ?, datetime('now'), datetime('now'));",
                (default_org_id, "Enterprise Core"),
            )
            cur.execute(
                "INSERT INTO projects (id, organization_id, name, description, business_criticality, created_at, updated_at) VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'));",
                (default_proj_id, default_org_id, "Main System", "Primary Enterprise System", "high"),
            )
            cur.execute(
                "INSERT INTO repositories (id, project_id, name, provider, url, default_branch, environment, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'));",
                (default_repo_id, default_proj_id, "CryptoSentinel Repo", "git", "https://github.com/shriramrajat/CryptoSentinel", "main", "production"),
            )
