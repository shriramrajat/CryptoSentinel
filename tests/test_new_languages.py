import sys
from pathlib import Path
import pytest

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ecdat.scanner import Scanner

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

def test_scan_multilanguage_fixtures():
    scanner = Scanner(root_dir=FIXTURES_DIR)
    assets = scanner.scan(FIXTURES_DIR)

    languages_found = {asset.language for asset in assets}
    expected_languages = {"python", "java", "c", "pem", "javascript", "typescript", "go", "php", "csharp", "kotlin"}
    
    for lang in expected_languages:
        assert lang in languages_found, f"Expected language '{lang}' was not detected in scan results."

def test_javascript_typescript_rules():
    scanner = Scanner(root_dir=FIXTURES_DIR)
    js_file = FIXTURES_DIR / "sample_javascript.js"
    assets = scanner.scan_file(js_file)

    algs = {a.algorithm for a in assets}
    assert "MD5" in algs
    assert "SHA-256" in algs
    assert "AES-256-GCM" in algs or "AES" in algs

def test_go_rust_php_rules():
    scanner = Scanner(root_dir=FIXTURES_DIR)
    
    go_assets = scanner.scan_file(FIXTURES_DIR / "sample_go.go")
    assert any(a.algorithm == "RSA" for a in go_assets)

    php_assets = scanner.scan_file(FIXTURES_DIR / "sample_php.php")
    assert any(a.algorithm == "MD5" for a in php_assets)
