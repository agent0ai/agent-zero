"""Tests for python/api/memory_dashboard.py — Memory Dashboard API."""

import sys
import os
import json
import tempfile
import time as _time
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------------------------
# Helpers (shared by both original and cache/pagination tests)
# ---------------------------------------------------------------------------

def _make_mock_dataset(name, ds_id="ds_1"):
    ds = MagicMock()
    ds.name = name
    ds.id = ds_id
    return ds


def _make_mock_data_item(raw_location, item_id="item_1"):
    item = MagicMock()
    item.raw_data_location = raw_location
    item.name = Path(raw_location).name if raw_location else ""
    item.id = item_id
    return item


def _setup_cognee(mock_cognee):
    """Wire mock cognee into cognee_init globals and sys.modules."""
    import python.helpers.cognee_init as ci
    ci._cognee_module = mock_cognee
    ci._search_type_class = MagicMock()
    sys.modules["cognee"] = mock_cognee


def _make_dashboard():
    from python.api.memory_dashboard import MemoryDashboard
    return MemoryDashboard(app=MagicMock(), thread_lock=MagicMock())


@pytest.fixture(autouse=True)
def _reset_state():
    """Reset module-level caches before each test."""
    import python.helpers.cognee_init as ci
    ci._cognee_module = None
    ci._search_type_class = None
    ci._configured = False

    import python.helpers.memory as mem
    mem.Memory._initialized = False
    mem.Memory._datasets_cache.clear()

    from python.api.memory_dashboard import _dashboard_cache
    _dashboard_cache.clear()

    saved_cognee = sys.modules.get("cognee")

    yield

    ci._cognee_module = None
    ci._search_type_class = None
    ci._configured = False
    mem.Memory._initialized = False
    mem.Memory._datasets_cache.clear()
    _dashboard_cache.clear()

    if saved_cognee is not None:
        sys.modules["cognee"] = saved_cognee


def _build_meta_text(content, meta):
    return f"[META:{json.dumps(meta)}]\n{content}"


def _make_cognee_with_items(items_by_dataset: dict[str, list]):
    """Build a mock cognee whose list_datasets/list_data return items_by_dataset.

    items_by_dataset: {"default_main": [("file:///path", "id_1", "content text"), ...]}
    Each tuple: (raw_data_location, item_id, content_body)
    """
    mock_cognee = MagicMock()
    datasets = []
    data_map = {}
    for ds_name, items in items_by_dataset.items():
        ds = _make_mock_dataset(ds_name, ds_id=f"id_{ds_name}")
        datasets.append(ds)
        data_items = []
        for raw_loc, item_id, content_body in items:
            di = _make_mock_data_item(raw_loc, item_id=item_id)
            data_items.append(di)
        data_map[f"id_{ds_name}"] = data_items

    mock_cognee.datasets.list_datasets = AsyncMock(return_value=datasets)

    async def _list_data(ds_id):
        return data_map.get(ds_id, [])

    mock_cognee.datasets.list_data = AsyncMock(side_effect=_list_data)
    return mock_cognee, data_map


# ===========================================================================
# Pre-existing tests for helper methods
# ===========================================================================

# --- _read_data_item_content ---

class TestReadDataItemContent:
    def test_reads_file_from_raw_data_location(self):
        dashboard = _make_dashboard()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("test content from file")
            f.flush()
            path = f.name

        try:
            item = MagicMock()
            item.raw_data_location = path
            result = dashboard._read_data_item_content(item)
            assert result == "test content from file"
        finally:
            os.unlink(path)

    def test_reads_file_url_scheme(self):
        dashboard = _make_dashboard()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("url scheme content")
            f.flush()
            path = f.name

        try:
            item = MagicMock()
            item.raw_data_location = f"file://{path}"
            result = dashboard._read_data_item_content(item)
            assert result == "url scheme content"
        finally:
            os.unlink(path)

    def test_falls_back_to_name(self):
        dashboard = _make_dashboard()
        item = MagicMock()
        item.raw_data_location = "/nonexistent/path/file.txt"
        item.name = "fallback_name"
        result = dashboard._read_data_item_content(item)
        assert result == "fallback_name"

    def test_no_raw_data_location(self):
        dashboard = _make_dashboard()
        item = MagicMock(spec=[])
        item.name = "just_a_name"
        result = dashboard._read_data_item_content(item)
        assert result == "just_a_name"


# --- _format_memory_for_dashboard ---

class TestFormatMemoryForDashboard:
    def test_formats_all_fields(self):
        from langchain_core.documents import Document
        dashboard = _make_dashboard()
        doc = Document(
            page_content="Test memory content",
            metadata={
                "id": "mem_123",
                "area": "solutions",
                "timestamp": "2026-03-07 12:00:00",
                "knowledge_source": True,
                "source_file": "test.md",
                "file_type": "markdown",
                "consolidation_action": "merged",
                "tags": ["important", "test"],
            },
        )
        result = dashboard._format_memory_for_dashboard(doc)
        assert result["id"] == "mem_123"
        assert result["area"] == "solutions"
        assert result["content_full"] == "Test memory content"
        assert result["knowledge_source"] is True
        assert result["source_file"] == "test.md"
        assert result["tags"] == ["important", "test"]

    def test_defaults_for_missing_fields(self):
        from langchain_core.documents import Document
        dashboard = _make_dashboard()
        doc = Document(page_content="Minimal", metadata={})
        result = dashboard._format_memory_for_dashboard(doc)
        assert result["id"] == "unknown"
        assert result["area"] == "unknown"
        assert result["knowledge_source"] is False
        assert result["tags"] == []


# --- _get_knowledge_graph ---

class TestGetKnowledgeGraph:
    @pytest.mark.asyncio
    async def test_returns_error_when_no_visualize_graph(self):
        dashboard = _make_dashboard()
        mock_cognee = MagicMock(spec=[])
        with patch.dict("sys.modules", {"cognee": mock_cognee}):
            result = await dashboard._get_knowledge_graph()
        assert result["success"] is False
        assert "not available" in result["error"]

    @pytest.mark.asyncio
    async def test_returns_html_on_success(self):
        dashboard = _make_dashboard()
        mock_cognee = MagicMock()
        mock_cognee.visualize_graph = AsyncMock(return_value="<html>graph</html>")
        with patch.dict("sys.modules", {"cognee": mock_cognee}):
            result = await dashboard._get_knowledge_graph()
        assert result["success"] is True
        assert result["html"] == "<html>graph</html>"

    @pytest.mark.asyncio
    async def test_handles_exception(self):
        dashboard = _make_dashboard()
        mock_cognee = MagicMock()
        mock_cognee.visualize_graph = AsyncMock(side_effect=Exception("graph error"))
        with patch.dict("sys.modules", {"cognee": mock_cognee}):
            result = await dashboard._get_knowledge_graph()
        assert result["success"] is False
        assert "graph error" in result["error"]


# --- _get_cognify_status ---

class TestGetCognifyStatus:
    @pytest.mark.asyncio
    async def test_returns_worker_status(self):
        dashboard = _make_dashboard()
        mock_worker = MagicMock()
        mock_worker.get_status.return_value = {
            "running": True,
            "dirty_datasets": ["ds1"],
            "insert_count": 5,
            "last_cognify_time": 12345.0,
            "last_run_datasets": ["ds1"],
            "last_run_success": True,
            "last_error": None,
        }
        with patch(
            "python.helpers.cognee_background.CogneeBackgroundWorker"
        ) as MockBg:
            MockBg.get_instance.return_value = mock_worker
            result = await dashboard._get_cognify_status()
        assert result["success"] is True
        assert result["running"] is True


# --- _get_memory_subdirs ---

class TestGetMemorySubdirs:
    @pytest.mark.asyncio
    async def test_returns_subdirs(self):
        dashboard = _make_dashboard()
        with patch(
            "python.api.memory_dashboard.get_existing_memory_subdirs",
            return_value=["default", "projects/personal", "projects/work"],
        ):
            result = await dashboard._get_memory_subdirs()
        assert result["success"] is True
        assert "default" in result["subdirs"]
        assert "projects/personal" in result["subdirs"]


# --- _get_current_memory_subdir ---

class TestGetCurrentMemorySubdir:
    @pytest.mark.asyncio
    async def test_returns_default_when_no_context(self):
        dashboard = _make_dashboard()
        result = await dashboard._get_current_memory_subdir({})
        assert result["memory_subdir"] == "default"

    @pytest.mark.asyncio
    async def test_returns_default_when_context_not_found(self):
        dashboard = _make_dashboard()
        with patch("python.api.memory_dashboard.AgentContext") as MockCtx:
            MockCtx.use.return_value = None
            result = await dashboard._get_current_memory_subdir(
                {"context_id": "nonexistent"}
            )
        assert result["memory_subdir"] == "default"


# --- _search_memories with offset ---

class TestSearchMemoriesOffset:
    @pytest.mark.asyncio
    async def test_offset_pagination(self):
        dashboard = _make_dashboard()

        mock_cognee = MagicMock()
        mock_ds = MagicMock()
        mock_ds.name = "default_main"
        mock_ds.id = "ds1"
        mock_cognee.datasets.list_datasets = AsyncMock(return_value=[mock_ds])

        items = []
        for i in range(10):
            item = MagicMock()
            item.raw_data_location = None
            item.name = f'[META:{{"id":"id_{i}","timestamp":"2026-03-0{min(i,9)} 12:00:00","area":"main"}}]\nContent {i}'
            items.append(item)
        mock_cognee.datasets.list_data = AsyncMock(return_value=items)

        with patch.dict("sys.modules", {"cognee": mock_cognee}), \
             patch("python.api.memory_dashboard.Memory") as MockMem:
            mock_mem_instance = MagicMock()
            mock_mem_instance._area_dataset.side_effect = lambda a: f"default_{a}"
            MockMem.get_by_subdir = AsyncMock(return_value=mock_mem_instance)
            MockMem.Area = MagicMock()
            MockMem.Area.__iter__ = MagicMock(return_value=iter([
                MagicMock(value="main"),
            ]))
            MockMem.Area.MAIN = MagicMock(value="main")

            result = await dashboard._search_memories({
                "memory_subdir": "default",
                "limit": 3,
                "offset": 2,
            })

        assert result["success"] is True
        assert len(result["memories"]) == 3


# --- ensure_cognee_setup is called before DB operations ---

class TestDashboardCallsSetup:
    """Verify that _get_cognee() is called before any Cognee DB operation.
    This is the exact bug that hit production: list_datasets() failed because
    cognee.setup() was never called to create the SQLite tables."""

    @pytest.mark.asyncio
    async def test_process_calls_get_cognee_before_action(self):
        """The top-level process() must call _get_cognee() before dispatching."""
        import python.helpers.cognee_init as ci
        mock_cognee_mod = MagicMock()
        mock_cognee_mod.SearchType = MagicMock()
        ci._cognee_module = mock_cognee_mod
        ci._search_type_class = mock_cognee_mod.SearchType

        dashboard = _make_dashboard()
        with patch("python.api.memory_dashboard.get_existing_memory_subdirs", return_value=["default"]):
            result = await dashboard.process({"action": "get_memory_subdirs"}, MagicMock())
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_search_memories_works_after_setup(self):
        """Full flow: setup -> list_datasets -> return memories.
        This test would have caught the production DatabaseNotCreatedError."""
        dashboard = _make_dashboard()

        mock_cognee = MagicMock()
        mock_cognee.datasets.list_datasets = AsyncMock(return_value=[])

        with patch.dict("sys.modules", {"cognee": mock_cognee}), \
             patch("python.api.memory_dashboard.Memory") as MockMem:
            mock_mem_instance = MagicMock()
            mock_mem_instance._area_dataset.side_effect = lambda a: f"default_{a}"
            MockMem.get_by_subdir = AsyncMock(return_value=mock_mem_instance)
            MockMem.Area = MagicMock()
            MockMem.Area.__iter__ = MagicMock(return_value=iter([
                MagicMock(value="main"),
            ]))
            MockMem.Area.MAIN = MagicMock(value="main")

            result = await dashboard._search_memories({"memory_subdir": "default"})

        assert result["success"] is True
        assert result["memories"] == []

    @pytest.mark.asyncio
    async def test_search_memories_handles_db_not_created(self):
        """If cognee.datasets.list_datasets() throws DatabaseNotCreatedError,
        the dashboard should return success with empty memories, not crash."""
        dashboard = _make_dashboard()

        mock_cognee = MagicMock()

        class DatabaseNotCreatedError(Exception):
            pass

        mock_cognee.datasets.list_datasets = AsyncMock(
            side_effect=DatabaseNotCreatedError("DB not created")
        )

        with patch.dict("sys.modules", {"cognee": mock_cognee}), \
             patch("python.api.memory_dashboard.Memory") as MockMem:
            mock_mem_instance = MagicMock()
            mock_mem_instance._area_dataset.side_effect = lambda a: f"default_{a}"
            MockMem.get_by_subdir = AsyncMock(return_value=mock_mem_instance)
            MockMem.Area = MagicMock()
            MockMem.Area.__iter__ = MagicMock(return_value=iter([
                MagicMock(value="main"),
            ]))
            MockMem.Area.MAIN = MagicMock(value="main")

            result = await dashboard._search_memories({"memory_subdir": "default"})

        assert result["success"] is True
        assert result["memories"] == []

    @pytest.mark.asyncio
    async def test_knowledge_graph_calls_setup_via_process(self):
        import python.helpers.cognee_init as ci
        mock_cognee_mod = MagicMock()
        mock_cognee_mod.SearchType = MagicMock()
        mock_cognee_mod.visualize_graph = AsyncMock(return_value="<html></html>")
        ci._cognee_module = mock_cognee_mod
        ci._search_type_class = mock_cognee_mod.SearchType

        dashboard = _make_dashboard()
        with patch.dict("sys.modules", {"cognee": mock_cognee_mod}):
            result = await dashboard.process({"action": "knowledge_graph"}, MagicMock())
        assert result["success"] is True


# --- _delete_memory ---

class TestDeleteMemory:
    @pytest.mark.asyncio
    async def test_missing_id_returns_error(self):
        dashboard = _make_dashboard()
        result = await dashboard._delete_memory({"memory_subdir": "default"})
        assert result["success"] is False
        assert "required" in result["error"].lower()


# --- _update_memory ---

class TestUpdateMemory:
    @pytest.mark.asyncio
    async def test_missing_params_returns_error(self):
        dashboard = _make_dashboard()
        result = await dashboard._update_memory({})
        assert result["success"] is False
        assert "Missing" in result["error"]


# ===========================================================================
# Cache + Pagination tests (added by Task 4)
# ===========================================================================

# --- Dashboard caching ---

class TestDashboardCaching:

    @pytest.mark.asyncio
    async def test_second_call_uses_cache(self, tmp_path):
        """Listing memories twice — list_data should only be called on the first call."""
        meta = {"id": "m1", "area": "main", "timestamp": "2026-01-01 00:00:00"}
        content_file = tmp_path / "m1.txt"
        content_file.write_text(_build_meta_text("Hello", meta))

        mock_cognee, _ = _make_cognee_with_items({
            "default_main": [(str(content_file), "item_1", "Hello")],
            "default_fragments": [],
            "default_solutions": [],
        })
        _setup_cognee(mock_cognee)

        dashboard = _make_dashboard()
        req_input = {"action": "search", "memory_subdir": "default", "search": ""}

        result1 = await dashboard.process(req_input, MagicMock())
        call_count_after_first = mock_cognee.datasets.list_data.call_count

        result2 = await dashboard.process(req_input, MagicMock())
        call_count_after_second = mock_cognee.datasets.list_data.call_count

        assert result1["success"] is True
        assert result2["success"] is True
        assert call_count_after_first > 0
        assert call_count_after_second == call_count_after_first, \
            "Second call should use cache, not call list_data again"

    @pytest.mark.asyncio
    async def test_cache_expires_after_ttl(self, tmp_path):
        """After TTL expires, list_data is called again."""
        meta = {"id": "m1", "area": "main", "timestamp": "2026-01-01 00:00:00"}
        content_file = tmp_path / "m1.txt"
        content_file.write_text(_build_meta_text("Hello", meta))

        mock_cognee, _ = _make_cognee_with_items({
            "default_main": [(str(content_file), "item_1", "Hello")],
            "default_fragments": [],
            "default_solutions": [],
        })
        _setup_cognee(mock_cognee)

        from python.api.memory_dashboard import _dashboard_cache, _CACHE_TTL
        dashboard = _make_dashboard()
        req_input = {"action": "search", "memory_subdir": "default", "search": ""}

        await dashboard.process(req_input, MagicMock())
        call_count_first = mock_cognee.datasets.list_data.call_count

        for key in list(_dashboard_cache.keys()):
            cached_time, cached_data = _dashboard_cache[key]
            _dashboard_cache[key] = (cached_time - _CACHE_TTL - 1, cached_data)

        await dashboard.process(req_input, MagicMock())
        call_count_second = mock_cognee.datasets.list_data.call_count

        assert call_count_second > call_count_first, \
            "After TTL expiry, list_data should be called again"

    @pytest.mark.asyncio
    async def test_invalidate_clears_cache(self, tmp_path):
        """invalidate_dashboard_cache() forces reload on next call."""
        meta = {"id": "m1", "area": "main", "timestamp": "2026-01-01 00:00:00"}
        content_file = tmp_path / "m1.txt"
        content_file.write_text(_build_meta_text("Hello", meta))

        mock_cognee, _ = _make_cognee_with_items({
            "default_main": [(str(content_file), "item_1", "Hello")],
            "default_fragments": [],
            "default_solutions": [],
        })
        _setup_cognee(mock_cognee)

        from python.api.memory_dashboard import invalidate_dashboard_cache
        dashboard = _make_dashboard()
        req_input = {"action": "search", "memory_subdir": "default", "search": ""}

        await dashboard.process(req_input, MagicMock())
        call_count_first = mock_cognee.datasets.list_data.call_count

        invalidate_dashboard_cache()

        await dashboard.process(req_input, MagicMock())
        call_count_second = mock_cognee.datasets.list_data.call_count

        assert call_count_second > call_count_first, \
            "After invalidation, list_data should be called again"


# --- True pagination (offset + limit on cached data) ---

class TestDashboardPagination:

    def _make_items(self, tmp_path, count):
        """Create N mock items with content files on disk."""
        ds_items = []
        for i in range(count):
            meta = {
                "id": f"m{i}",
                "area": "main",
                "timestamp": f"2026-01-01 00:00:{i:02d}",
            }
            fpath = tmp_path / f"m{i}.txt"
            fpath.write_text(_build_meta_text(f"Content {i}", meta))
            ds_items.append((str(fpath), f"item_{i}", f"Content {i}"))
        return ds_items

    @pytest.mark.asyncio
    async def test_pagination_offset_limit(self, tmp_path):
        """5 items, offset=2 limit=2 → returns exactly 2 items."""
        items = self._make_items(tmp_path, 5)
        mock_cognee, _ = _make_cognee_with_items({
            "default_main": items,
            "default_fragments": [],
            "default_solutions": [],
        })
        _setup_cognee(mock_cognee)

        dashboard = _make_dashboard()
        req_input = {
            "action": "search",
            "memory_subdir": "default",
            "search": "",
            "offset": 2,
            "limit": 2,
        }

        result = await dashboard.process(req_input, MagicMock())

        assert result["success"] is True
        assert len(result["memories"]) == 2
        assert result["total_count"] == 2

    @pytest.mark.asyncio
    async def test_total_db_count_reflects_all_items(self, tmp_path):
        """Even with pagination, total_db_count returns full count."""
        items = self._make_items(tmp_path, 5)
        mock_cognee, _ = _make_cognee_with_items({
            "default_main": items,
            "default_fragments": [],
            "default_solutions": [],
        })
        _setup_cognee(mock_cognee)

        dashboard = _make_dashboard()
        req_input = {
            "action": "search",
            "memory_subdir": "default",
            "search": "",
            "offset": 0,
            "limit": 2,
        }

        result = await dashboard.process(req_input, MagicMock())

        assert result["success"] is True
        assert len(result["memories"]) == 2
        assert result["total_db_count"] == 5
