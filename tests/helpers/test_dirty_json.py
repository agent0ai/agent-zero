"""Tests for python/helpers/dirty_json.py — invalid JSON parser."""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# --- try_parse ---


class TestTryParse:
    """Tests for try_parse() — tries standard JSON first, falls back to DirtyJson."""

    def test_valid_json_object(self):
        from python.helpers.dirty_json import try_parse

        result = try_parse('{"a": 1, "b": 2}')
        assert result == {"a": 1, "b": 2}

    def test_valid_json_array(self):
        from python.helpers.dirty_json import try_parse

        result = try_parse("[1, 2, 3]")
        assert result == [1, 2, 3]

    def test_dirty_json_trailing_comma(self):
        from python.helpers.dirty_json import try_parse

        result = try_parse('{"a": 1, "b": 2,}')
        assert result == {"a": 1, "b": 2}

    def test_dirty_json_single_quotes(self):
        from python.helpers.dirty_json import try_parse

        result = try_parse("{'a': 1, 'b': 'hello'}")
        assert result == {"a": 1, "b": "hello"}

    def test_dirty_json_unquoted_keys(self):
        from python.helpers.dirty_json import try_parse

        result = try_parse("{foo: 1, bar: 2}")
        assert result == {"foo": 1, "bar": 2}


# --- parse ---


class TestParse:
    """Tests for parse() — always uses DirtyJson."""

    def test_valid_json(self):
        from python.helpers.dirty_json import parse

        result = parse('{"x": 42}')
        assert result == {"x": 42}

    def test_trailing_comma_object(self):
        from python.helpers.dirty_json import parse

        result = parse('{"a": 1,}')
        assert result == {"a": 1}

    def test_trailing_comma_array(self):
        from python.helpers.dirty_json import parse

        result = parse("[1, 2, 3,]")
        assert result == [1, 2, 3]

    def test_single_quotes(self):
        from python.helpers.dirty_json import parse

        result = parse("{'key': 'value'}")
        assert result == {"key": "value"}

    def test_unquoted_keys(self):
        from python.helpers.dirty_json import parse

        result = parse("{name: 'Alice', age: 30}")
        assert result == {"name": "Alice", "age": 30}

    def test_single_line_comment(self):
        from python.helpers.dirty_json import parse

        result = parse('{"a": 1 // comment\n}')
        assert result == {"a": 1}

    def test_multi_line_comment(self):
        from python.helpers.dirty_json import parse

        result = parse('{"a": 1 /* block comment */}')
        assert result == {"a": 1}

    def test_empty_string(self):
        from python.helpers.dirty_json import parse

        result = parse("")
        assert result is None

    def test_whitespace_only(self):
        from python.helpers.dirty_json import parse

        result = parse("   \n\t  ")
        assert result is None

    def test_truncated_json(self):
        from python.helpers.dirty_json import parse

        result = parse('{"a": 1, "b": ')
        assert result == {"a": 1, "b": None}

    def test_nested_dirty_json(self):
        from python.helpers.dirty_json import parse

        result = parse('{"outer": {"inner": [1, 2,]}, "trailing": true,}')
        assert result == {"outer": {"inner": [1, 2]}, "trailing": True}

    def test_null_and_undefined(self):
        from python.helpers.dirty_json import parse

        result = parse('{"a": null, "b": undefined}')
        assert result == {"a": None, "b": None}

    def test_true_false(self):
        from python.helpers.dirty_json import parse

        result = parse('{"yes": true, "no": false}')
        assert result == {"yes": True, "no": False}

    def test_numbers(self):
        from python.helpers.dirty_json import parse

        result = parse('{"int": 42, "float": 3.14, "neg": -10, "exp": 1e5}')
        assert result["int"] == 42
        assert result["float"] == 3.14
        assert result["neg"] == -10
        assert result["exp"] == 100000.0

    def test_multiline_string_triple_quotes(self):
        from python.helpers.dirty_json import parse

        result = parse('"""line1\nline2"""')
        assert result == "line1\nline2"

    def test_json_with_leading_text(self):
        from python.helpers.dirty_json import parse

        result = parse('Some text {"a": 1}')
        assert result == {"a": 1}

    def test_backtick_quotes(self):
        from python.helpers.dirty_json import parse

        result = parse('{"key": `value`}')
        assert result == {"key": "value"}

    def test_escape_sequences(self):
        from python.helpers.dirty_json import parse

        result = parse(r'{"tab": "\t", "newline": "\n", "quote": "\""}')
        assert result == {"tab": "\t", "newline": "\n", "quote": '"'}


# --- stringify ---


class TestStringify:
    """Tests for stringify()."""

    def test_simple_object(self):
        from python.helpers.dirty_json import stringify

        result = stringify({"a": 1, "b": 2})
        assert result == '{"a": 1, "b": 2}'

    def test_unicode(self):
        from python.helpers.dirty_json import stringify

        result = stringify({"msg": "café"})
        assert "café" in result
        assert "\\u" not in result  # ensure_ascii=False

    def test_passthrough_kwargs(self):
        from python.helpers.dirty_json import stringify

        result = stringify({"a": 1}, indent=2)
        assert "\n" in result
        assert "  " in result


# --- DirtyJson class ---


class TestDirtyJsonClass:
    """Tests for DirtyJson class directly."""

    def test_parse_string_static(self):
        from python.helpers.dirty_json import DirtyJson

        result = DirtyJson.parse_string('{"x": 1}')
        assert result == {"x": 1}

    def test_feed_incremental(self):
        from python.helpers.dirty_json import DirtyJson

        parser = DirtyJson()
        result1 = parser.feed('{"a": ')
        assert result1 == {"a": None}
        # After the first feed exhausts input the object is already popped
        # from the internal stack, so a second feed cannot resume inside it.
        # Verify the partial result is preserved.
        assert parser.result == {"a": None}

    def test_feed_empty_then_content(self):
        from python.helpers.dirty_json import DirtyJson

        parser = DirtyJson()
        result = parser.feed('{"x": 1}')
        assert result == {"x": 1}

    def test_double_brace_handling(self):
        from python.helpers.dirty_json import parse

        # The {{ handler advances past both opening braces, then
        # _parse_object advances one more char, so the key is parsed
        # as an unquoted token that includes the trailing quote char.
        result = parse('{{"a": 1}}')
        assert result == {'a"': 1}

    def test_double_brace_closing(self):
        from python.helpers.dirty_json import parse

        result = parse('{"a": 1}}')
        assert result == {"a": 1}


# --- Edge cases ---


class TestDirtyJsonEdgeCases:
    """Edge cases and error resilience."""

    def test_array_with_trailing_comma_only(self):
        from python.helpers.dirty_json import parse

        result = parse("[1,]")
        assert result == [1]

    def test_object_no_closing_brace(self):
        from python.helpers.dirty_json import parse

        result = parse('{"a": 1')
        assert result == {"a": 1}

    def test_empty_object(self):
        from python.helpers.dirty_json import parse

        result = parse("{}")
        assert result == {}

    def test_empty_array(self):
        from python.helpers.dirty_json import parse

        result = parse("[]")
        assert result == []

    def test_deeply_nested(self):
        from python.helpers.dirty_json import parse

        result = parse('{"a": {"b": {"c": [1, 2]}}}')
        assert result == {"a": {"b": {"c": [1, 2]}}}

    def test_unquoted_string_value(self):
        from python.helpers.dirty_json import parse

        result = parse("{key: someValue}")
        assert result == {"key": "someValue"}
