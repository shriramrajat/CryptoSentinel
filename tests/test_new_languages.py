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
    expected_languages = {
        "python", "java", "c", "pem", "javascript", "typescript",
        "go", "rust", "php", "csharp", "kotlin"
    }

    for lang in expected_languages:
        assert lang in languages_found, f"Expected language '{lang}' was not detected in scan results."


def test_javascript_typescript_rules():
    scanner = Scanner(root_dir=FIXTURES_DIR)
    js_file = FIXTURES_DIR / "sample_javascript.js"
    assert js_file.exists()
    assets = scanner.scan_file(js_file)

    algs = {a.algorithm for a in assets}
    assert "MD5" in algs
    assert "SHA-256" in algs
    assert "AES" in algs or "AES-256-GCM" in algs

    ts_file = FIXTURES_DIR / "sample_typescript.ts"
    assert ts_file.exists()
    ts_assets = scanner.scan_file(ts_file)
    assert any(a.language == "typescript" for a in ts_assets)


def test_go_rust_php_rules():
    scanner = Scanner(root_dir=FIXTURES_DIR)

    go_file = FIXTURES_DIR / "sample_go.go"
    assert go_file.exists()
    go_assets = scanner.scan_file(go_file)
    assert any(a.algorithm == "RSA" for a in go_assets)

    rust_file = FIXTURES_DIR / "sample_rust.rs"
    assert rust_file.exists()
    rust_assets = scanner.scan_file(rust_file)
    assert any(a.language == "rust" and a.algorithm in {"RSA", "AES", "MD5", "SHA-1", "SHA-256"} for a in rust_assets)

    php_file = FIXTURES_DIR / "sample_php.php"
    assert php_file.exists()
    php_assets = scanner.scan_file(php_file)
    assert any(a.algorithm == "MD5" for a in php_assets)


def test_csharp_kotlin_rules():
    scanner = Scanner(root_dir=FIXTURES_DIR)

    cs_file = FIXTURES_DIR / "sample_csharp.cs"
    assert cs_file.exists()
    cs_assets = scanner.scan_file(cs_file)
    assert any(a.language == "csharp" for a in cs_assets)

    kt_file = FIXTURES_DIR / "sample_kotlin.kt"
    assert kt_file.exists()
    kt_assets = scanner.scan_file(kt_file)
    assert any(a.language == "kotlin" for a in kt_assets)
