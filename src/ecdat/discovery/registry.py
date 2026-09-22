"""Registry/facade for composing advanced discovery adapters."""

from pathlib import Path
from typing import Any

from .base import AdvancedDiscoveryResult, DiscoveryError
from .binary import BinaryScanner
from .container import ContainerScanner
from .dependency import DependencyScanner
from .protocol import ProtocolScanner


class DiscoveryRegistry:
    def __init__(self) -> None:
        self.adapters = {"binary": BinaryScanner(), "container": ContainerScanner(), "dependency": DependencyScanner(), "protocol": ProtocolScanner()}

    def scan(self, source_type: str, path: str) -> AdvancedDiscoveryResult:
        try:
            adapter = self.adapters[source_type.lower()]
        except KeyError as exc:
            raise DiscoveryError(f"Unsupported discovery source: {source_type}") from exc
        return adapter.scan(path)

    def register(self, source_type: str, adapter: Any) -> None:
        if not callable(getattr(adapter, "scan", None)):
            raise TypeError("Discovery adapter must provide scan(path)")
        self.adapters[source_type.lower()] = adapter
