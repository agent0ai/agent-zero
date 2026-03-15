"""Tests for python/tools/memory_forget.py — MemoryForget tool."""

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
    from python.tools.memory_forget import MemoryForget
    return MemoryForget(
        agent=mock_agent,
        name="memory_forget",
        method=None,
        args={"query": "old data"},
        message="",
        loop_data=None,
    )


class TestMemoryForgetExecute:
    @pytest.mark.asyncio
    async def test_forget_returns_count(self, tool):
        mock_db = MagicMock()
        mock_db.delete_documents_by_query = AsyncMock(return_value=["doc1"])
        with patch("python.tools.memory_forget.Memory.get", new_callable=AsyncMock, return_value=mock_db):
            resp = await tool.execute(query="forget this", threshold=0.7)
        assert "1" in resp.message or "Deleted" in resp.message
        assert resp.break_loop is False
