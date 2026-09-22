"""In-memory stores for Phase 6 hardware and cloud discoveries.
These accumulate findings between API calls so GET endpoints can serve them.
Production deployments should persist to the Phase 4 InventoryStore.
"""
from __future__ import annotations
from typing import Any, Dict, List

_HW_FINDINGS: List[Dict[str, Any]] = []
_CLOUD_FINDINGS: List[Dict[str, Any]] = []

def add_hardware(findings: List[Dict[str, Any]]) -> None:
    """Append hardware findings; deduplicate by finding_id."""
    existing = {f.get("finding_id") for f in _HW_FINDINGS}
    for f in findings:
        if f.get("finding_id") not in existing:
            _HW_FINDINGS.append(f)
            existing.add(f.get("finding_id"))

def get_hardware() -> List[Dict[str, Any]]:
    return list(_HW_FINDINGS)

def add_cloud(findings: List[Dict[str, Any]]) -> None:
    existing = {f.get("finding_id") for f in _CLOUD_FINDINGS}
    for f in findings:
        if f.get("finding_id") not in existing:
            _CLOUD_FINDINGS.append(f)
            existing.add(f.get("finding_id"))

def get_cloud() -> List[Dict[str, Any]]:
    return list(_CLOUD_FINDINGS)

def clear_all() -> None:
    """Testing helper."""
    _HW_FINDINGS.clear()
    _CLOUD_FINDINGS.clear()
