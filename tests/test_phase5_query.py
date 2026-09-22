import unittest
from datetime import datetime, timedelta, timezone

from ecdat.phase5_copilot import EvidenceCopilot
from ecdat.phase5_query import SecurityQueryEngine


class Phase5QueryTests(unittest.TestCase):
    def test_allowlist_and_unsupported_intent(self):
        engine = SecurityQueryEngine()
        self.assertEqual(engine.parse("show RSA assets")["status"], "SUPPORTED")
        self.assertEqual(engine.parse("drop table assets")["status"], "UNSUPPORTED_QUERY")
        self.assertEqual(EvidenceCopilot().explain({"algorithm": "RSA"})["status"], "OK")

    def test_all_allowlisted_filters_change_results(self):
        now = datetime.now(timezone.utc)
        assets = [
            {"asset_id": "rsa", "algorithm": "RSA", "repo_id": "payments", "first_seen": now.isoformat(), "migration_status": "IN_PROGRESS"},
            {"asset_id": "sha", "algorithm": "SHA-1", "repo_id": "legacy", "first_seen": (now - timedelta(days=30)).isoformat()},
            {"asset_id": "quantum", "algorithm": "ECC", "repo_id": "payments", "quantum_risk_tier": "HIGH", "first_seen": now.isoformat()},
            {"asset_id": "cert", "algorithm": "RSA", "repo_id": "payments", "first_seen": now.isoformat()},
        ]
        certificates = [{"asset_id": "cert", "is_expired": 1}]
        engine = SecurityQueryEngine()
        self.assertEqual(engine.execute("show RSA assets", assets)["total"], 2)
        self.assertEqual(engine.execute("show SHA-1 assets", assets)["results"][0]["asset_id"], "sha")
        self.assertEqual(engine.execute("show quantum vulnerable assets", assets)["results"][0]["asset_id"], "quantum")
        self.assertEqual(engine.execute("show expired certificates", assets, certificates)["results"][0]["asset_id"], "cert")
        self.assertEqual(engine.execute("show assets in migration IN_PROGRESS", assets)["results"][0]["asset_id"], "rsa")
        self.assertEqual(engine.execute("show new crypto discovered in the last 7 days", assets)["total"], 3)
        self.assertEqual(engine.execute("show RSA assets repository payments", assets)["total"], 2)
        self.assertEqual(engine.execute("show SHA-1 assets repository payments", assets)["total"], 0)


if __name__ == "__main__":
    unittest.main()
