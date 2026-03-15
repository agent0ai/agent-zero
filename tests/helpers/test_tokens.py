"""Tests for python/helpers/tokens.py — token counting."""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(autouse=True)
def mock_tiktoken():
    """Mock tiktoken to avoid real encoding calls."""
    mock_encoding = MagicMock()
    # Default: ~4 chars per token for English
    mock_encoding.encode.side_effect = lambda text, **kw: list(range(len(text) // 4 + 1))

    with patch("python.helpers.tokens.tiktoken") as mock_tiktoken_mod:
        mock_tiktoken_mod.get_encoding.return_value = mock_encoding
        yield mock_tiktoken_mod


# --- count_tokens ---


class TestCountTokens:
    """Tests for count_tokens()."""

    def test_empty_string(self, mock_tiktoken):
        from python.helpers.tokens import count_tokens

        result = count_tokens("")
        assert result == 0
        mock_tiktoken.get_encoding.assert_not_called()

    def test_short_text(self, mock_tiktoken):
        from python.helpers.tokens import count_tokens

        mock_encoding = mock_tiktoken.get_encoding.return_value
        mock_encoding.encode.side_effect = None
        mock_encoding.encode.return_value = [0, 1, 2, 3]  # 4 tokens

        result = count_tokens("hello world")
        assert result == 4
        mock_tiktoken.get_encoding.assert_called_once_with("cl100k_base")
        mock_encoding.encode.assert_called_once_with("hello world", disallowed_special=())

    def test_single_char(self, mock_tiktoken):
        from python.helpers.tokens import count_tokens

        mock_encoding = mock_tiktoken.get_encoding.return_value
        mock_encoding.encode.side_effect = None
        mock_encoding.encode.return_value = [0]

        result = count_tokens("x")
        assert result == 1

    def test_long_text(self, mock_tiktoken):
        from python.helpers.tokens import count_tokens

        long_text = "a" * 1000
        mock_encoding = mock_tiktoken.get_encoding.return_value
        mock_encoding.encode.side_effect = None
        mock_encoding.encode.return_value = list(range(250))  # 250 tokens

        result = count_tokens(long_text)
        assert result == 250

    def test_custom_encoding(self, mock_tiktoken):
        from python.helpers.tokens import count_tokens

        mock_encoding = mock_tiktoken.get_encoding.return_value
        mock_encoding.encode.side_effect = None
        mock_encoding.encode.return_value = [0, 1]

        count_tokens("test", encoding_name="gpt2")
        mock_tiktoken.get_encoding.assert_called_with("gpt2")


# --- approximate_tokens ---


class TestApproximateTokens:
    """Tests for approximate_tokens()."""

    def test_empty_string(self, mock_tiktoken):
        from python.helpers.tokens import approximate_tokens

        result = approximate_tokens("")
        assert result == 0

    def test_buffered_count(self, mock_tiktoken):
        from python.helpers.tokens import approximate_tokens

        mock_encoding = mock_tiktoken.get_encoding.return_value
        mock_encoding.encode.side_effect = None
        mock_encoding.encode.return_value = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]  # 10 tokens

        result = approximate_tokens("some text here")
        # 10 * 1.1 = 11
        assert result == 11

    def test_rounds_down(self, mock_tiktoken):
        from python.helpers.tokens import approximate_tokens

        mock_encoding = mock_tiktoken.get_encoding.return_value
        mock_encoding.encode.side_effect = None
        mock_encoding.encode.return_value = [0]  # 1 token

        result = approximate_tokens("x")
        assert result == 1  # int(1.1) = 1


# --- trim_to_tokens ---


class TestTrimToTokens:
    """Tests for trim_to_tokens()."""

    def test_within_limit(self, mock_tiktoken):
        from python.helpers.tokens import trim_to_tokens

        mock_encoding = mock_tiktoken.get_encoding.return_value
        mock_encoding.encode.side_effect = None
        mock_encoding.encode.return_value = [0, 1, 2]  # 3 tokens
        text = "short"

        result = trim_to_tokens(text, max_tokens=10, direction="start")
        assert result == "short"

        result = trim_to_tokens(text, max_tokens=10, direction="end")
        assert result == "short"

    def test_exceeds_limit_start(self, mock_tiktoken):
        from python.helpers.tokens import trim_to_tokens

        # 100 chars, 25 tokens -> exceeds 10 tokens
        text = "a" * 100
        mock_encoding = mock_tiktoken.get_encoding.return_value
        mock_encoding.encode.side_effect = None
        mock_encoding.encode.return_value = list(range(25))

        result = trim_to_tokens(text, max_tokens=10, direction="start")
        assert result.endswith("...")
        assert not result.startswith("...")
        assert len(result) < len(text)

    def test_exceeds_limit_end(self, mock_tiktoken):
        from python.helpers.tokens import trim_to_tokens

        text = "a" * 100
        mock_encoding = mock_tiktoken.get_encoding.return_value
        mock_encoding.encode.side_effect = None
        mock_encoding.encode.return_value = list(range(25))

        result = trim_to_tokens(text, max_tokens=10, direction="end")
        assert result.startswith("...")
        assert not result.endswith("...")

    def test_custom_ellipsis(self, mock_tiktoken):
        from python.helpers.tokens import trim_to_tokens

        text = "a" * 100
        mock_encoding = mock_tiktoken.get_encoding.return_value
        mock_encoding.encode.return_value = list(range(25))

        result = trim_to_tokens(text, max_tokens=10, direction="start", ellipsis=" […] ")
        assert result.endswith(" […] ")

    def test_zero_max_tokens(self, mock_tiktoken):
        from python.helpers.tokens import trim_to_tokens

        text = "hello"
        mock_encoding = mock_tiktoken.get_encoding.return_value
        mock_encoding.encode.return_value = [0, 1, 2]

        result = trim_to_tokens(text, max_tokens=0, direction="start")
        assert result.endswith("...")
        assert len(result) < len(text)
