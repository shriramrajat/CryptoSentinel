"""Relational, deterministic cryptographic dependency graph."""

from dataclasses import asdict, dataclass
from typing import Any, Dict, Iterable, List, Optional

from .discovery.base import stable_id


@dataclass(frozen=True)
class GraphNode:
    node_id: str
    node_type: str
    label: str
    metadata: Dict[str, Any]


@dataclass(frozen=True)
class GraphRelationship:
    relationship_id: str
    source_id: str
    target_id: str
    relationship_type: str
    metadata: Dict[str, Any]


class CryptoGraph:
    def __init__(self, db: Optional[Any] = None) -> None:
        self.db = db
        self.nodes: Dict[str, GraphNode] = {}
        self.relationships: Dict[str, GraphRelationship] = {}
        if db:
            for node in db.get_graph_nodes():
                self.nodes[node["node_id"]] = GraphNode(node["node_id"], node["node_type"], node["label"], node["metadata"])
            for relationship in db.get_graph_relationships():
                self.relationships[relationship["relationship_id"]] = GraphRelationship(relationship["relationship_id"], relationship["source_id"], relationship["target_id"], relationship["relationship_type"], relationship["metadata"])

    def add_node(self, node_type: str, label: str, metadata: Optional[Dict[str, Any]] = None, node_id: Optional[str] = None) -> GraphNode:
        identity = node_id or stable_id("node", [node_type, label])
        node = GraphNode(identity, node_type.upper(), label, metadata or {})
        self.nodes[identity] = node
        if self.db:
            self.db.upsert_graph_node(asdict(node))
        return node

    def add_relationship(self, source_id: str, target_id: str, relationship_type: str, metadata: Optional[Dict[str, Any]] = None) -> GraphRelationship:
        if source_id not in self.nodes or target_id not in self.nodes:
            raise KeyError("Both relationship endpoints must exist")
        identity = stable_id("rel", [source_id, target_id, relationship_type.upper()])
        relationship = GraphRelationship(identity, source_id, target_id, relationship_type.upper(), metadata or {})
        self.relationships[identity] = relationship
        if self.db:
            self.db.upsert_graph_relationship(asdict(relationship))
        return relationship

    def neighbors(self, node_id: str, relationship_type: Optional[str] = None) -> List[GraphNode]:
        rel_type = relationship_type.upper() if relationship_type else None
        target_ids = [rel.target_id for rel in self.relationships.values() if rel.source_id == node_id and (not rel_type or rel.relationship_type == rel_type)]
        return [self.nodes[target_id] for target_id in target_ids]

    def find(self, node_type: Optional[str] = None, label: Optional[str] = None) -> List[GraphNode]:
        return [node for node in self.nodes.values() if (not node_type or node.node_type == node_type.upper()) and (not label or label.lower() in node.label.lower())]

    def to_dict(self) -> Dict[str, Any]:
        return {"nodes": [asdict(node) for node in self.nodes.values()], "relationships": [asdict(rel) for rel in self.relationships.values()]}
