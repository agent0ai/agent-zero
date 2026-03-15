"""Tests for python/helpers/strings.py."""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class TestSanitizeString:
    def test_returns_valid_string_unchanged(self):
        from python.helpers.strings import sanitize_string

        assert sanitize_string("hello") == "hello"
        assert sanitize_string("café") == "café"

    def test_replaces_surrogates(self):
        from python.helpers.strings import sanitize_string

        # Surrogate pair in invalid context
        result = sanitize_string("\udc80")
        assert "\udc80" not in result
        assert "\ufffd" in result or len(result) > 0

    def test_converts_non_str_to_str(self):
        from python.helpers.strings import sanitize_string

        assert sanitize_string(123) == "123"
        assert sanitize_string(3.14) == "3.14"


class TestCalculateValidMatchLengths:
    def test_identical_strings(self):
        from python.helpers.strings import calculate_valid_match_lengths

        a, b = calculate_valid_match_lengths("abc", "abc")
        assert a == 3
        assert b == 3

    def test_partial_match_with_deviation(self):
        from python.helpers.strings import calculate_valid_match_lengths

        a, b = calculate_valid_match_lengths("abc", "axc")
        assert a >= 1
        assert b >= 1

    def test_empty_strings(self):
        from python.helpers.strings import calculate_valid_match_lengths

        a, b = calculate_valid_match_lengths("", "")
        assert a == 0
        assert b == 0

    def test_bytes_input(self):
        from python.helpers.strings import calculate_valid_match_lengths

        a, b = calculate_valid_match_lengths(b"foo", b"foo")
        assert a == 3
        assert b == 3

    def test_ignore_patterns_skips_matching(self):
        from python.helpers.strings import calculate_valid_match_lengths

        # Pattern that matches leading spaces
        a, b = calculate_valid_match_lengths("  abc", "  abc", ignore_patterns=[r"^\s+"])
        assert a == 5
        assert b == 5


class TestFormatKey:
    def test_camel_case(self):
        from python.helpers.strings import format_key

        assert format_key("camelCase") == "Camel Case"

    def test_snake_case(self):
        from python.helpers.strings import format_key

        assert format_key("snake_case") == "Snake Case"

    def test_mixed(self):
        from python.helpers.strings import format_key

        assert format_key("some_key_name") == "Some Key Name"


class TestDictToText:
    def test_simple_dict(self):
        from python.helpers.strings import dict_to_text

        result = dict_to_text({"foo": "bar", "baz": 42})
        assert "Foo:" in result
        assert "bar" in result
        assert "Baz:" in result
        assert "42" in result

    def test_empty_dict(self):
        from python.helpers.strings import dict_to_text

        assert dict_to_text({}) == ""


class TestTruncateText:
    def test_short_text_unchanged(self):
        from python.helpers.strings import truncate_text

        assert truncate_text("hi", 10) == "hi"

    def test_truncate_at_end(self):
        from python.helpers.strings import truncate_text

        assert truncate_text("hello world", 8, at_end=True) == "hello wo..."

    def test_truncate_at_start(self):
        from python.helpers.strings import truncate_text

        assert truncate_text("hello world", 8, at_end=False) == "...o world"

    def test_custom_replacement(self):
        from python.helpers.strings import truncate_text

        assert truncate_text("hello", 3, replacement="…") == "hel…"


class TestTruncateTextByRatio:
    def test_short_text_unchanged(self):
        from python.helpers.strings import truncate_text_by_ratio

        assert truncate_text_by_ratio("hi", 100) == "hi"

    def test_ratio_zero_replaces_from_start(self):
        from python.helpers.strings import truncate_text_by_ratio

        result = truncate_text_by_ratio("abcdefghij", 8, ratio=0.0)
        assert result.startswith("...")
        assert len(result) == 8

    def test_ratio_one_replaces_from_end(self):
        from python.helpers.strings import truncate_text_by_ratio

        result = truncate_text_by_ratio("abcdefghij", 8, ratio=1.0)
        assert result.endswith("...")
        assert len(result) == 8

    def test_ratio_half_splits_middle(self):
        from python.helpers.strings import truncate_text_by_ratio

        result = truncate_text_by_ratio("abcdefghijklmnop", 12, ratio=0.5)
        assert "..." in result
        assert len(result) == 12


class TestReplaceFileIncludes:
    def test_no_placeholders_returns_unchanged(self):
        from python.helpers.strings import replace_file_includes

        text = "plain text"
        assert replace_file_includes(text) == text

    def test_empty_string_returns_empty(self):
        from python.helpers.strings import replace_file_includes

        assert replace_file_includes("") == ""

    def test_replaces_include_with_file_content(self):
        from python.helpers.strings import replace_file_includes

        with patch("python.helpers.strings.files") as mock_files:
            mock_files.fix_dev_path.return_value = "/some/path"
            mock_files.read_file.return_value = "file content"
            result = replace_file_includes("before §§include(/path/to/file) after")
            assert "file content" in result
            assert "before" in result
            assert "after" in result

    def test_keeps_placeholder_when_file_unreadable(self):
        from python.helpers.strings import replace_file_includes

        with patch("python.helpers.strings.files") as mock_files:
            mock_files.fix_dev_path.side_effect = OSError("not found")
            result = replace_file_includes("text §§include(missing) more")
            assert "§§include(missing)" in result
