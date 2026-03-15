"""Tests for python/tools/memory_save.py — MemorySave tool."""

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
    agent.read_prompt = MagicMock(side_effect=lambda t, **kw: f"Saved: {kw.get('memory_id', '')}")
    return agent


@pytest.fixture
def tool(mock_agent):
    from python.tools.memory_save import MemorySave
    return MemorySave(
        agent=mock_agent,
        name="memory_save",
        method=None,
        args={"text": "Remember this", "area": "main"},
        message="",
        loop_data=None,
    )


class TestMemorySaveExecute:
    @pytest.mark.asyncio
    async def test_save_returns_response_with_id(self, tool):
        mock_db = MagicMock()
        mock_db.insert_text = AsyncMock(return_value="mem-123")
        with patch("python.tools.memory_save.Memory.get", new_callable=AsyncMock, return_value=mock_db):
            resp = await tool.execute(text="Important info", area="main")
        assert "mem-123" in resp.message or "Saved" in resp.message
        assert resp.break_loop is False

    @pytest.mark.asyncio
    async def test_default_area_is_main(self, tool):
        mock_db = MagicMock()
        mock_db.insert_text = AsyncMock(return_value="id-1")
        with patch("python.tools.memory_save.Memory.get", new_callable=AsyncMock, return_value=mock_db):
            resp = await tool.execute(text="Data", area="")
        mock_db.insert_text.assert_called_once()
        call_kw = mock_db.insert_text.call_args[1]
        assert call_kw.get("metadata", {}).get("area") == "main"
