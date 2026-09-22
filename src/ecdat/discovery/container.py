"""OCI/Docker archive inspection without extraction or container execution."""

import tarfile
import zipfile
from collections import deque
from pathlib import Path
from typing import Iterable

from .base import AdvancedDiscoveryResult, DiscoveryError, DiscoveryFinding, validate_file


class ContainerScanner:
    MAX_ARCHIVE_SIZE = 512 * 1024 * 1024
    MAX_MEMBERS = 100_000
    MAX_MEMBER_SIZE = 64 * 1024 * 1024
    MAX_TOTAL_UNCOMPRESSED_SIZE = 512 * 1024 * 1024
    MAX_COMPRESSION_RATIO = 100
    MAX_DIRECTORIES = 10_000
    MAX_DEPTH = 32

    def scan(self, path: str) -> AdvancedDiscoveryResult:
        source = Path(path).resolve()
        if source.is_dir():
            return self._scan_directory(source)
        source = validate_file(str(source), self.MAX_ARCHIVE_SIZE)
        result = AdvancedDiscoveryResult("container", source.as_posix())
        try:
            if tarfile.is_tarfile(source):
                with tarfile.open(source, "r:*") as archive:
                    self._inspect_tar_members(archive, result)
            elif zipfile.is_zipfile(source):
                with zipfile.ZipFile(source) as archive:
                    self._inspect_zip_members(archive, result)
            else:
                result.errors.append("UNSUPPORTED_CONTAINER_FORMAT")
        except (tarfile.TarError, zipfile.BadZipFile, OSError) as exc:
            raise DiscoveryError(f"Malformed container archive: {exc}") from exc
        return result

    def _scan_directory(self, root: Path) -> AdvancedDiscoveryResult:
        result = AdvancedDiscoveryResult("container", root.as_posix())
        queue = deque([(root, 0)])
        files = directories = total_bytes = 0
        while queue and files < self.MAX_MEMBERS and directories < self.MAX_DIRECTORIES:
            directory, depth = queue.popleft()
            if depth > self.MAX_DEPTH:
                result.errors.append("RECURSION_LIMIT_EXCEEDED")
                continue
            try:
                children = list(directory.iterdir())
            except OSError:
                result.errors.append("DIRECTORY_READ_ERROR")
                continue
            for path in children:
                if path.is_symlink():
                    result.errors.append("SYMLINK_SKIPPED")
                    continue
                if path.is_dir():
                    directories += 1
                    queue.append((path, depth + 1))
                elif path.is_file():
                    files += 1
                    size = path.stat().st_size
                    total_bytes += size
                    if size > self.MAX_MEMBER_SIZE or total_bytes > self.MAX_TOTAL_UNCOMPRESSED_SIZE:
                        result.errors.append("MEMBER_SIZE_LIMIT_EXCEEDED")
                        continue
                    self._inspect_name(path.relative_to(root).as_posix(), result)
        if queue:
            result.errors.append("DIRECTORY_LIMIT_EXCEEDED")
        return result

    def _inspect_tar_members(self, archive: tarfile.TarFile, result: AdvancedDiscoveryResult) -> None:
        total_size = 0
        for index, member in enumerate(archive):
            if index >= self.MAX_MEMBERS:
                result.errors.append("MEMBER_LIMIT_EXCEEDED")
                return
            name = getattr(member, "filename", getattr(member, "name", ""))
            size = int(getattr(member, "file_size", getattr(member, "size", 0)))
            total_size += size
            if Path(name).is_absolute() or ".." in Path(name).parts:
                result.errors.append("ARCHIVE_PATH_TRAVERSAL")
                continue
            if size > self.MAX_MEMBER_SIZE or total_size > self.MAX_TOTAL_UNCOMPRESSED_SIZE:
                result.errors.append("MEMBER_SIZE_LIMIT_EXCEEDED")
                continue
            self._inspect_name(name, result)

    def _inspect_zip_members(self, archive: zipfile.ZipFile, result: AdvancedDiscoveryResult) -> None:
        total_size = 0
        for index, member in enumerate(archive.filelist):
            if index >= self.MAX_MEMBERS:
                result.errors.append("MEMBER_LIMIT_EXCEEDED")
                return
            name, size, compressed = member.filename, member.file_size, member.compress_size
            total_size += size
            if Path(name).is_absolute() or ".." in Path(name).parts:
                result.errors.append("ARCHIVE_PATH_TRAVERSAL")
                continue
            ratio = size / max(compressed, 1)
            if size > self.MAX_MEMBER_SIZE or total_size > self.MAX_TOTAL_UNCOMPRESSED_SIZE:
                result.errors.append("MEMBER_SIZE_LIMIT_EXCEEDED")
                continue
            if ratio > self.MAX_COMPRESSION_RATIO:
                result.errors.append("COMPRESSION_RATIO_EXCEEDED")
                continue
            self._inspect_name(name, result)

    def _inspect_name(self, name: str, result: AdvancedDiscoveryResult) -> None:
        lowered = name.lower()
        indicators = []
        if any(token in lowered for token in ("openssl", "libcrypto", "gnutls", "mbedtls", "wolfssl")):
            indicators.append(("crypto-library", 0.65))
        if lowered.endswith((".pem", ".crt", ".cer", ".key")):
            indicators.append(("certificate-or-key-file", 0.7))
        if any(token in lowered for token in ("dockerfile", "package.json", "requirements.txt", "pom.xml", "go.mod", "cargo.toml")):
            indicators.append(("manifest-or-config", 0.8))
        for indicator, confidence in indicators:
            result.add_finding(DiscoveryFinding("container", f"{result.source_location}!/{name}", indicator, name, confidence, "container_path", "container-path", metadata={"artifact": name}, identity_inputs=[name, indicator]))
