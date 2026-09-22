import tempfile
import unittest
from pathlib import Path

from ecdat.discovery.protocol import ProtocolScanner


class Phase5ProtocolTests(unittest.TestCase):
    def test_tls_is_structured(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tls.conf"
            path.write_text("TLS 1.2 ECDHE-RSA-AES256-GCM-SHA384", encoding="utf-8")
            protocol = ProtocolScanner().scan(str(path)).protocols[0]
            self.assertEqual(protocol["protocol"], "TLS")
            self.assertEqual(protocol["version"], "1.2")


if __name__ == "__main__":
    unittest.main()
