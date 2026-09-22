"""Discovery source registry — Phase 5 + Phase 6 sources."""
from __future__ import annotations
from typing import Any
from .base import AdvancedDiscoveryResult
from .binary import BinaryScanner
from .container import ContainerScanner
from .dependency import DependencyScanner
from .protocol import ProtocolScanner
from .hardware import HardwareScanner
from .cloud import CloudScanner

_SCANNERS: dict[str, Any] = {
    "binary": BinaryScanner(),
    "container": ContainerScanner(),
    "dependency": DependencyScanner(),
    "protocol": ProtocolScanner(),
    "hardware": HardwareScanner(),
    "cloud": CloudScanner(),
}

class DiscoveryRegistry:
    """Central registry for all discovery adapters."""
    SOURCES = set(_SCANNERS)

    def scan(self, source_type: str, path: str) -> AdvancedDiscoveryResult:
        scanner = _SCANNERS.get(source_type.lower())
        if not scanner:
            raise ValueError(f"Unsupported discovery source: {source_type!r}. Supported: {sorted(self.SOURCES)}")
        return scanner.scan(path)
