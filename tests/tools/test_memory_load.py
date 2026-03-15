"""Tests for python/tools/memory_load.py — MemoryLoad tool."""

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
    agent.read_prompt = MagicMock(side_effect=lambda t, **kw: f"Not found: {kw.get('query', '')}")
    return agent


@pytest.fixture
def tool(mock_agent):
    from python.tools.memory_load import MemoryLoad
    return MemoryLoad(
        agent=mock_agent,
        name="memory_load",
        method=None,
        args={"query": "test"},
        message="",
        loop_data=None,
    )


class TestMemoryLoadExecute:
    @pytest.mark.asyncio
    async def test_no_results_returns_not_found_message(self, tool):
        mock_db = MagicMock()
        mock_db.search_similarity_threshold = AsyncMock(return_value=[])
        with patch("python.tools.memory_load.Memory.get", new_callable=AsyncMock, return_value=mock_db):
            resp = await tool.execute(query="nonexistent")
        assert "Not found" in resp.message or "not found" in resp.message.lower()
        assert resp.break_loop is False

    @pytest.mark.asyncio
    async def test_results_returned_as_text(self, tool):
        mock_docs = [{"content": "Doc 1", "metadata": {}}, {"content": "Doc 2", "metadata": {}}]
        mock_db = MagicMock()
        mock_db.search_similarity_threshold = AsyncMock(return_value=mock_docs)
        with patch("python.tools.memory_load.Memory.get", new_callable=AsyncMock, return_value=mock_db):
            with patch("python.tools.memory_load.Memory.format_docs_plain", return_value=["Doc 1", "Doc 2"]):
                resp = await tool.execute(query="test", threshold=0.7, limit=10)
        assert "Doc 1" in resp.message
        assert "Doc 2" in resp.message
