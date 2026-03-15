"""Tests for python/tools/memory_delete.py — MemoryDelete tool."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def mock_agent():
    agent = MagicMock()
    agent.read_prompt = MagicMock(side_effect=lambda t, **kw: f"Deleted: {kw.get('memory_count', 0)}")
    return agent


@pytest.fixture
def tool(mock_agent):
    from python.tools.memory_delete import MemoryDelete
    return MemoryDelete(
        agent=mock_agent,
        name="memory_delete",
        method=None,
        args={"ids": "id1,id2"},
        message="",
        loop_data=None,
    )


class TestMemoryDeleteExecute:
    @pytest.mark.asyncio
    async def test_delete_returns_count(self, tool):
        mock_db = MagicMock()
        mock_db.delete_documents_by_ids = AsyncMock(return_value=["id1", "id2"])
        with patch("python.tools.memory_delete.Memory.get", new_callable=AsyncMock, return_value=mock_db):
            resp = await tool.execute(ids="id1,id2")
        assert "2" in resp.message or "Deleted" in resp.message
        assert resp.break_loop is False

    @pytest.mark.asyncio
    async def test_empty_ids_deletes_nothing(self, tool):
        mock_db = MagicMock()
        mock_db.delete_documents_by_ids = AsyncMock(return_value=[])
        with patch("python.tools.memory_delete.Memory.get", new_callable=AsyncMock, return_value=mock_db):
            resp = await tool.execute(ids="")
        mock_db.delete_documents_by_ids.assert_called_with(ids=[])
