import unittest

from ecdat.phase5_graph import CryptoGraph


class Phase5GraphTests(unittest.TestCase):
    def test_relationships_are_deduplicated_and_traversable(self):
        graph = CryptoGraph(); app = graph.add_node("application", "api"); asset = graph.add_node("asset", "RSA")
        first = graph.add_relationship(app.node_id, asset.node_id, "USES")
        second = graph.add_relationship(app.node_id, asset.node_id, "USES")
        self.assertEqual(first.relationship_id, second.relationship_id)
        self.assertEqual(graph.neighbors(app.node_id)[0].label, "RSA")


if __name__ == "__main__":
    unittest.main()
