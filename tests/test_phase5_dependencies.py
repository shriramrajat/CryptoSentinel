import tempfile
import unittest
from pathlib import Path

from ecdat.discovery.dependency import DependencyScanner


class Phase5DependencyTests(unittest.TestCase):
    def test_dependency_presence_is_not_usage(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "requirements.txt"
            path.write_text("cryptography==42.0.0\n", encoding="utf-8")
            result = DependencyScanner().scan(str(path))
            self.assertEqual(result.dependencies[0]["evidence"], "DEPENDENCY_PRESENT")


if __name__ == "__main__":
    unittest.main()
