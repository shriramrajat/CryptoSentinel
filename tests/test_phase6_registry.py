"""Phase 6: Discovery registry includes hardware and cloud."""
from ecdat.discovery.registry import DiscoveryRegistry
import pytest

def test_hardware_source_registered():
    assert "hardware" in DiscoveryRegistry.SOURCES

def test_cloud_source_registered():
    assert "cloud" in DiscoveryRegistry.SOURCES

def test_unsupported_source_raises():
    reg = DiscoveryRegistry()
    with pytest.raises(ValueError, match="Unsupported"):
        reg.scan("unknown_source", "/tmp/nonexistent")

def test_all_five_phase5_sources_still_registered():
    for src in ("binary", "container", "dependency", "protocol"):
        assert src in DiscoveryRegistry.SOURCES
