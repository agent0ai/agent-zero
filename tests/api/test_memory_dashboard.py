"""Tests for python/api/memory_dashboard.py — Memory Dashboard API."""

import sys
import os
import threading
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.memory_dashboard import MemoryDashboard


def _make_dashboard() -> MemoryDashboard:
    return MemoryDashboard(app=MagicMock(), thread_lock=threading.Lock())


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
            "python.api.memory_dashboard.CogneeBackgroundWorker",
            create=True,
        ) as MockClass:
            MockClass.get_instance.return_value = mock_worker
            # Need to patch the actual import path
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
        from langchain_core.documents import Document
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
             patch("python.api.memory_dashboard.Memory") as MockMem, \
             patch("python.helpers.cognee_init.configure_cognee"):
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
    """Verify that ensure_cognee_setup() is called before any Cognee DB operation.
    This is the exact bug that hit production: list_datasets() failed because
    cognee.setup() was never called to create the SQLite tables."""

    @pytest.mark.asyncio
    async def test_process_calls_ensure_setup_before_action(self):
        """The top-level process() must call ensure_cognee_setup() before dispatching."""
        dashboard = _make_dashboard()
        call_order = []

        async def mock_setup():
            call_order.append("ensure_cognee_setup")

        with patch("python.api.memory_dashboard.ensure_cognee_setup", side_effect=mock_setup) as mock_ecs, \
             patch("python.api.memory_dashboard.get_existing_memory_subdirs", return_value=["default"]):
            result = await dashboard.process({"action": "get_memory_subdirs"}, MagicMock())

        mock_ecs.assert_called_once()
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_search_memories_works_after_setup(self):
        """Full flow: setup → list_datasets → return memories.
        This test would have caught the production DatabaseNotCreatedError."""
        dashboard = _make_dashboard()

        mock_cognee = MagicMock()
        mock_cognee.datasets.list_datasets = AsyncMock(return_value=[])

        with patch("python.api.memory_dashboard.ensure_cognee_setup", new_callable=AsyncMock), \
             patch.dict("sys.modules", {"cognee": mock_cognee}), \
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

        with patch("python.api.memory_dashboard.ensure_cognee_setup", new_callable=AsyncMock), \
             patch.dict("sys.modules", {"cognee": mock_cognee}), \
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
        dashboard = _make_dashboard()
        mock_cognee = MagicMock()
        mock_cognee.visualize_graph = AsyncMock(return_value="<html></html>")

        with patch("python.api.memory_dashboard.ensure_cognee_setup", new_callable=AsyncMock) as mock_setup, \
             patch.dict("sys.modules", {"cognee": mock_cognee}):
            result = await dashboard.process({"action": "knowledge_graph"}, MagicMock())

        mock_setup.assert_called_once()
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
