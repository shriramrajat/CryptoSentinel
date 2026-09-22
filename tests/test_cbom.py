import sys
from pathlib import Path
import pytest

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ecdat.service import ScanService
from ecdat.cbom.generator import generate_cbom

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

def test_cbom_generation_service():
    service = ScanService()
    result = service.run_scan(str(FIXTURES_DIR), generate_cbom=True)

    assert "cbom" in result
    cbom = result["cbom"]
    assert cbom["bomFormat"] == "CycloneDX"
    assert cbom["specVersion"] == "1.6"
    assert "components" in cbom
    assert isinstance(cbom["components"], list)

def test_cbom_generator_empty():
    cbom = generate_cbom([])
    assert cbom["bomFormat"] == "CycloneDX"
    assert cbom["specVersion"] == "1.6"
    assert cbom["components"] == []
