from pathlib import Path

from ecdat.discovery.base import AdvancedDiscoveryResult, DiscoveryFinding
from ecdat.inventory.store import InventoryStore
from ecdat.phase5_graph import CryptoGraph
from ecdat.phase5_inventory import AdvancedDiscoveryInventoryAdapter


def test_discovery_creates_inventory_observation_and_graph(tmp_path):
    store = InventoryStore(str(Path(tmp_path) / "inventory.db"))
    result = AdvancedDiscoveryResult("binary", "service")
    result.add_finding(DiscoveryFinding("binary", "service", "RSA_generate_key_ex", "RSA_generate_key_ex", .8, "imported_symbol", metadata={"algorithm": "RSA", "category": "asymmetric_encryption"}, identity_inputs=["rsa"]))
    summary = AdvancedDiscoveryInventoryAdapter(store).ingest(result, "repo-a")
    assert summary["findings_ingested"] == 1
    graph = CryptoGraph(store)
    assert len(graph.nodes) == 2
    assert len(graph.relationships) == 1

