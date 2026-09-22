"""Adapter from evidence-preserving Phase 5 results into the Phase 4 inventory."""

from typing import Any, Dict, Optional

from .discovery.base import AdvancedDiscoveryResult, finding_to_asset, stable_id, utc_now
from .inventory.store import InventoryStore
from .phase5_graph import CryptoGraph


class AdvancedDiscoveryInventoryAdapter:
    """Uses the Phase 4 InventoryStore; it does not persist a second inventory."""

    def __init__(self, store: Optional[InventoryStore] = None) -> None:
        self.store = store or InventoryStore()

    def ingest(self, result: AdvancedDiscoveryResult, repo_id: str, repo_name: str = "default-repo", org_id: str = "default-org", project_id: str = "default-project") -> Dict[str, Any]:
        assets = []
        for finding in result.findings:
            asset = finding_to_asset(finding)
            if asset.algorithm == "UNKNOWN":
                continue
            assets.append({
                "asset_id": asset.asset_id,
                "asset_category": asset.category,
                "algorithm": asset.algorithm,
                "key_size": asset.key_length,
                "file_path": asset.file_path,
                "line_number": asset.line_number,
                "code_snippet": asset.evidence.code_snippet,
                "function_context": finding.detection_mechanism,
                "quantum_risk_tier": "HIGH" if asset.algorithm.upper() in {"RSA", "DH", "ECDH", "ECC"} else "LOW",
                "hndl_vulnerable": asset.algorithm.upper() in {"RSA", "DH", "ECDH", "ECC"},
                "is_deprecated": asset.algorithm.upper() in {"MD5", "SHA-1", "DES", "RC4"},
                "migration_status": "NOT_STARTED",
            })
        graph = CryptoGraph(self.store)
        repository = graph.add_node("REPOSITORY", repo_id, {"repo_name": repo_name})
        for item in assets:
            asset_node = graph.add_node("CRYPTO_ASSET", item["asset_id"], {"algorithm": item["algorithm"], "file_path": item["file_path"]})
            graph.add_relationship(repository.node_id, asset_node.node_id, "CONTAINS")
        summary = {
            "source_type": result.source_type,
            "findings_ingested": len(assets),
            "repo_id": repo_id,
        }
        return summary

