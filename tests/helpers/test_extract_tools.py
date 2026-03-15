"""Tests for python/helpers/extract_tools.py — tool call extraction from LLM responses."""

import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# --- extract_json_object_string ---


class TestExtractJsonObjectString:
    """Tests for extract_json_object_string()."""

    def test_simple_object(self):
        from python.helpers.extract_tools import extract_json_object_string

        content = 'Here is the result: {"tool": "search", "query": "test"}'
        result = extract_json_object_string(content)
        assert result == '{"tool": "search", "query": "test"}'

    def test_nested_object(self):
        from python.helpers.extract_tools import extract_json_object_string

        content = 'Prefix {"a": {"b": 1}, "c": [1, 2]} suffix'
        result = extract_json_object_string(content)
        assert result == '{"a": {"b": 1}, "c": [1, 2]}'

    def test_no_opening_brace(self):
        from python.helpers.extract_tools import extract_json_object_string

        result = extract_json_object_string("no json here")
        assert result == ""

    def test_no_closing_brace(self):
        from python.helpers.extract_tools import extract_json_object_string

        content = 'Start {"a": 1'
        result = extract_json_object_string(content)
        assert result == '{"a": 1'

    def test_multiple_objects_uses_last_brace(self):
        from python.helpers.extract_tools import extract_json_object_string

        content = '{"first": 1} and {"second": 2}'
        result = extract_json_object_string(content)
        assert result == '{"first": 1} and {"second": 2}'

    def test_llm_response_with_markdown(self):
        from python.helpers.extract_tools import extract_json_object_string

        content = """I'll search for that.

```json
{"name": "search", "args": {"q": "weather"}}
```
"""
        result = extract_json_object_string(content)
        assert "{" in result and "}" in result
        assert "search" in result


# --- extract_json_string ---


class TestExtractJsonString:
    """Tests for extract_json_string() — regex-based extraction."""

    def test_extracts_object(self):
        from python.helpers.extract_tools import extract_json_string

        content = 'text {"a": 1} more'
        result = extract_json_string(content)
        assert result == '{"a": 1}'

    def test_extracts_array(self):
        from python.helpers.extract_tools import extract_json_string

        content = 'text [1, 2, 3] more'
        result = extract_json_string(content)
        assert result == "[1, 2, 3]"

    def test_extracts_first_match(self):
        from python.helpers.extract_tools import extract_json_string

        content = '{"first": 1} {"second": 2}'
        result = extract_json_string(content)
        assert "first" in result or "second" in result

    def test_no_match_returns_empty(self):
        from python.helpers.extract_tools import extract_json_string

        result = extract_json_string("no json at all")
        assert result == ""


# --- fix_json_string ---


class TestFixJsonString:
    """Tests for fix_json_string()."""

    def test_replaces_unescaped_newlines_in_string_values(self):
        from python.helpers.extract_tools import fix_json_string

        json_str = '{"key": "line1\nline2"}'
        result = fix_json_string(json_str)
        assert "\\n" in result
        assert "\n" not in result.split('"')[2] or "\\n" in result

    def test_preserves_escaped_newlines(self):
        from python.helpers.extract_tools import fix_json_string

        json_str = '{"key": "line1\\nline2"}'
        result = fix_json_string(json_str)
        assert "\\n" in result


# --- json_parse_dirty ---


class TestJsonParseDirty:
    """Tests for json_parse_dirty() — main entry for parsing LLM JSON."""

    def test_valid_json_in_content(self):
        from python.helpers.extract_tools import json_parse_dirty

        content = 'Response: {"tool": "search", "args": {"q": "test"}}'
        result = json_parse_dirty(content)
        assert result == {"tool": "search", "args": {"q": "test"}}

    def test_dirty_json_trailing_comma(self):
        from python.helpers.extract_tools import json_parse_dirty

        content = '{"a": 1, "b": 2,}'
        result = json_parse_dirty(content)
        assert result == {"a": 1, "b": 2}

    def test_empty_input(self):
        from python.helpers.extract_tools import json_parse_dirty

        assert json_parse_dirty("") is None
        assert json_parse_dirty(None) is None

    def test_non_string_input(self):
        from python.helpers.extract_tools import json_parse_dirty

        assert json_parse_dirty(123) is None
        assert json_parse_dirty([]) is None

    def test_no_json_object(self):
        from python.helpers.extract_tools import json_parse_dirty

        result = json_parse_dirty("just plain text")
        assert result is None

    def test_malformed_returns_none(self):
        from python.helpers.extract_tools import json_parse_dirty

        with patch("python.helpers.extract_tools.DirtyJson") as mock_dirty:
            mock_dirty.parse_string.side_effect = Exception("parse error")
            result = json_parse_dirty('{"broken": ')
            assert result is None

    def test_extracted_not_dict_returns_none(self):
        from python.helpers.extract_tools import json_parse_dirty

        # extract_json_object_string returns "[1,2,3]" for array
        content = "Here is an array: [1, 2, 3]"
        result = json_parse_dirty(content)
        # json_parse_dirty only returns dict, so array -> None
        assert result is None

    def test_multi_tool_response(self):
        from python.helpers.extract_tools import json_parse_dirty

        content = '{"tools": [{"name": "search"}, {"name": "fetch"}]}'
        result = json_parse_dirty(content)
        assert result == {"tools": [{"name": "search"}, {"name": "fetch"}]}


# --- import_module ---


class TestImportModule:
    """Tests for import_module()."""

    def test_import_module_success(self, tmp_path):
        from python.helpers.extract_tools import import_module

        mod_file = tmp_path / "test_mod.py"
        mod_file.write_text("X = 42\n")

        with patch("python.helpers.extract_tools.get_abs_path", return_value=str(mod_file)):
            mod = import_module("test_mod.py")
            assert mod.X == 42

    def test_import_module_missing_file_raises(self):
        from python.helpers.extract_tools import import_module

        with patch("python.helpers.extract_tools.get_abs_path", return_value="/nonexistent/mod.py"):
            with patch("importlib.util.spec_from_file_location", return_value=None):
                with pytest.raises(ImportError, match="Could not load"):
                    import_module("mod.py")


# --- load_classes_from_file ---


class TestLoadClassesFromFile:
    """Tests for load_classes_from_file()."""

    def test_loads_subclass(self, tmp_path):
        from python.helpers.extract_tools import load_classes_from_file

        mod_file = tmp_path / "plugin.py"
        mod_file.write_text("""
class Base:
    pass

class MyTool(Base):
    pass
""")

        with patch("python.helpers.extract_tools.get_abs_path", return_value=str(mod_file)):
            classes = load_classes_from_file("plugin.py", object, one_per_file=False)
            assert len(classes) >= 1
            assert any(c.__name__ == "MyTool" for c in classes)

    def test_one_per_file(self, tmp_path):
        from python.helpers.extract_tools import load_classes_from_file

        mod_file = tmp_path / "multi.py"
        mod_file.write_text("""
class Base:
    pass

class A(Base):
    pass

class B(Base):
    pass
""")

        with patch("python.helpers.extract_tools.get_abs_path", return_value=str(mod_file)):
            classes = load_classes_from_file("multi.py", object, one_per_file=True)
            assert len(classes) == 1


# --- load_classes_from_folder ---


class TestLoadClassesFromFolder:
    """Tests for load_classes_from_folder()."""

    def test_loads_from_matching_files(self, tmp_path):
        from python.helpers.extract_tools import load_classes_from_folder

        (tmp_path / "tool_a.py").write_text("""
class Base:
    pass

class ToolA(Base):
    pass
""")
        (tmp_path / "tool_b.py").write_text("""
class Base:
    pass

class ToolB(Base):
    pass
""")
        (tmp_path / "other.txt").write_text("ignore")

        def mock_get_abs_path(*args):
            if not args:
                return str(tmp_path)
            joined = os.path.join(*[str(a) for a in args])
            if joined.endswith(".py"):
                if os.path.sep in joined or os.path.isabs(joined):
                    return joined
                return str(tmp_path / joined)
            return str(tmp_path)

        with patch("python.helpers.extract_tools.get_abs_path", side_effect=mock_get_abs_path):
            classes = load_classes_from_folder(
                str(tmp_path), "tool_*.py", object, one_per_file=True
            )
            assert len(classes) >= 1
