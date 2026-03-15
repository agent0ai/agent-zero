"""Tests for python/helpers/searxng.py."""

import sys
from pathlib import Path
from unittest.mock import patch, AsyncMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class TestSearxngSearch:
    @pytest.mark.asyncio
    async def test_search_calls_development_function(self):
        from python.helpers import searxng

        mock_result = {"results": [{"title": "Hit", "url": "https://example.com"}]}

        with patch("python.helpers.searxng.runtime") as mock_runtime:
            mock_runtime.call_development_function = AsyncMock(return_value=mock_result)

            result = await searxng.search("test query")

            assert result == mock_result
            mock_runtime.call_development_function.assert_called_once()
            call_args = mock_runtime.call_development_function.call_args
            assert call_args[1]["query"] == "test query"

    @pytest.mark.asyncio
    async def test_search_returns_json_from_post(self):
        from python.helpers import searxng

        expected = {"results": [], "query": "foo"}

        with patch("python.helpers.searxng.runtime") as mock_runtime:
            mock_runtime.call_development_function = AsyncMock(return_value=expected)

            result = await searxng.search("foo")

            assert result == expected
