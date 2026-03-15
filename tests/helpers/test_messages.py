"""Tests for python/helpers/messages.py."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# --- truncate_text ---


class TestTruncateText:
    def test_truncate_text_returns_unchanged_when_under_threshold(self):
        from python.helpers import messages

        mock_agent = MagicMock()
        mock_agent.read_prompt = MagicMock(return_value="[...truncated...]")
        output = "short text"
        result = messages.truncate_text(mock_agent, output, threshold=1000)
        assert result == "short text"
        mock_agent.read_prompt.assert_not_called()

    def test_truncate_text_returns_unchanged_when_zero_threshold(self):
        from python.helpers import messages

        mock_agent = MagicMock()
        output = "x" * 500
        result = messages.truncate_text(mock_agent, output, threshold=0)
        assert result == output

    def test_truncate_text_truncates_when_over_threshold(self):
        from python.helpers import messages

        mock_agent = MagicMock()
        mock_agent.read_prompt = MagicMock(return_value="[...truncated...]")
        output = "a" * 1500
        result = messages.truncate_text(mock_agent, output, threshold=1000)
        assert len(result) <= 1000 + 20
        assert "[...truncated...]" in result
        assert result.startswith("a")
        assert result.endswith("a")
        mock_agent.read_prompt.assert_called_once()

    def test_truncate_text_uses_placeholder_length(self):
        from python.helpers import messages

        mock_agent = MagicMock()
        mock_agent.read_prompt = MagicMock(return_value="[...]")
        output = "x" * 200
        result = messages.truncate_text(mock_agent, output, threshold=100)
        mock_agent.read_prompt.assert_called_once()
        call_kwargs = mock_agent.read_prompt.call_args[1]
        assert call_kwargs["length"] == 100


# --- truncate_dict_by_ratio ---


class TestTruncateDictByRatio:
    def test_truncate_dict_by_ratio_returns_unchanged_when_under_threshold(self):
        from python.helpers import messages

        mock_agent = MagicMock()
        mock_agent.read_prompt = MagicMock(return_value="[...]")
        data = {"key": "short", "nested": {"a": 1}}
        result = messages.truncate_dict_by_ratio(
            mock_agent, data, threshold_chars=10000, truncate_to=100
        )
        assert result == data
        mock_agent.read_prompt.assert_not_called()

    def test_truncate_dict_by_ratio_truncates_large_string_value(self):
        from python.helpers import messages

        mock_agent = MagicMock()
        mock_agent.read_prompt = MagicMock(side_effect=lambda x, length: f"[truncated {length}]")
        data = {"key": "x" * 500}
        result = messages.truncate_dict_by_ratio(
            mock_agent, data, threshold_chars=100, truncate_to=50
        )
        assert "truncated" in str(result["key"]) or len(result["key"]) < 500

    def test_truncate_dict_by_ratio_processes_nested_dict(self):
        from python.helpers import messages

        mock_agent = MagicMock()
        mock_agent.read_prompt = MagicMock(return_value="[...]")
        data = {"outer": {"inner": "value"}}
        result = messages.truncate_dict_by_ratio(
            mock_agent, data, threshold_chars=10000, truncate_to=100
        )
        assert result["outer"]["inner"] == "value"

    def test_truncate_dict_by_ratio_processes_list(self):
        from python.helpers import messages

        mock_agent = MagicMock()
        mock_agent.read_prompt = MagicMock(return_value="[...]")
        data = [{"a": 1}, {"b": 2}]
        result = messages.truncate_dict_by_ratio(
            mock_agent, data, threshold_chars=10000, truncate_to=100
        )
        assert result[0]["a"] == 1
        assert result[1]["b"] == 2

    def test_truncate_dict_by_ratio_truncates_string_item(self):
        from python.helpers import messages

        mock_agent = MagicMock()
        mock_agent.read_prompt = MagicMock(side_effect=lambda x, length: f"[{length}]")
        data = "a" * 500
        result = messages.truncate_dict_by_ratio(
            mock_agent, data, threshold_chars=100, truncate_to=50
        )
        assert "[" in str(result) or len(result) < 500

    def test_truncate_dict_by_ratio_passes_non_dict_list_str_through(self):
        from python.helpers import messages

        mock_agent = MagicMock()
        data = 42
        result = messages.truncate_dict_by_ratio(
            mock_agent, data, threshold_chars=10, truncate_to=5
        )
        assert result == 42
