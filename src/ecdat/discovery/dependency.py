"""Dependency manifest intelligence with conservative usage semantics."""

import json
import re
import tomllib
from pathlib import Path
from typing import Any, Dict, List

from .base import AdvancedDiscoveryResult, DiscoveryError, DiscoveryFinding, validate_file


CRYPTO_NAMES = {"cryptography", "pycryptodome", "openssl", "libressl", "boringssl", "libsodium", "bcrypt", "jsonwebtoken", "jose", "bouncycastle", "org.bouncycastle", "golang.org/x/crypto", "ring", "rustls"}


class DependencyScanner:
    MAX_FILE_SIZE = 8 * 1024 * 1024

    def scan(self, path: str) -> AdvancedDiscoveryResult:
        manifest = validate_file(path, self.MAX_FILE_SIZE)
        result = AdvancedDiscoveryResult("dependency", manifest.as_posix())
        try:
            dependencies = self._parse(manifest)
        except (OSError, UnicodeDecodeError, ValueError, tomllib.TOMLDecodeError, json.JSONDecodeError) as exc:
            raise DiscoveryError(f"Malformed dependency manifest: {exc}") from exc
        for name, version in dependencies:
            crypto = self._is_crypto(name)
            entry = {"name": name, "version": version, "capability": "cryptographic" if crypto else "unknown", "evidence": "DEPENDENCY_PRESENT", "transitive": manifest.name.endswith(("lock", ".lock"))}
            result.dependencies.append(entry)
            result.add_finding(DiscoveryFinding("dependency", manifest.as_posix(), name, f"{name} {version}".strip(), 0.95, "manifest_parser", "dependency-present", metadata=entry, identity_inputs=[name, version]))
        return result

    def _parse(self, path: Path) -> List[tuple[str, str]]:
        name = path.name.lower()
        text = path.read_text(encoding="utf-8")
        if name == "package.json":
            obj = json.loads(text); sections = [obj.get("dependencies", {}), obj.get("devDependencies", {})]
            return [(key, str(value)) for section in sections for key, value in section.items()]
        if name in {"pyproject.toml", "cargo.toml"}:
            obj = tomllib.loads(text); sections = [obj.get("project", {}).get("dependencies", []), obj.get("tool", {}).get("poetry", {}).get("dependencies", {}), obj.get("dependencies", {})]
            values = []
            for section in sections:
                values.extend([(item, "") if isinstance(item, str) else (item, str(version)) for item, version in section.items()] if isinstance(section, dict) else [(re.split(r"[<>=!~ ]", item, 1)[0], "") for item in section])
            return values
        if name == "go.mod":
            return [(match.group(1), match.group(2)) for match in re.finditer(r"^\s*([\w./-]+)\s+(v[^\s]+)", text, re.MULTILINE)]
        if name == "pom.xml":
            return [(a, b) for a, b in re.findall(r"<artifactId>\s*([^<]+).*?<version>\s*([^<]+)", text, re.DOTALL)]
        if name in {"requirements.txt", "go.sum", "cargo.lock", "poetry.lock", "composer.lock", "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "packages.config"}:
            return [(re.split(r"[<>=!~ @]", line.strip(), maxsplit=1)[0], "") for line in text.splitlines() if line.strip() and not line.lstrip().startswith(("#", "//", "-"))]
        raise DiscoveryError(f"Unsupported dependency manifest: {path.name}")

    @staticmethod
    def _is_crypto(name: str) -> bool:
        normalized = name.lower()
        return normalized in CRYPTO_NAMES or any(token in normalized for token in ("crypto", "ssl", "tls", "bcrypt", "jwt", "jose"))
