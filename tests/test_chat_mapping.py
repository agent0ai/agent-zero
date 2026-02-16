"""
Tests for plugins/comms_core/helpers/chat_mapping.py

Covers get/set/remove, timestamp preservation, JSON persistence roundtrip,
graceful handling of missing/corrupt files, and thread safety.
"""

import json
import sys
import threading
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from plugins.comms_core.helpers.chat_mapping import ChatMapping, ChatMapEntry


@pytest.fixture
def mapping(monkeypatch, tmp_path):
    """Return a ChatMapping with its file path redirected to tmp_path."""
    monkeypatch.setattr(
        "plugins.comms_core.helpers.chat_mapping.files.get_abs_path",
        lambda rel: str(tmp_path / rel),
    )
    return ChatMapping("test_platform")


# ---------------------------------------------------------------------------
# Basic get / set / remove
# ---------------------------------------------------------------------------

class TestBasicOperations:
    def test_get_missing_returns_none(self, mapping):
        assert mapping.get_context_id("no-such-chat") is None

    def test_set_and_get(self, mapping):
        mapping.set("chat1", "ctx-abc", "user1")
        assert mapping.get_context_id("chat1") == "ctx-abc"

    def test_remove(self, mapping):
        mapping.set("chat1", "ctx-abc")
        mapping.remove("chat1")
        assert mapping.get_context_id("chat1") is None

    def test_remove_missing_no_error(self, mapping):
        mapping.remove("nonexistent")  # should not raise

    def test_len(self, mapping):
        assert len(mapping) == 0
        mapping.set("c1", "x1")
        mapping.set("c2", "x2")
        assert len(mapping) == 2


# ---------------------------------------------------------------------------
# Timestamp behaviour
# ---------------------------------------------------------------------------

class TestTimestamps:
    def test_created_at_set_on_first_insert(self, mapping):
        mapping.set("chat1", "ctx1")
        entry = mapping._map["chat1"]
        assert entry.created_at != ""
        assert entry.last_active != ""

    def test_created_at_preserved_on_update(self, mapping):
        mapping.set("chat1", "ctx1")
        original_created = mapping._map["chat1"].created_at

        mapping.set("chat1", "ctx2")
        assert mapping._map["chat1"].created_at == original_created
        assert mapping.get_context_id("chat1") == "ctx2"

    def test_last_active_updated_on_set(self, mapping):
        mapping.set("chat1", "ctx1")
        first_active = mapping._map["chat1"].last_active

        # Force a small time gap
        import time
        time.sleep(0.01)

        mapping.set("chat1", "ctx1")
        assert mapping._map["chat1"].last_active >= first_active

    def test_platform_user_id_preserved_on_update(self, mapping):
        mapping.set("chat1", "ctx1", "user_original")
        mapping.set("chat1", "ctx2")  # no user_id provided
        assert mapping._map["chat1"].platform_user_id == "user_original"


# ---------------------------------------------------------------------------
# JSON persistence roundtrip
# ---------------------------------------------------------------------------

class TestPersistence:
    @pytest.mark.asyncio
    async def test_save_load_roundtrip(self, mapping):
        mapping.set("chat1", "ctx-abc", "user1")
        mapping.set("chat2", "ctx-def", "user2")

        await mapping.save()

        # Create fresh mapping pointing at same file
        fresh = ChatMapping.__new__(ChatMapping)
        fresh._platform = mapping._platform
        fresh._lock = threading.RLock()
        fresh._map = {}
        fresh._path = mapping._path

        await fresh.load()

        assert fresh.get_context_id("chat1") == "ctx-abc"
        assert fresh.get_context_id("chat2") == "ctx-def"
        assert fresh._map["chat1"].platform_user_id == "user1"

    @pytest.mark.asyncio
    async def test_load_missing_file(self, mapping):
        """Loading when no file exists should leave mapping empty, not crash."""
        await mapping.load()
        assert len(mapping) == 0

    @pytest.mark.asyncio
    async def test_load_corrupt_json(self, mapping):
        """Loading corrupt JSON should be handled gracefully."""
        mapping._path.parent.mkdir(parents=True, exist_ok=True)
        mapping._path.write_text("NOT VALID JSON {{{", encoding="utf-8")
        await mapping.load()
        assert len(mapping) == 0

    @pytest.mark.asyncio
    async def test_save_creates_parent_dirs(self, mapping, tmp_path):
        # Point to a deeply nested path that doesn't exist
        mapping._path = tmp_path / "a" / "b" / "c" / "chat_map.json"
        mapping.set("chat1", "ctx1")
        await mapping.save()
        assert mapping._path.exists()

    @pytest.mark.asyncio
    async def test_saved_json_structure(self, mapping):
        mapping.set("chat1", "ctx-abc", "user1")
        await mapping.save()
        raw = json.loads(mapping._path.read_text(encoding="utf-8"))
        assert "chat1" in raw
        entry = raw["chat1"]
        assert entry["context_id"] == "ctx-abc"
        assert entry["platform_user_id"] == "user1"
        assert "created_at" in entry
        assert "last_active" in entry


# ---------------------------------------------------------------------------
# Thread safety
# ---------------------------------------------------------------------------

class TestConcurrency:
    def test_concurrent_set_get(self, mapping):
        """Hammer set/get from multiple threads to check for data races."""
        errors: list[Exception] = []
        barrier = threading.Barrier(10)

        def worker(idx):
            try:
                barrier.wait(timeout=5)
                chat_id = f"chat-{idx}"
                ctx_id = f"ctx-{idx}"
                mapping.set(chat_id, ctx_id, f"user-{idx}")
                retrieved = mapping.get_context_id(chat_id)
                assert retrieved == ctx_id
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        assert errors == [], f"Thread errors: {errors}"
        assert len(mapping) == 10
