"""
Tests for plugins/comms_core/helpers/bridge_registry.py

Covers register/unregister/get/list, overwrite, thread safety, and snapshot isolation.
"""

import sys
import threading
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from plugins.comms_core.helpers import bridge_registry
from plugins.comms_core.helpers.bridge_base import BridgeConfig, CommunicationBridge, NormalisedAttachment


class StubBridge(CommunicationBridge):
    """Minimal concrete bridge for registry tests."""

    def __init__(self, name: str = "stub"):
        self._name = name
        super().__init__(BridgeConfig())

    @property
    def platform_name(self) -> str:
        return self._name

    async def start_transport(self): ...
    async def stop_transport(self): ...
    async def send_text(self, chat_id, text, reply_to=None): ...
    async def send_voice(self, chat_id, audio_bytes, reply_to=None): ...
    async def send_typing_indicator(self, chat_id, action="typing"): ...
    async def download_attachment(self, ref) -> NormalisedAttachment:
        return NormalisedAttachment("f", b"", "x")


@pytest.fixture(autouse=True)
def clean_registry(monkeypatch):
    """Ensure each test starts with a fresh, empty registry."""
    monkeypatch.setattr(bridge_registry, "_bridges", {})


class TestRegisterGet:
    def test_register_and_get(self):
        b = StubBridge("telegram")
        bridge_registry.register(b)
        assert bridge_registry.get_bridge("telegram") is b

    def test_get_missing_returns_none(self):
        assert bridge_registry.get_bridge("nonexistent") is None

    def test_list_platforms_empty(self):
        assert bridge_registry.list_platforms() == []

    def test_list_platforms_populated(self):
        bridge_registry.register(StubBridge("telegram"))
        bridge_registry.register(StubBridge("slack"))
        platforms = bridge_registry.list_platforms()
        assert sorted(platforms) == ["slack", "telegram"]


class TestUnregister:
    def test_unregister_existing(self):
        bridge_registry.register(StubBridge("telegram"))
        bridge_registry.unregister("telegram")
        assert bridge_registry.get_bridge("telegram") is None

    def test_unregister_missing_no_error(self):
        bridge_registry.unregister("does_not_exist")  # should not raise


class TestOverwrite:
    def test_overwrite_existing_platform(self):
        b1 = StubBridge("telegram")
        b2 = StubBridge("telegram")
        bridge_registry.register(b1)
        bridge_registry.register(b2)
        assert bridge_registry.get_bridge("telegram") is b2


class TestGetAll:
    def test_get_all_returns_copy(self):
        b = StubBridge("telegram")
        bridge_registry.register(b)
        snapshot = bridge_registry.get_all()
        assert snapshot == {"telegram": b}
        # Mutating the snapshot should not affect the registry
        snapshot["telegram"] = None
        assert bridge_registry.get_bridge("telegram") is b

    def test_get_all_empty(self):
        assert bridge_registry.get_all() == {}


class TestThreadSafety:
    def test_concurrent_register_unregister(self):
        """Hammer the registry from multiple threads to check for races."""
        errors: list[Exception] = []
        barrier = threading.Barrier(10)

        def worker(idx):
            try:
                barrier.wait(timeout=5)
                name = f"platform-{idx}"
                b = StubBridge(name)
                bridge_registry.register(b)
                # Verify our own entry exists
                assert bridge_registry.get_bridge(name) is b
                bridge_registry.unregister(name)
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        assert errors == [], f"Thread errors: {errors}"
        # All should be unregistered
        assert bridge_registry.list_platforms() == []
