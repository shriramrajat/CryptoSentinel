import unittest

from ecdat.discovery.base import DiscoveryFinding, finding_to_asset


class Phase5DiscoveryTests(unittest.TestCase):
    def test_finding_preserves_evidence_and_adapts_to_canonical_asset(self):
        finding = DiscoveryFinding("binary", "app/service", "EVP_sha256", "EVP_sha256", .8, "imported_symbol", "rule-1", identity_inputs=["EVP_sha256"])
        asset = finding_to_asset(finding)
        self.assertEqual(finding.finding_id, DiscoveryFinding("binary", "app/service", "EVP_sha256", "EVP_sha256", .8, "imported_symbol", "rule-1", identity_inputs=["EVP_sha256"]).finding_id)
        self.assertEqual(asset.evidence.code_snippet, "EVP_sha256")


if __name__ == "__main__":
    unittest.main()
