"""
CycloneDX v1.6 CBOM (Cryptography Bill of Materials) Generator.

Produces machine-readable CBOM JSON from normalized CryptoAsset objects.
The generator is a pure mapper — it contains no discovery logic.

Reference spec: CycloneDX 1.6 — cryptoProperties extension.
https://cyclonedx.org/docs/1.6/json/
"""

import json
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Iterable

from ecdat.models import CryptoAsset

# Version of the CBOM spec this generator targets
CYCLONEDX_SPEC_VERSION = "1.6"
CYCLONEDX_SCHEMA_VERSION = "1.6"
CBOM_COMPONENT_TYPE = "cryptographic-asset"

# ── Category → CycloneDX assetType mapping ────────────────────────────────────
_CATEGORY_TO_ASSET_TYPE: Dict[str, str] = {
    "symmetric_encryption": "algorithm",
    "asymmetric_encryption": "algorithm",
    "hashing": "algorithm",
    "digital_signature": "algorithm",
    "key_exchange": "algorithm",
    "mac": "algorithm",
    "key_derivation": "algorithm",
    "protocol": "protocol",
    "certificate_or_key": "certificate",  # refined below based on key_metadata
    "hardcoded_secret": "related-crypto-material",
}

# ── Algorithm → CycloneDX primitive mapping ────────────────────────────────────
_ALGORITHM_TO_PRIMITIVE: Dict[str, str] = {
    # Symmetric
    "AES": "ae",
    "DES": "block-cipher",
    "3DES": "block-cipher",
    "RC4": "stream-cipher",
    "CHACHA20": "stream-cipher",
    "ChaCha20": "stream-cipher",
    # Asymmetric
    "RSA": "pke",
    "ECC": "pke",
    "EC": "pke",
    "ECDSA": "signature",
    "ECDH": "ekm",
    "EdDSA": "signature",
    "Ed25519": "signature",
    "DSA": "signature",
    "DH": "ekm",
    # Hash
    "MD5": "hash",
    "SHA-1": "hash",
    "SHA-224": "hash",
    "SHA-256": "hash",
    "SHA-384": "hash",
    "SHA-512": "hash",
    "SHA-3": "hash",
    "BLAKE2": "hash",
    # MAC / KDF
    "HMAC": "mac",
    "PBKDF2": "kdf",
    "scrypt": "kdf",
    "Argon2": "kdf",
    "bcrypt": "kdf",
    # Protocol
    "TLS": "unknown",
    "SSL": "unknown",
    "JWT": "unknown",
    "SSH": "unknown",
    "IPsec": "unknown",
    # Secret
    "SECRET": "unknown",
    "Certificate": "unknown",
}

# ── Purpose → CycloneDX executionEnvironment/mode ─────────────────────────────
_PURPOSE_TO_MODE: Dict[str, str] = {
    "encryption": "encrypt",
    "decryption": "decrypt",
    "signing": "sign",
    "verification": "verify",
    "key_generation": "generate",
    "key_exchange": "keyAgreement",
    "key_derivation": "keyDerive",
    "hashing": "digest",
    "mac": "mac",
    "password_hashing": "keyDerive",
    "unknown": "unknown",
    "certificate_or_public_key": "unknown",
}


def generate_cbom(
    assets: Iterable[CryptoAsset],
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Generate a CycloneDX v1.6 CBOM dict from a list of CryptoAssets.
    This function contains no discovery logic — it is a pure mapper.

    Args:
        assets: Iterable of CryptoAsset objects from the scanner.
        metadata: Optional dict of additional metadata to include in the CBOM.

    Returns:
        A dict representing the CycloneDX CBOM JSON object.
    """
    asset_list = list(assets)
    now_utc = datetime.now(timezone.utc).isoformat()

    cbom: Dict[str, Any] = {
        "bomFormat": "CycloneDX",
        "specVersion": CYCLONEDX_SPEC_VERSION,
        "serialNumber": f"urn:uuid:{uuid.uuid4()}",
        "version": 1,
        "metadata": {
            "timestamp": now_utc,
            "tools": [
                {
                    "vendor": "CryptoSentinel / ECDAT",
                    "name": "CryptoSentinel",
                    "version": (metadata or {}).get("scanner_version", "0.2.0"),
                }
            ],
            "component": {
                "type": "application",
                "name": (metadata or {}).get("target", "scanned-target"),
                "bom-ref": "target-application",
            },
        },
        "components": [],
        "dependencies": [],
    }

    if metadata:
        cbom["metadata"]["properties"] = [
            {"name": k, "value": str(v)}
            for k, v in metadata.items()
            if k not in ("scanner_version", "target")
        ]

    for asset in asset_list:
        component = _asset_to_component(asset)
        cbom["components"].append(component)

    return cbom


def generate_cbom_json(
    assets: Iterable[CryptoAsset],
    metadata: Optional[Dict[str, Any]] = None,
    indent: int = 2,
) -> str:
    """
    Generate a CycloneDX v1.6 CBOM JSON string.
    """
    cbom = generate_cbom(assets, metadata=metadata)
    return json.dumps(cbom, indent=indent, default=str)


def _asset_to_component(asset: CryptoAsset) -> Dict[str, Any]:
    """Map a single CryptoAsset to a CycloneDX component dict."""
    category = asset.category.lower()
    algorithm = asset.algorithm

    # Determine CycloneDX asset type
    cdx_asset_type = _CATEGORY_TO_ASSET_TYPE.get(category, "algorithm")
    # Refine: if certificate_metadata is present → certificate; if key_metadata → related-crypto-material (key)
    if asset.certificate_metadata:
        cdx_asset_type = "certificate"
    elif asset.key_metadata and cdx_asset_type == "certificate":
        cdx_asset_type = "related-crypto-material"

    # Primitive
    primitive = _ALGORITHM_TO_PRIMITIVE.get(algorithm, "unknown")
    if primitive == "unknown" and category in ("digital_signature",):
        primitive = "signature"
    elif primitive == "unknown" and category in ("key_exchange",):
        primitive = "ekm"

    # Mode for crypto operations
    mode = _PURPOSE_TO_MODE.get(asset.purpose or "unknown", "unknown")

    # Build component
    component: Dict[str, Any] = {
        "type": CBOM_COMPONENT_TYPE,
        "bom-ref": asset.asset_id,
        "name": algorithm,
        "cryptoProperties": {
            "assetType": cdx_asset_type,
            "algorithmProperties": _build_algorithm_properties(asset, primitive, mode),
        },
        "evidence": _build_evidence(asset),
        "properties": _build_properties(asset),
    }

    # Add certificate properties if available
    if asset.certificate_metadata:
        component["cryptoProperties"]["certificateProperties"] = _build_cert_properties(asset.certificate_metadata)
        del component["cryptoProperties"]["algorithmProperties"]  # certificates don't use algorithmProperties

    # Add key properties if available
    if asset.key_metadata and asset.category == "certificate_or_key":
        component["cryptoProperties"]["relatedCryptoMaterialProperties"] = _build_key_properties(asset)

    return component


def _build_algorithm_properties(asset: CryptoAsset, primitive: str, mode: str) -> Dict[str, Any]:
    props: Dict[str, Any] = {
        "primitive": primitive,
        "executionEnvironment": "software",
        "implementationPlatform": _resolve_library_platform(asset.library),
        "certificationLevel": [],
        "mode": mode,
    }

    if asset.key_length:
        props["keySize"] = asset.key_length

    if asset.padding:
        props["padding"] = asset.padding

    if asset.mode:
        props["cryptoFunctions"] = [asset.mode]

    if asset.protocol:
        props["protocolProperties"] = {"type": asset.protocol}

    return props


def _build_cert_properties(cert_meta) -> Dict[str, Any]:
    props: Dict[str, Any] = {
        "subjectName": cert_meta.subject or "unknown",
        "issuerName": cert_meta.issuer or "unknown",
        "notValidBefore": cert_meta.not_before or "",
        "notValidAfter": cert_meta.not_after or "",
        "signatureAlgorithmRef": cert_meta.signature_algorithm or "unknown",
        "subjectPublicKeyRef": cert_meta.public_key_algorithm or "unknown",
    }
    if cert_meta.fingerprint_sha256:
        props["certificateExtensions"] = [
            {"oid": "sha256fingerprint", "value": cert_meta.fingerprint_sha256}
        ]
    if cert_meta.subject_alt_names:
        props["subjectAlternativeNames"] = cert_meta.subject_alt_names[:10]  # limit for readability
    return props


def _build_key_properties(asset: CryptoAsset) -> Dict[str, Any]:
    km = asset.key_metadata
    return {
        "type": "private-key" if km.key_type else "key",
        "id": asset.asset_id,
        "state": "pre-activation",
        "algorithmRef": km.key_type or asset.algorithm,
        "activationDate": "",
        "size": km.key_size,
        # Security invariant: raw private material is never stored
        "value": "not-stored",
    }


def _build_evidence(asset: CryptoAsset) -> Dict[str, Any]:
    ev = asset.evidence
    return {
        "occurrences": [
            {
                "location": asset.file_path,
                "line": asset.line_number,
                "additionalContext": ev.code_snippet[:200] if ev and ev.code_snippet else "",
            }
        ],
        "identity": [
            {
                "field": "name",
                "confidence": round(asset.confidence, 2),
                "methods": [
                    {
                        "technique": ev.detection_mechanism if ev else "unknown",
                        "confidence": round(asset.confidence, 2),
                        "value": ev.matched_rule_id if ev else "unknown",
                    }
                ],
            }
        ],
    }


def _build_properties(asset: CryptoAsset) -> List[Dict[str, str]]:
    props = [
        {"name": "ecdat:language", "value": asset.language},
        {"name": "ecdat:library", "value": asset.library},
        {"name": "ecdat:category", "value": asset.category},
        {"name": "ecdat:confidence", "value": str(round(asset.confidence, 2))},
        {"name": "ecdat:detection_rule", "value": asset.detection_rule or "unknown"},
    ]
    if asset.purpose:
        props.append({"name": "ecdat:purpose", "value": asset.purpose})
    if asset.protocol:
        props.append({"name": "ecdat:protocol", "value": asset.protocol})
    if asset.mode:
        props.append({"name": "ecdat:mode", "value": asset.mode})
    if asset.padding:
        props.append({"name": "ecdat:padding", "value": asset.padding})
    if asset.key_length:
        props.append({"name": "ecdat:key_length", "value": str(asset.key_length)})
    return props


def _resolve_library_platform(library: str) -> str:
    """Map a library name to a CycloneDX implementation platform identifier."""
    lib = library.lower()
    if lib in ("openssl", "libssl"):
        return "openssl"
    elif lib in ("cryptography", "pycryptodome", "pycrypto"):
        return "python"
    elif lib in ("javax.crypto", "java.security"):
        return "jca"
    elif lib in ("node:crypto", "webcrypto"):
        return "nodejs"
    elif lib in ("ring", "rustcrypto", "openssl", "rustcrypto/rsa"):
        return "rust"
    elif lib in ("crypto/rsa", "crypto/aes", "crypto/sha256", "crypto/tls"):
        return "golang"
    elif lib in ("system.security.cryptography",):
        return "dotnet"
    elif lib == "pem":
        return "pem"
    return "unknown"
