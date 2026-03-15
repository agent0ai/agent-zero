"""Tests for python/tools/search_engine.py — SearchEngine tool."""

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
    agent.handle_intervention = AsyncMock()
    return agent


@pytest.fixture
def tool(mock_agent):
    from python.tools.search_engine import SearchEngine
    return SearchEngine(
        agent=mock_agent,
        name="search_engine",
        method=None,
        args={"query": "test query"},
        message="",
        loop_data=None,
    )


class TestSearchEngineExecute:
    @pytest.mark.asyncio
    async def test_returns_formatted_results(self, tool):
        mock_results = {
            "results": [
                {"title": "Result 1", "url": "https://example.com/1", "content": "Content 1"},
                {"title": "Result 2", "url": "https://example.com/2", "content": "Content 2"},
            ]
        }
        with patch("python.tools.search_engine.searxng", new_callable=AsyncMock, return_value=mock_results):
            resp = await tool.execute(query="test")
        assert "Result 1" in resp.message
        assert "https://example.com/1" in resp.message
        assert resp.break_loop is False

    @pytest.mark.asyncio
    async def test_handles_search_exception(self, tool):
        with patch("python.tools.search_engine.searxng", new_callable=AsyncMock, side_effect=Exception("Search failed")):
            resp = await tool.execute(query="test")
        assert "failed" in resp.message.lower()
