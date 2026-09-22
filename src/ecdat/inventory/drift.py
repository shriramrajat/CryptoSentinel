"""Deterministic drift detection engine for Phase 4."""
import json
from typing import Any, Dict, List, Optional
from ecdat.inventory.models import DriftEvent, DriftSeverity, DriftType

PRIORITY_RANK = {
    "IMMEDIATE_ACTION": 5,
    "PLANNING_REQUIRED": 4,
    "NEEDS_CONTEXT": 3,
    "MONITOR": 2,
    "LOW_PRIORITY": 1,
}

SEVERITY_RANK = {
    "critical": 5,
    "high": 4,
    "medium": 3,
    "low": 2,
    "info": 1,
    "unknown": 0,
}

LIFECYCLE_RANK = {
    "DISCOVERED": 1,
    "PLANNING": 2,
    "IN_PROGRESS": 3,
    "MIGRATING": 3,
    "TESTING": 4,
    "COMPLETED": 5,
    "MIGRATED": 5,
    "DEPRECATED": 5,
}


def detect_drift(
    repository_id: str,
    scan_id: str,
    current_obs: List[Dict[str, Any]],
    previous_obs: List[Dict[str, Any]],
) -> List[DriftEvent]:
    """Compare current scan observations against previous scan observations to produce deterministic DriftEvents."""
    drift_events: List[DriftEvent] = []

    curr_by_id = {obs["asset_id"]: obs for obs in current_obs}
    prev_by_id = {obs["asset_id"]: obs for obs in previous_obs}

    # 1. NEW_ASSET & REGRESSION/PROGRESS check
    for asset_id, curr in curr_by_id.items():
        if asset_id not in prev_by_id:
            # Check if this new asset is quantum vulnerable or high priority
            priority = curr.get("overall_priority", "MONITOR")
            sev = DriftSeverity.HIGH if priority in ("IMMEDIATE_ACTION", "PLANNING_REQUIRED") else DriftSeverity.INFO
            drift_events.append(
                DriftEvent(
                    repository_id=repository_id,
                    scan_id=scan_id,
                    asset_id=asset_id,
                    type=DriftType.NEW_ASSET,
                    severity=sev,
                    before_state_json="{}",
                    after_state_json=json.dumps({
                        "algorithm": curr.get("algorithm"),
                        "source_path": curr.get("source_path"),
                        "line_number": curr.get("line_number"),
                        "priority": priority,
                    }),
                    explanation=f"New cryptographic asset '{curr.get('algorithm')}' detected at {curr.get('source_path')}:{curr.get('line_number')}.",
                )
            )
        else:
            prev = prev_by_id[asset_id]
            # MODIFIED_ASSET check
            if (
                curr.get("algorithm") != prev.get("algorithm")
                or curr.get("key_length") != prev.get("key_length")
                or curr.get("purpose") != prev.get("purpose")
            ):
                drift_events.append(
                    DriftEvent(
                        repository_id=repository_id,
                        scan_id=scan_id,
                        asset_id=asset_id,
                        type=DriftType.MODIFIED_ASSET,
                        severity=DriftSeverity.MEDIUM,
                        before_state_json=json.dumps({
                            "algorithm": prev.get("algorithm"),
                            "key_length": prev.get("key_length"),
                            "purpose": prev.get("purpose"),
                        }),
                        after_state_json=json.dumps({
                            "algorithm": curr.get("algorithm"),
                            "key_length": curr.get("key_length"),
                            "purpose": curr.get("purpose"),
                        }),
                        explanation=f"Asset '{asset_id}' parameters modified from {prev.get('algorithm')} ({prev.get('key_length')} bits) to {curr.get('algorithm')} ({curr.get('key_length')} bits).",
                    )
                )

            # RISK_REGRESSION or RISK_IMPROVEMENT check
            curr_prio_rank = PRIORITY_RANK.get(curr.get("overall_priority", "MONITOR"), 2)
            prev_prio_rank = PRIORITY_RANK.get(prev.get("overall_priority", "MONITOR"), 2)
            curr_sev_rank = SEVERITY_RANK.get(curr.get("technical_quantum_risk", "info"), 1)
            prev_sev_rank = SEVERITY_RANK.get(prev.get("technical_quantum_risk", "info"), 1)

            if curr_prio_rank > prev_prio_rank or curr_sev_rank > prev_sev_rank:
                drift_events.append(
                    DriftEvent(
                        repository_id=repository_id,
                        scan_id=scan_id,
                        asset_id=asset_id,
                        type=DriftType.RISK_REGRESSION,
                        severity=DriftSeverity.HIGH if curr_prio_rank >= 4 else DriftSeverity.MEDIUM,
                        before_state_json=json.dumps({
                            "priority": prev.get("overall_priority"),
                            "risk": prev.get("technical_quantum_risk"),
                        }),
                        after_state_json=json.dumps({
                            "priority": curr.get("overall_priority"),
                            "risk": curr.get("technical_quantum_risk"),
                        }),
                        explanation=f"Risk regression on asset '{asset_id}': priority increased from {prev.get('overall_priority')} to {curr.get('overall_priority')}.",
                    )
                )
            elif curr_prio_rank < prev_prio_rank or curr_sev_rank < prev_sev_rank:
                drift_events.append(
                    DriftEvent(
                        repository_id=repository_id,
                        scan_id=scan_id,
                        asset_id=asset_id,
                        type=DriftType.RISK_IMPROVEMENT,
                        severity=DriftSeverity.INFO,
                        before_state_json=json.dumps({
                            "priority": prev.get("overall_priority"),
                            "risk": prev.get("technical_quantum_risk"),
                        }),
                        after_state_json=json.dumps({
                            "priority": curr.get("overall_priority"),
                            "risk": curr.get("technical_quantum_risk"),
                        }),
                        explanation=f"Risk improvement on asset '{asset_id}': priority decreased from {prev.get('overall_priority')} to {curr.get('overall_priority')}.",
                    )
                )

            # MIGRATION_PROGRESS or MIGRATION_REGRESSION check
            curr_life_rank = LIFECYCLE_RANK.get(curr.get("lifecycle_state", "DISCOVERED"), 1)
            prev_life_rank = LIFECYCLE_RANK.get(prev.get("lifecycle_state", "DISCOVERED"), 1)

            if curr_life_rank > prev_life_rank:
                drift_events.append(
                    DriftEvent(
                        repository_id=repository_id,
                        scan_id=scan_id,
                        asset_id=asset_id,
                        type=DriftType.MIGRATION_PROGRESS,
                        severity=DriftSeverity.INFO,
                        before_state_json=json.dumps({"lifecycle_state": prev.get("lifecycle_state")}),
                        after_state_json=json.dumps({"lifecycle_state": curr.get("lifecycle_state")}),
                        explanation=f"Migration progress on asset '{asset_id}': lifecycle state advanced to {curr.get('lifecycle_state')}.",
                    )
                )
            elif curr_life_rank < prev_life_rank:
                drift_events.append(
                    DriftEvent(
                        repository_id=repository_id,
                        scan_id=scan_id,
                        asset_id=asset_id,
                        type=DriftType.MIGRATION_REGRESSION,
                        severity=DriftSeverity.HIGH,
                        before_state_json=json.dumps({"lifecycle_state": prev.get("lifecycle_state")}),
                        after_state_json=json.dumps({"lifecycle_state": curr.get("lifecycle_state")}),
                        explanation=f"Migration regression on asset '{asset_id}': lifecycle state regressed from {prev.get('lifecycle_state')} to {curr.get('lifecycle_state')}.",
                    )
                )

    # 2. REMOVED_ASSET check
    for asset_id, prev in prev_by_id.items():
        if asset_id not in curr_by_id:
            drift_events.append(
                DriftEvent(
                    repository_id=repository_id,
                    scan_id=scan_id,
                    asset_id=asset_id,
                    type=DriftType.REMOVED_ASSET,
                    severity=DriftSeverity.INFO,
                    before_state_json=json.dumps({
                        "algorithm": prev.get("algorithm"),
                        "source_path": prev.get("source_path"),
                        "line_number": prev.get("line_number"),
                    }),
                    after_state_json="{}",
                    explanation=f"Cryptographic asset '{prev.get('algorithm')}' removed from {prev.get('source_path')}:{prev.get('line_number')}.",
                )
            )

    return drift_events
