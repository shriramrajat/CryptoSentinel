"""Deterministic alert generation and lifecycle engine for Phase 4."""
import json
import hashlib
from typing import Any, Dict, List, Optional

from ecdat.inventory.models import (
    Alert,
    AlertScopeType,
    AlertSeverity,
    AlertStatus,
    AlertType,
    DriftEvent,
    DriftType,
)
from ecdat.inventory.store import InventoryStore


def generate_dedup_key(alert_type: AlertType, scope_type: AlertScopeType, scope_id: str, asset_id: Optional[str]) -> str:
    raw = f"{alert_type.value}:{scope_type.value}:{scope_id}:{asset_id or ''}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def evaluate_alerts_for_scan(
    store: InventoryStore,
    repository_id: str,
    scan_id: str,
    observations: List[Dict[str, Any]],
    drift_events: List[DriftEvent],
) -> List[Alert]:
    """Evaluate current scan findings and drift events to generate or update alerts."""
    alerts_created_or_updated: List[Alert] = []

    def _process_alert(
        alert_type: AlertType,
        severity: AlertSeverity,
        scope_type: AlertScopeType,
        scope_id: str,
        asset_id: Optional[str],
        message: str,
    ) -> None:
        dedup_key = generate_dedup_key(alert_type, scope_type, scope_id, asset_id)
        existing = store.find_active_alert_by_dedup_key(dedup_key)
        if existing:
            # Active alert already exists, don't create duplicate
            return

        # Check if there is a resolved alert that needs reopening
        with store.get_db_context() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM alerts WHERE dedup_key = ? AND status = 'RESOLVED' ORDER BY created_at DESC LIMIT 1;",
                (dedup_key,),
            )
            res_row = cur.fetchone()

        if res_row:
            # Reopen resolved alert
            alert = store.get_alert(res_row["id"])
            if alert:
                alert.transition_to(AlertStatus.OPEN)
                with store.get_db_context() as conn:
                    conn.execute(
                        "UPDATE alerts SET status = 'OPEN', updated_at = datetime('now') WHERE id = ?;",
                        (alert.id,),
                    )
                alerts_created_or_updated.append(alert)
                return

        # Create new alert
        new_alert = Alert(
            type=alert_type,
            severity=severity,
            scope_type=scope_type,
            scope_id=scope_id,
            repository_id=repository_id,
            asset_id=asset_id,
            message=message,
            dedup_key=dedup_key,
        )
        saved = store.save_alert(new_alert)
        alerts_created_or_updated.append(saved)

    # 1. Evaluate Observations
    WEAK_ALGS = {"MD5", "DES", "3DES", "RC4", "SHA-1", "SHA1"}

    for obs in observations:
        asset_id = obs["asset_id"]
        alg = (obs.get("algorithm") or "").upper()
        key_len = obs.get("key_length")
        priority = obs.get("overall_priority", "MONITOR")
        tech_risk = obs.get("technical_quantum_risk", "info")
        cert_meta = obs.get("certificate_metadata")

        # WEAK_ALGORITHM_DETECTED
        if alg in WEAK_ALGS or (alg == "RSA" and key_len and key_len <= 1024):
            _process_alert(
                AlertType.WEAK_ALGORITHM_DETECTED,
                AlertSeverity.HIGH if alg in ("MD5", "DES", "RC4") or (alg == "RSA" and key_len and key_len <= 1024) else AlertSeverity.MEDIUM,
                AlertScopeType.ASSET,
                asset_id,
                asset_id,
                f"Weak cryptographic algorithm '{alg}' ({key_len or 'N/A'} bits) detected at {obs.get('source_path')}:{obs.get('line_number')}.",
            )

        # QUANTUM_CRITICAL_ASSET
        if priority == "IMMEDIATE_ACTION" or tech_risk == "critical":
            _process_alert(
                AlertType.QUANTUM_CRITICAL_ASSET,
                AlertSeverity.CRITICAL,
                AlertScopeType.ASSET,
                asset_id,
                asset_id,
                f"Quantum-critical asset '{alg}' with IMMEDIATE_ACTION priority detected at {obs.get('source_path')}:{obs.get('line_number')}.",
            )

        # CERTIFICATE_EXPIRING
        if cert_meta:
            if isinstance(cert_meta, str):
                try:
                    cert_meta = json.loads(cert_meta)
                except Exception:
                    cert_meta = {}
            if cert_meta.get("is_expired"):
                _process_alert(
                    AlertType.CERTIFICATE_EXPIRING,
                    AlertSeverity.HIGH,
                    AlertScopeType.ASSET,
                    asset_id,
                    asset_id,
                    f"Expired certificate detected for asset '{asset_id}' at {obs.get('source_path')}.",
                )

        # MIGRATION_OVERDUE
        if obs.get("mosca_urgency") in ("CRITICAL", "HIGH"):
            _process_alert(
                AlertType.MIGRATION_OVERDUE,
                AlertSeverity.HIGH,
                AlertScopeType.ASSET,
                asset_id,
                asset_id,
                f"PQC Migration is urgent/overdue (Mosca urgency '{obs.get('mosca_urgency')}') for asset '{asset_id}'.",
            )

    # 2. Evaluate Drift Events
    for drift in drift_events:
        d_type = drift.type if isinstance(drift.type, DriftType) else DriftType(drift.type)
        asset_id = drift.asset_id

        if d_type == DriftType.NEW_ASSET:
            # Check if new asset is high priority or quantum vulnerable
            after_st = json.loads(drift.after_state_json) if isinstance(drift.after_state_json, str) else drift.after_state_json
            if after_st.get("priority") == "IMMEDIATE_ACTION":
                _process_alert(
                    AlertType.HIGH_PRIORITY_NEW_ASSET,
                    AlertSeverity.CRITICAL,
                    AlertScopeType.ASSET,
                    asset_id,
                    asset_id,
                    f"New high-priority cryptographic asset detected: {drift.explanation}",
                )
            else:
                _process_alert(
                    AlertType.NEW_QUANTUM_VULNERABLE_ASSET,
                    AlertSeverity.MEDIUM,
                    AlertScopeType.ASSET,
                    asset_id,
                    asset_id,
                    f"New cryptographic asset introduced: {drift.explanation}",
                )

        elif d_type == DriftType.RISK_REGRESSION:
            _process_alert(
                AlertType.CRYPTO_REGRESSION,
                AlertSeverity.HIGH,
                AlertScopeType.ASSET,
                asset_id,
                asset_id,
                f"Cryptographic risk regression detected: {drift.explanation}",
            )

        elif d_type == DriftType.MIGRATION_REGRESSION:
            _process_alert(
                AlertType.MIGRATION_STATE_REGRESSION,
                AlertSeverity.HIGH,
                AlertScopeType.ASSET,
                asset_id,
                asset_id,
                f"PQC Migration state regressed: {drift.explanation}",
            )

    return alerts_created_or_updated
