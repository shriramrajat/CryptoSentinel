import sys
from pathlib import Path
import pytest

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ecdat.scanner import Scanner
from ecdat.detectors.certificates import scan_certificate_file

def test_certificate_parser_invalid_data():
    sample_path = Path("fake_path.pem")
    assets = scan_certificate_file(sample_path, "invalid pem data")
    assert assets == []

def test_certificate_parser_with_sample_pem():
    sample_pem = Path(__file__).resolve().parent / "fixtures" / "sample_keys.pem"
    if sample_pem.exists():
        scanner = Scanner(root_dir=sample_pem.parent)
        assets = scanner.scan_file(sample_pem)
        assert len(assets) > 0
        for asset in assets:
            assert asset.category in {"certificate_or_key", "asymmetric_encryption"}
