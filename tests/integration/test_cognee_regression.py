"""
Regression tests for the cognee database initialization bug.

Production bug: sqlite3.OperationalError and DatabaseNotCreatedError occurred when
cognee database wasn't initialized before use. The fix involved adding configure_cognee()
calls before database operations.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(autouse=True)
def _reset_module_state():
    """Reset module-level state before each test."""
    import python.helpers.memory as mem
    import python.helpers.cognee_init as ci
    mem._cognee = None
    mem._SearchType = None
    mem.Memory._initialized = False
    mem.Memory._datasets_cache.clear()
    ci._configured = False
    yield
    mem._cognee = None
    mem._SearchType = None
    mem.Memory._initialized = False
    mem.Memory._datasets_cache.clear()
    ci._configured = False


# --- configure_cognee called before Memory operations ---


@pytest.mark.regression
@pytest.mark.asyncio
async def test_memory_get_calls_configure_cognee_before_preload():
    """When cognee is not initialized, Memory.get() flow calls configure_cognee() before proceeding."""
    from python.helpers.memory import Memory

    configure_called = []

    def mock_configure():
        configure_called.append(True)

    mock_agent = MagicMock()
    mock_agent.config = MagicMock()
    mock_agent.config.knowledge_subdirs = ["default"]
    mock_agent.context = MagicMock()
    mock_agent.context.config = MagicMock()
    mock_agent.context.config.memory_subdir = "default"

    mock_cognee = MagicMock()
    mock_cognee.add = AsyncMock()
    mock_cognee.SearchType = MagicMock()
    mock_cognee.SearchType.CHUNKS = MagicMock()
    mock_cognee.SearchType.GRAPH_COMPLETION = MagicMock()

    with patch("python.helpers.memory.configure_cognee", side_effect=mock_configure), \
         patch("python.helpers.memory.get_agent_memory_subdir", return_value="default"), \
         patch("python.helpers.memory.get_knowledge_subdirs_by_memory_subdir", return_value=["default"]), \
         patch("python.helpers.memory.abs_knowledge_dir", return_value="/tmp/knowledge"), \
         patch("python.helpers.memory._state_dir", return_value="/tmp/test_state"), \
         patch("os.makedirs"), \
         patch("os.path.exists", return_value=False), \
         patch("builtins.open", MagicMock()), \
         patch("python.helpers.memory.knowledge_import") as mock_ki, \
         patch.dict("sys.modules", {"cognee": mock_cognee}):
        mock_ki.load_knowledge.return_value = {}
        mem = await Memory.get(mock_agent)

    assert len(configure_called) >= 1
    assert mem.dataset_name == "default"


@pytest.mark.regression
@pytest.mark.asyncio
async def test_search_similarity_threshold_calls_configure_cognee_first():
    """search_similarity_threshold calls configure_cognee() via _get_cognee() before cognee.search()."""
    from python.helpers.memory import Memory

    call_order = []

    def mock_configure():
        call_order.append("configure_cognee")

    mock_cognee = MagicMock()
    mock_cognee.search = AsyncMock(return_value=[])
    mock_cognee.SearchType = MagicMock()
    mock_cognee.SearchType.CHUNKS = MagicMock()
    mock_cognee.SearchType.GRAPH_COMPLETION = MagicMock()

    with patch("python.helpers.memory.configure_cognee", side_effect=mock_configure), \
         patch("python.helpers.memory.get_cognee_setting", side_effect=lambda k, d: d), \
         patch.dict("sys.modules", {"cognee": mock_cognee}):
        mem = Memory(dataset_name="default", memory_subdir="default")
        await mem.search_similarity_threshold("test query", limit=5, threshold=0.5)

    assert "configure_cognee" in call_order
    assert call_order.index("configure_cognee") < len(call_order)


@pytest.mark.regression
@pytest.mark.asyncio
async def test_insert_documents_calls_configure_cognee_first():
    """insert_documents calls configure_cognee() via _get_cognee() before cognee.add()."""
    from python.helpers.memory import Memory
    from langchain_core.documents import Document

    call_order = []

    def mock_configure():
        call_order.append("configure_cognee")

    mock_cognee = MagicMock()
    mock_cognee.add = AsyncMock(return_value=None)
    mock_cognee.SearchType = MagicMock()

    with patch("python.helpers.memory.configure_cognee", side_effect=mock_configure), \
         patch("python.helpers.cognee_background.CogneeBackgroundWorker") as mock_cbw, \
         patch.dict("sys.modules", {"cognee": mock_cognee}):
        mock_cbw.get_instance.return_value = MagicMock()
        mem = Memory(dataset_name="default", memory_subdir="default")
        await mem.insert_documents([Document(page_content="test", metadata={})])

    assert "configure_cognee" in call_order


# --- Database not created: proper error handling ---


@pytest.mark.regression
@pytest.mark.asyncio
async def test_search_handles_sqlite_operational_error():
    """When cognee database doesn't exist, search_similarity_threshold returns [] instead of crashing."""
    import sqlite3
    from python.helpers.memory import Memory

    mock_cognee = MagicMock()
    mock_cognee.search = AsyncMock(side_effect=sqlite3.OperationalError("no such table: datasets"))
    mock_cognee.SearchType = MagicMock()
    mock_cognee.SearchType.CHUNKS = MagicMock()
    mock_cognee.SearchType.GRAPH_COMPLETION = MagicMock()

    with patch("python.helpers.memory.configure_cognee"), \
         patch("python.helpers.memory.get_cognee_setting", side_effect=lambda k, d: d), \
         patch.dict("sys.modules", {"cognee": mock_cognee}):
        mem = Memory(dataset_name="default", memory_subdir="default")
        result = await mem.search_similarity_threshold("query", limit=5, threshold=0.5)

    assert result == []
    assert isinstance(result, list)


@pytest.mark.regression
@pytest.mark.asyncio
async def test_search_handles_database_not_created_error():
    """When cognee raises DatabaseNotCreatedError, search returns [] instead of unhandled crash."""

    class DatabaseNotCreatedError(Exception):
        pass

    from python.helpers.memory import Memory

    mock_cognee = MagicMock()
    mock_cognee.search = AsyncMock(side_effect=DatabaseNotCreatedError("DB not created"))
    mock_cognee.SearchType = MagicMock()
    mock_cognee.SearchType.CHUNKS = MagicMock()
    mock_cognee.SearchType.GRAPH_COMPLETION = MagicMock()

    with patch("python.helpers.memory.configure_cognee"), \
         patch("python.helpers.memory.get_cognee_setting", side_effect=lambda k, d: d), \
         patch.dict("sys.modules", {"cognee": mock_cognee}):
        mem = Memory(dataset_name="default", memory_subdir="default")
        result = await mem.search_similarity_threshold("query", limit=5, threshold=0.5)

    assert result == []


@pytest.mark.regression
@pytest.mark.asyncio
async def test_delete_data_by_id_handles_database_not_created():
    """_delete_data_by_id handles DatabaseNotCreatedError and returns False, no crash."""

    class DatabaseNotCreatedError(Exception):
        pass

    from python.helpers.memory import _delete_data_by_id

    mock_cognee = MagicMock()
    mock_cognee.datasets.list_datasets = AsyncMock(side_effect=DatabaseNotCreatedError("DB not created"))

    with patch("python.helpers.memory.configure_cognee"), \
         patch.dict("sys.modules", {"cognee": mock_cognee}):
        result = await _delete_data_by_id("default_main", "some_id")

    assert result is False


@pytest.mark.regression
@pytest.mark.asyncio
async def test_memory_dashboard_handles_db_error_gracefully():
    """MemoryDashboard returns success with empty memories when cognee DB operations fail."""

    class DatabaseNotCreatedError(Exception):
        pass

    from python.api.memory_dashboard import MemoryDashboard

    mock_cognee = MagicMock()
    mock_cognee.datasets.list_datasets = AsyncMock(side_effect=DatabaseNotCreatedError("DB not created"))

    with patch("python.helpers.cognee_init.configure_cognee"), \
         patch.dict("sys.modules", {"cognee": mock_cognee}), \
         patch("python.api.memory_dashboard.Memory") as MockMem:
        mock_mem_instance = MagicMock()
        mock_mem_instance._area_dataset.side_effect = lambda a: f"default_{a}"
        MockMem.get_by_subdir = AsyncMock(return_value=mock_mem_instance)
        MockMem.Area = MagicMock()
        MockMem.Area.__iter__ = MagicMock(return_value=iter([MagicMock(value="main")]))
        MockMem.Area.MAIN = MagicMock(value="main")

        dashboard = MemoryDashboard(app=MagicMock(), thread_lock=MagicMock())
        result = await dashboard._search_memories({"memory_subdir": "default"})

    assert result["success"] is True
    assert result["memories"] == []


# --- configure_cognee failure: user-friendly error ---


@pytest.mark.regression
@pytest.mark.asyncio
async def test_memory_dashboard_wraps_configure_cognee_failure():
    """When configure_cognee() fails, MemoryDashboard returns structured error, not raw crash."""

    from python.api.memory_dashboard import MemoryDashboard

    def failing_configure():
        raise RuntimeError("Cognee config failed: invalid API key")

    with patch("python.helpers.cognee_init.configure_cognee", side_effect=failing_configure):
        dashboard = MemoryDashboard(app=MagicMock(), thread_lock=MagicMock())
        result = await dashboard.process({"action": "get_memory_subdirs"}, MagicMock())

    assert result["success"] is False
    assert "error" in result
    assert "Cognee" in result["error"] or "config" in result["error"].lower() or "invalid" in result["error"].lower()


@pytest.mark.regression
@pytest.mark.asyncio
async def test_get_cognee_propagates_configure_failure():
    """When configure_cognee() raises, _get_cognee() propagates the error (caller must handle)."""

    from python.helpers.memory import _get_cognee

    def failing_configure():
        raise ValueError("Cognee setup failed")

    with patch("python.helpers.memory.configure_cognee", side_effect=failing_configure):
        with pytest.raises(ValueError, match="Cognee setup failed"):
            _get_cognee()
