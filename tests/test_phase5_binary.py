import tempfile
import unittest
from pathlib import Path

from ecdat.discovery.binary import BinaryScanner


class Phase5BinaryTests(unittest.TestCase):
    def test_elf_indicators_are_not_claimed_as_direct_algorithm_use(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "service"
            path.write_bytes(b"\x7fELF" + b"libcrypto.so EVP_sha256")
            result = BinaryScanner().scan(str(path))
            self.assertEqual(result.findings[0].observation_type, "INFERRED_FROM_BINARY_INDICATOR")


if __name__ == "__main__":
    unittest.main()
