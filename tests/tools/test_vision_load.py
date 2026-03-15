"""Tests for python/tools/vision_load.py — VisionLoad tool."""

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
    agent.context = MagicMock()
    agent.context.log = MagicMock()
    agent.context.log.log = MagicMock(return_value=MagicMock())
    agent.hist_add_message = MagicMock()
    agent.hist_add_tool_result = MagicMock()
    return agent


@pytest.fixture
def tool(mock_agent):
    from python.tools.vision_load import VisionLoad
    return VisionLoad(
        agent=mock_agent,
        name="vision_load",
        method=None,
        args={},
        message="",
        loop_data=None,
    )


class TestVisionLoadExecute:
    @pytest.mark.asyncio
    async def test_empty_paths_returns_dummy(self, tool):
        resp = await tool.execute(paths=[])
        assert resp.message == "dummy"
        assert resp.break_loop is False

    @pytest.mark.asyncio
    async def test_skips_nonexistent_paths(self, tool):
        with patch("python.tools.vision_load.runtime.call_development_function", new_callable=AsyncMock) as mock_exists:
            mock_exists.return_value = False
            resp = await tool.execute(paths=["/nonexistent/image.png"])
        assert tool.images_dict == {}
        assert resp.message == "dummy"
