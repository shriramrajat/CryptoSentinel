import tempfile
import unittest
from pathlib import Path

from ecdat.discovery.binary import BinaryScanner
from ecdat.discovery.container import ContainerScanner


class Phase5SecurityTests(unittest.TestCase):
    def test_oversized_inputs_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "large.bin"
            path.write_bytes(b"MZ" + b"x" * (BinaryScanner.MAX_FILE_SIZE + 1))
            with self.assertRaises(ValueError):
                BinaryScanner().scan(str(path))

    def test_unsupported_container_is_explicit(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "image.bin"; path.write_bytes(b"not an image")
            self.assertIn("UNSUPPORTED_CONTAINER_FORMAT", ContainerScanner().scan(str(path)).errors)


if __name__ == "__main__":
    unittest.main()
