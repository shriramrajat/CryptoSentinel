# Phase 4 — Enterprise Cryptographic Inventory & Continuous Monitoring

## Overview

Phase 4 transforms CryptoSentinel from a scan-centric discovery and migration analysis tool into a persistent enterprise cryptographic inventory and continuous monitoring platform.

It adds historical tracking, observation management, deterministic drift detection, enterprise posture aggregation, deduplicated security alerts, and continuous scan scheduling on top of the Phase 1 discovery, Phase 2 risk, and Phase 3 migration intelligence engines.

---

## Architectural Hierarchy & Flow

```
Repository / Target
        ↓
Scan Execution (Phase 1 Discovery → Phase 2 Risk → Phase 3 Migration)
        ↓
ScanRecord & CryptoAsset Persistence
        ↓
Observation Record (first_seen / last_seen tracking)
        ↓
RiskAssessmentSnapshot & MigrationAssessmentSnapshot
        ↓
Deterministic Drift Detection (NEW, REMOVED, MODIFIED, REGRESSION, PROGRESS)
        ↓
Enterprise Posture Engine (Org, Project, Repo aggregation & trends)
        ↓
Alert Engine & Deduplication (OPEN → ACKNOWLEDGED → RESOLVED → REOPENED)
```

---

## Domain Model & Entities

1. **Organization (`organizations`)**: Top-level enterprise entity (`id`, `name`, `created_at`, `updated_at`).
2. **Project (`projects`)**: Application or system within an organization (`id`, `organization_id`, `name`, `description`, `business_criticality`, `created_at`, `updated_at`).
3. **Repository (`repositories`)**: Source repository (`id`, `project_id`, `name`, `provider`, `url`, `default_branch`, `environment`, `created_at`, `updated_at`).
4. **ScanRecord (`scans`)**: Execution instance of a scan (`id`, `repository_id`, `started_at`, `completed_at`, `status`, `commit_sha`, `branch`, `scanner_version`, `source_type`, `asset_count`, `error_count`).
5. **CryptoAssetRecord (`crypto_assets`)**: Preserves canonical Phase 1 asset identity (`asset_id`, `algorithm`, `category`, `purpose`, `language`, `library`, `key_length`, `mode`, `padding`, `source_path`, `line_number`, `evidence_json`, `detection_rule`, `confidence`, `certificate_metadata_json`, `key_metadata_json`, `created_at`).
6. **ObservationRecord (`observations`)**: Records an asset observation in a scan (`id`, `asset_id`, `scan_id`, `repository_id`, `observed_at`, `source_path`, `line_number`, `status`, `fingerprint`).
7. **RiskAssessmentSnapshot (`risk_snapshots`)**: Persists Phase 2 risk assessment outputs per observation (`id`, `observation_id`, `asset_id`, `scan_id`, `technical_quantum_risk`, `business_urgency`, `overall_priority`, `hndl_status`, `mosca_urgency`, `policy_json`, `assessed_at`).
8. **MigrationAssessmentSnapshot (`migration_snapshots`)**: Persists Phase 3 PQC migration intelligence outputs (`id`, `observation_id`, `asset_id`, `scan_id`, `recommendation_type`, `target_algorithm`, `readiness_state`, `migration_priority`, `lifecycle_state`, `assessed_at`).
9. **DriftEvent (`drift_events`)**: Persists detected changes between scans (`id`, `repository_id`, `scan_id`, `asset_id`, `type`, `severity`, `before_state_json`, `after_state_json`, `detected_at`, `explanation`).
10. **Alert (`alerts`)**: Deduplicated security incidents (`id`, `type`, `severity`, `scope_type`, `scope_id`, `repository_id`, `asset_id`, `message`, `created_at`, `updated_at`, `status`, `dedup_key`).
11. **ScanSchedule (`scan_schedules`)**: Persistence for automated scan definitions (`id`, `repository_id`, `enabled`, `interval_hours`, `next_run_at`, `last_run_at`, `created_at`, `updated_at`).

---

## Deterministic Drift Detection

Drift events are automatically evaluated on every scan against the repository's previous completed scan:

- **`NEW_ASSET`**: Asset discovered in current scan but absent in previous scan.
- **`REMOVED_ASSET`**: Asset present in previous scan but absent in current scan.
- **`MODIFIED_ASSET`**: Key parameters (algorithm, key length, purpose) modified.
- **`RISK_REGRESSION`**: Overall priority or quantum risk severity increased.
- **`RISK_IMPROVEMENT`**: Overall priority or quantum risk severity decreased.
- **`MIGRATION_PROGRESS`**: PQC lifecycle state or readiness state advanced towards migration.
- **`MIGRATION_REGRESSION`**: PQC lifecycle state regressed.

---

## Alert Engine & Deduplication

Alerts are automatically generated for security conditions:
- `WEAK_ALGORITHM_DETECTED` (MD5, DES, RC4, RSA <= 1024-bit, SHA-1)
- `QUANTUM_CRITICAL_ASSET` (Shor-vulnerable asset with IMMEDIATE_ACTION priority)
- `NEW_QUANTUM_VULNERABLE_ASSET`
- `CERTIFICATE_EXPIRING`
- `CRYPTO_REGRESSION`
- `MIGRATION_OVERDUE`
- `HIGH_PRIORITY_NEW_ASSET`
- `MIGRATION_STATE_REGRESSION`

### Deduplication Key
`dedup_key = sha256(type:scope_type:scope_id:asset_id)[:32]`

Active `OPEN` or `ACKNOWLEDGED` alerts matching the same deduplication key will not create duplicate alerts. If a previously `RESOLVED` alert re-occurs in a new scan, it is automatically transitioned to `OPEN`.

---

## Scheduling Capability & Limitations

Phase 4 introduces `ScanSchedule` records and API endpoints (`GET /api/v1/schedules`, `POST /api/v1/schedules`, `PATCH /api/v1/schedules/{id}`) for declaring automated recurring scan definitions. Scan schedules store `interval_hours`, `enabled`, `next_run_at`, and `last_run_at`.

*Execution Boundary Limitation*: Actual background cron job execution relies on external orchestrators or scheduled workers invoking `POST /api/v1/repositories/{id}/scans`. Heavy background queuing engines (such as Celery or Kafka) are intentionally excluded to keep the deployment lightweight.

---

## REST API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/organizations` | `POST` / `GET` | Create / List Organizations |
| `/api/v1/projects` | `POST` / `GET` | Create / List Projects |
| `/api/v1/repositories` | `POST` / `GET` | Create / List Repositories |
| `/api/v1/repositories/{id}/scans` | `POST` / `GET` | Trigger scan / List scans for repo |
| `/api/v1/scans/{id}` | `GET` | Get scan details & observations |
| `/api/v1/inventory` | `GET` | Query enterprise inventory assets |
| `/api/v1/inventory/assets/{id}` | `GET` | Get asset history & drift log |
| `/api/v1/drift` | `GET` | List drift events |
| `/api/v1/posture` | `GET` | Get global posture metrics |
| `/api/v1/posture/repository/{id}` | `GET` | Get repository posture metrics |
| `/api/v1/posture/trends` | `GET` | Get posture trends over time |
| `/api/v1/alerts` | `GET` / `PATCH` | List alerts / Update alert status |
| `/api/v1/schedules` | `GET` / `POST` / `PATCH` | Manage scan schedules |

---

## Security Considerations

1. **Redaction**: Raw private keys and credentials in evidence strings remain redacted via Phase 1 sanitize logic.
2. **Immutable History**: Completed `ScanRecord`s and `ObservationRecord`s are immutable historical logs.
3. **Storage Security**: Database file path defaults to `crypto_inventory.db` or environment variable `AUDIT_DB_PATH`.
