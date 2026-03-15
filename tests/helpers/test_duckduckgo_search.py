"""Tests for python/helpers/duckduckgo_search.py."""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class TestDuckDuckGoSearch:
    def test_search_returns_list_of_strings(self):
        from python.helpers import duckduckgo_search

        mock_results = [
            {"title": "Result 1", "body": "Content 1"},
            {"title": "Result 2", "body": "Content 2"},
        ]

        with patch("python.helpers.duckduckgo_search.DDGS") as mock_ddgs_cls:
            mock_ddgs = MagicMock()
            mock_ddgs.text.return_value = mock_results
            mock_ddgs_cls.return_value = mock_ddgs

            result = duckduckgo_search.search("test query")

            assert isinstance(result, list)
            assert len(result) == 2
            mock_ddgs.text.assert_called_once_with(
                "test query",
                region="wt-wt",
                safesearch="off",
                timelimit="y",
                max_results=5,
            )

    def test_search_with_custom_params(self):
        from python.helpers import duckduckgo_search

        with patch("python.helpers.duckduckgo_search.DDGS") as mock_ddgs_cls:
            mock_ddgs = MagicMock()
            mock_ddgs.text.return_value = []
            mock_ddgs_cls.return_value = mock_ddgs

            duckduckgo_search.search(
                "query",
                results=10,
                region="us-en",
                time="w",
            )

            mock_ddgs.text.assert_called_once_with(
                "query",
                region="us-en",
                safesearch="off",
                timelimit="w",
                max_results=10,
            )

    def test_search_converts_results_to_strings(self):
        from python.helpers import duckduckgo_search

        mock_results = [{"title": "A", "body": "B"}, 123, "plain string"]

        with patch("python.helpers.duckduckgo_search.DDGS") as mock_ddgs_cls:
            mock_ddgs = MagicMock()
            mock_ddgs.text.return_value = mock_results
            mock_ddgs_cls.return_value = mock_ddgs

            result = duckduckgo_search.search("q")

            assert all(isinstance(r, str) for r in result)
            assert result[2] == "plain string"
