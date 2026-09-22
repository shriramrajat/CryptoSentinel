import unittest
import tempfile
from pathlib import Path

from ecdat.phase5_git import GitInspector


class Phase5GitTests(unittest.TestCase):
    def test_invalid_repository_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                GitInspector().metadata(str(Path(directory)))


if __name__ == "__main__":
    unittest.main()
