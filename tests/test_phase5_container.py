import io
import tarfile
import tempfile
import unittest
from pathlib import Path

from ecdat.discovery.container import ContainerScanner


class Phase5ContainerTests(unittest.TestCase):
    def test_archive_traversal_is_reported_without_extraction(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "image.tar"
            with tarfile.open(path, "w") as archive:
                info = tarfile.TarInfo("../escape.pem"); info.size = 1
                archive.addfile(info, io.BytesIO(b"x"))
            result = ContainerScanner().scan(str(path))
            self.assertIn("ARCHIVE_PATH_TRAVERSAL", result.errors)


if __name__ == "__main__":
    unittest.main()
