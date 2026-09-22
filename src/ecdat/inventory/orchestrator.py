"""Orchestration layer combining ScanService (Phases 1-3) with Phase 4 Inventory & Monitoring."""
import json
from typing import Any, Dict, List, Optional

from ecdat.inventory.alerts import evaluate_alerts_for_scan
from ecdat.inventory.drift import detect_drift
from ecdat.inventory.models import (
    CryptoAssetRecord,
    MigrationAssessmentSnapshot,
    ObservationRecord,
    ObservationStatus,
    RiskAssessmentSnapshot,
    ScanRecord,
    ScanStatus,
)
from ecdat.inventory.store import InventoryStore
from ecdat.service import ScanService, SCANNER_VERSION


class EnterpriseScanOrchestrator:
    def __init__(self, store: Optional[InventoryStore] = None):
        self.store = store or InventoryStore()
        self.service = ScanService()

    def run_enterprise_scan(
        self,
        target_path: str,
        repository_id: Optional[str] = None,
        language_filters: Optional[List[str]] = None,
        generate_cbom: bool = False,
        user_context_map: Optional[Dict[str, Any]] = None,
        policy_config: Optional[Dict[str, Any]] = None,
        commit_sha: str = "head",
        branch: str = "main",
    ) -> Dict[str, Any]:
        """Run Phase 1-3 scan pipeline, persist scan/assets/observations, compute drift, and generate alerts."""
        if not repository_id:
            _, _, repository_id = self.store.get_or_create_default_hierarchy()

        repo = self.store.get_repository(repository_id)
        if not repo:
            raise ValueError(f"Repository '{repository_id}' does not exist.")

        # 1. Fetch previous completed scan observations for drift comparison
        prev_scan = self.store.get_latest_scan_for_repo(repository_id)
        prev_obs = self.store.get_scan_observations(prev_scan.id) if prev_scan else []

        # 2. Start Scan Record
        scan_rec = ScanRecord(
            repository_id=repository_id,
            commit_sha=commit_sha,
            branch=branch,
            scanner_version=SCANNER_VERSION,
            source_type="repository",
            status=ScanStatus.IN_PROGRESS,
        )
        scan_rec = self.store.start_scan(scan_rec)

        try:
            # 3. Execute Phases 1-3 scan pipeline
            result = self.service.run_scan(
                target_path=target_path,
                language_filters=language_filters,
                generate_cbom=generate_cbom,
                user_context_map=user_context_map,
                policy_config=policy_config,
            )
        except Exception as exc:
            # Mark scan as failed
            self.store.complete_scan(scan_rec.id, asset_count=0, error_count=1, status=ScanStatus.FAILED)
            raise exc

        findings = result.get("findings", [])
        errors = result.get("errors", [])

        active_asset_ids: List[str] = []

        # 4. Persist assets, observations, and snapshots
        for f in findings:
            asset_id = f["finding_id"]
            active_asset_ids.append(asset_id)
            loc = f.get("file_location", {})
            src_path = loc.get("file_path", "unknown")
            line_no = loc.get("line_number", 1)

            # Persist CryptoAssetRecord
            asset_rec = CryptoAssetRecord(
                asset_id=asset_id,
                algorithm=f["algorithm"],
                category=f["category"],
                purpose=f.get("purpose"),
                language=f.get("language"),
                library=f.get("library"),
                key_length=f.get("key_length"),
                mode=f.get("mode"),
                padding=f.get("padding"),
                source_path=src_path,
                line_number=line_no,
                evidence_json=json.dumps(f.get("evidence", {})),
                detection_rule=f.get("detection_rule", "unknown"),
                confidence=f.get("risk", {}).get("confidence", 0.9),
                certificate_metadata_json=json.dumps(f["certificate_metadata"]) if f.get("certificate_metadata") else None,
                key_metadata_json=json.dumps(f["key_metadata"]) if f.get("key_metadata") else None,
            )
            self.store.save_crypto_asset(asset_rec)

            # Persist ObservationRecord
            obs_rec = ObservationRecord(
                asset_id=asset_id,
                scan_id=scan_rec.id,
                repository_id=repository_id,
                source_path=src_path,
                line_number=line_no,
                status=ObservationStatus.ACTIVE,
                fingerprint=f"{asset_id}:{src_path}:{line_no}",
            )
            self.store.save_observation(obs_rec)

            # Persist RiskAssessmentSnapshot
            risk = f.get("risk", {})
            qri = f.get("quantum_risk_intelligence", {})
            risk_snap = RiskAssessmentSnapshot(
                observation_id=obs_rec.id,
                asset_id=asset_id,
                scan_id=scan_rec.id,
                technical_quantum_risk=qri.get("technical_quantum_risk", risk.get("severity", "medium")),
                business_urgency=qri.get("business_urgency", "medium"),
                overall_priority=qri.get("overall_priority", "MONITOR"),
                hndl_status=qri.get("hndl_assessment", {}).get("status", "NOT_APPLICABLE"),
                mosca_urgency=qri.get("lifecycle_assessment", {}).get("urgency", "LOW"),
                policy_json=json.dumps(result.get("metadata", {}).get("policy", {})),
            )
            self.store.save_risk_snapshot(risk_snap)

            # Persist MigrationAssessmentSnapshot
            mig_intel = f.get("migration_intelligence", {})
            rec = mig_intel.get("recommendation", {})
            readiness = mig_intel.get("readiness", {})
            mig_snap = MigrationAssessmentSnapshot(
                observation_id=obs_rec.id,
                asset_id=asset_id,
                scan_id=scan_rec.id,
                recommendation_type=rec.get("migration_type", "DIRECT"),
                target_algorithm=rec.get("target_algorithm", ""),
                readiness_state=readiness.get("state", "UNKNOWN"),
                migration_priority=mig_intel.get("migration_priority", "LOW"),
                lifecycle_state=mig_intel.get("lifecycle_record", {}).get("current_state", "DISCOVERED"),
            )
            self.store.save_migration_snapshot(mig_snap)

        # 5. Complete Scan Record
        self.store.complete_scan(scan_rec.id, asset_count=len(findings), error_count=len(errors))

        # 6. Update observation status for missing assets
        self.store.mark_absent_observations(repository_id, scan_rec.id, active_asset_ids)

        # 7. Compute Drift
        curr_obs = self.store.get_scan_observations(scan_rec.id)
        drift_events = detect_drift(repository_id, scan_rec.id, curr_obs, prev_obs)
        for drift in drift_events:
            self.store.save_drift_event(drift)

        # 8. Evaluate Alerts
        new_alerts = evaluate_alerts_for_scan(self.store, repository_id, scan_rec.id, curr_obs, drift_events)

        # 9. Attach Phase 4 metadata to scan response
        result["inventory_metadata"] = {
            "scan_id": scan_rec.id,
            "repository_id": repository_id,
            "drift_events_count": len(drift_events),
            "alerts_created_count": len(new_alerts),
            "total_active_assets": len(active_asset_ids),
        }

        return result
