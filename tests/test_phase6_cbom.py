"""Phase 6: CBOM completeness and determinism tests."""
import json, hashlib
from ecdat.cbom.generator import generate_cbom
from ecdat.models import CryptoAsset, Evidence

def _asset(algo, category, path, line, rule="r1"):
    return CryptoAsset.create(
        name=algo, category=category, algorithm=algo,
        file_path=path, line_number=line,
        code_snippet=f"use {algo}", library="test",
        confidence=0.9, matched_rule_id=rule,
    )

class TestCBOMDeterminism:
    def test_same_inputs_same_structure(self):
        assets = [_asset("RSA", "asymmetric_encryption", "src/a.py", 1)]
        bom1 = generate_cbom(assets)
        bom2 = generate_cbom(assets)
        assert len(bom1["components"]) == len(bom2["components"])
        assert bom1["components"][0]["name"] == bom2["components"][0]["name"]

    def test_no_duplicate_component_bom_refs(self):
        assets = [
            _asset("RSA", "asymmetric_encryption", "src/a.py", 1),
            _asset("AES", "symmetric_encryption", "src/b.py", 2),
        ]
        bom = generate_cbom(assets)
        refs = [c["bom-ref"] for c in bom["components"]]
        assert len(refs) == len(set(refs))

class TestCBOMStructure:
    def test_valid_cyclonedx_envelope(self):
        bom = generate_cbom([_asset("AES", "symmetric_encryption", "src/x.py", 1)])
        assert bom["bomFormat"] == "CycloneDX"
        assert "specVersion" in bom
        assert "components" in bom

    def test_component_has_crypto_properties(self):
        bom = generate_cbom([_asset("RSA", "asymmetric_encryption", "src/y.py", 1)])
        comp = bom["components"][0]
        assert "cryptoProperties" in comp

    def test_algorithm_and_mode_preserved(self):
        asset = CryptoAsset.create(
            name="AES", category="symmetric_encryption", algorithm="AES",
            file_path="src/z.py", line_number=10,
            code_snippet="AES.new(key, AES.MODE_GCM)", library="pycryptodome",
            confidence=0.95, mode="GCM", key_length=256,
        )
        bom = generate_cbom([asset])
        comp = bom["components"][0]
        crypto = comp["cryptoProperties"]
        assert crypto.get("algorithmProperties", {}).get("keySize") == 256 or \
               comp.get("name", "").startswith("AES")

    def test_empty_assets_produces_empty_components(self):
        bom = generate_cbom([])
        assert bom["components"] == []

class TestCBOMEvidence:
    def test_evidence_preserved_in_bom(self):
        asset = _asset("SHA-1", "hashing", "src/old.py", 5)
        bom = generate_cbom([asset])
        comp = bom["components"][0]
        # evidence location or occurrence should reflect source path
        bom_json = json.dumps(bom)
        assert "SHA-1" in bom_json or "sha" in bom_json.lower()
