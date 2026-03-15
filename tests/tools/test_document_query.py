"""Tests for python/tools/document_query.py — DocumentQueryTool."""

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
    return agent


@pytest.fixture
def tool(mock_agent):
    from python.tools.document_query import DocumentQueryTool
    t = DocumentQueryTool(
        agent=mock_agent,
        name="document_query",
        method=None,
        args={},
        message="",
        loop_data=None,
    )
    t.log = MagicMock(update=MagicMock())
    return t


class TestDocumentQueryToolExecute:
    @pytest.mark.asyncio
    async def test_no_document_returns_error(self, tool):
        resp = await tool.execute(document=None)
        assert "no document" in resp.message.lower()
        assert resp.break_loop is False

    @pytest.mark.asyncio
    async def test_empty_document_list_returns_error(self, tool):
        resp = await tool.execute(document=[])
        assert "no document" in resp.message.lower()

    @pytest.mark.asyncio
    async def test_single_document_no_queries_returns_content(self, tool):
        with patch("python.tools.document_query.DocumentQueryHelper") as MockHelper:
            mock_helper = MagicMock()
            mock_helper.document_get_content = AsyncMock(return_value="Document content here")
            MockHelper.return_value = mock_helper
            resp = await tool.execute(document="file:///doc.pdf")
        assert "Document content here" in resp.message
        assert resp.break_loop is False

    @pytest.mark.asyncio
    async def test_exception_returns_error_message(self, tool):
        with patch("python.tools.document_query.DocumentQueryHelper") as MockHelper:
            MockHelper.side_effect = Exception("Processing failed")
            resp = await tool.execute(document="file:///doc.pdf")
        assert "Error" in resp.message
        assert "Processing failed" in resp.message
