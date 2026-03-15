"""Tests for python/helpers/files.py."""

import base64
import os
import sys
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import for patch.object targets (avoids patch resolution issues with namespace packages)
import python.helpers.files as _files_mod
import python.helpers.extract_tools as _extract_tools_mod

# --- Fixtures ---


@pytest.fixture
def patch_base_dir(tmp_workdir):
    """Patch get_base_dir to use tmp_workdir for file operations."""
    with patch.object(_files_mod, "get_base_dir", return_value=str(tmp_workdir)):
        yield tmp_workdir


# --- load_plugin_variables ---


class TestLoadPluginVariables:
    def test_returns_empty_for_non_md_file(self):
        from python.helpers.files import load_plugin_variables

        assert load_plugin_variables("script.py") == {}
        assert load_plugin_variables("data.json") == {}

    def test_returns_empty_when_plugin_file_not_found(self):
        from python.helpers.files import load_plugin_variables

        with patch.object(_files_mod, "find_file_in_dirs") as mock_find:
            mock_find.side_effect = FileNotFoundError
            assert load_plugin_variables("prompt.md") == {}

    def test_returns_empty_when_plugin_file_does_not_exist(self):
        from python.helpers.files import load_plugin_variables

        with patch.object(_files_mod, "find_file_in_dirs", return_value="/nonexistent/prompt.py"):
            with patch.object(_files_mod, "exists", return_value=False):
                assert load_plugin_variables("prompt.md") == {}

    def test_returns_variables_from_plugin_class(self):
        from python.helpers.files import load_plugin_variables

        mock_cls = MagicMock()
        mock_instance = MagicMock()
        mock_instance.get_variables.return_value = {"foo": "bar"}
        mock_cls.return_value = mock_instance

        with patch.object(_files_mod, "find_file_in_dirs", return_value="/some/prompt.py"):
            with patch.object(_files_mod, "exists", return_value=True):
                with patch.object(
                    _extract_tools_mod,
                    "load_classes_from_file",
                    return_value=[mock_cls],
                ):
                    result = load_plugin_variables("prompt.md")
        assert result == {"foo": "bar"}
        mock_instance.get_variables.assert_called_once_with("prompt.md", [], **{})


# --- evaluate_text_conditions ---


class TestEvaluateTextConditions:
    def test_returns_unchanged_when_no_if_block(self):
        from python.helpers.files import evaluate_text_conditions

        text = "Hello {{name}}"
        assert evaluate_text_conditions(text, name="World") == "Hello {{name}}"

    def test_keeps_content_when_condition_true(self):
        from python.helpers.files import evaluate_text_conditions

        text = "A {{if x}}B{{endif}} C"
        assert evaluate_text_conditions(text, x=True) == "A B C"

    def test_removes_content_when_condition_false(self):
        from python.helpers.files import evaluate_text_conditions

        text = "A {{if x}}B{{endif}} C"
        assert evaluate_text_conditions(text, x=False) == "A  C"

    def test_nested_conditions(self):
        from python.helpers.files import evaluate_text_conditions

        text = "A {{if a}}B {{if b}}C{{endif}} D{{endif}} E"
        assert evaluate_text_conditions(text, a=True, b=True) == "A B C D E"
        assert evaluate_text_conditions(text, a=True, b=False) == "A B  D E"
        assert evaluate_text_conditions(text, a=False, b=True) == "A  E"


# --- is_probably_binary_bytes ---


class TestIsProbablyBinaryBytes:
    def test_empty_returns_false(self):
        from python.helpers.files import is_probably_binary_bytes

        assert is_probably_binary_bytes(b"") is False

    def test_nul_byte_returns_true(self):
        from python.helpers.files import is_probably_binary_bytes

        assert is_probably_binary_bytes(b"hello\x00world") is True

    def test_plain_text_returns_false(self):
        from python.helpers.files import is_probably_binary_bytes

        assert is_probably_binary_bytes(b"Hello world\n") is False

    def test_high_ratio_of_control_chars_returns_true(self):
        from python.helpers.files import is_probably_binary_bytes

        # Many control chars (excluding \t\n\f\r\b)
        data = bytes([0x01] * 40 + [0x20] * 10)  # 80% control
        assert is_probably_binary_bytes(data, threshold=0.3) is True

    def test_low_ratio_returns_false(self):
        from python.helpers.files import is_probably_binary_bytes

        data = b"Normal text with few control chars"
        assert is_probably_binary_bytes(data, threshold=0.3) is False


# --- replace_placeholders_text ---


class TestReplacePlaceholdersText:
    def test_replaces_single_placeholder(self):
        from python.helpers.files import replace_placeholders_text

        assert replace_placeholders_text("Hi {{name}}", name="Alice") == "Hi Alice"

    def test_replaces_multiple_placeholders(self):
        from python.helpers.files import replace_placeholders_text

        result = replace_placeholders_text("{{a}} + {{b}}", a=1, b=2)
        assert result == "1 + 2"

    def test_unchanged_when_no_placeholders(self):
        from python.helpers.files import replace_placeholders_text

        assert replace_placeholders_text("No placeholders") == "No placeholders"


# --- replace_placeholders_json ---


class TestReplacePlaceholdersJson:
    def test_replaces_with_json_serialization(self):
        from python.helpers.files import replace_placeholders_json

        result = replace_placeholders_json('{"x": {{val}}}', val=[1, 2])
        assert result == '{"x": [1, 2]}'

    def test_skips_placeholder_not_in_content(self):
        from python.helpers.files import replace_placeholders_json

        result = replace_placeholders_json('{"a": 1}', other=99)
        assert result == '{"a": 1}'


# --- replace_placeholders_dict ---


class TestReplacePlaceholdersDict:
    def test_replaces_in_string_value(self):
        from python.helpers.files import replace_placeholders_dict

        result = replace_placeholders_dict({"key": "{{x}}"}, x="val")
        assert result == {"key": "val"}

    def test_replaces_nested(self):
        from python.helpers.files import replace_placeholders_dict

        result = replace_placeholders_dict({"a": {"b": "{{x}}"}}, x=1)
        assert result == {"a": {"b": 1}}

    def test_replaces_in_list(self):
        from python.helpers.files import replace_placeholders_dict

        result = replace_placeholders_dict({"items": ["{{a}}", "{{b}}"]}, a=1, b=2)
        assert result == {"items": [1, 2]}


# --- remove_code_fences ---


class TestRemoveCodeFences:
    def test_removes_triple_backtick_fences(self):
        from python.helpers.files import remove_code_fences

        text = "```\ncode here\n```"
        assert remove_code_fences(text) == "code here\n"

    def test_removes_triple_tilde_fences(self):
        from python.helpers.files import remove_code_fences

        text = "~~~\ncode here\n~~~"
        assert remove_code_fences(text) == "code here\n"

    def test_removes_language_specifier(self):
        from python.helpers.files import remove_code_fences

        text = "```python\nprint(1)\n```"
        assert remove_code_fences(text) == "print(1)\n"


# --- is_full_json_template ---


class TestIsFullJsonTemplate:
    def test_true_for_json_fenced(self):
        from python.helpers.files import is_full_json_template

        text = "```json\n{}\n```"
        assert is_full_json_template(text) is True

    def test_true_for_tilde_json_fenced(self):
        from python.helpers.files import is_full_json_template

        text = "~~~json\n{\"a\":1}\n~~~"
        assert is_full_json_template(text) is True

    def test_false_for_plain_json(self):
        from python.helpers.files import is_full_json_template

        assert is_full_json_template("{}") is False

    def test_false_for_plain_text(self):
        from python.helpers.files import is_full_json_template

        assert is_full_json_template("hello") is False


# --- find_file_in_dirs ---


class TestFindFileInDirs:
    def test_returns_first_found(self, patch_base_dir):
        from python.helpers.files import find_file_in_dirs

        d1 = patch_base_dir / "dir1"
        d2 = patch_base_dir / "dir2"
        d1.mkdir()
        d2.mkdir()
        (d1 / "a.txt").write_text("first")
        (d2 / "a.txt").write_text("second")

        result = find_file_in_dirs("a.txt", [str(d1), str(d2)])
        assert "dir1" in result
        assert result.endswith("a.txt")

    def test_raises_when_not_found(self, patch_base_dir):
        from python.helpers.files import find_file_in_dirs

        with pytest.raises(FileNotFoundError, match="not found"):
            find_file_in_dirs("nonexistent.txt", [str(patch_base_dir)])


# --- get_unique_filenames_in_dirs ---


class TestGetUniqueFilenamesInDirs:
    def test_returns_unique_by_basename(self, patch_base_dir):
        from python.helpers.files import get_unique_filenames_in_dirs

        d1 = patch_base_dir / "d1"
        d2 = patch_base_dir / "d2"
        d1.mkdir()
        d2.mkdir()
        (d1 / "same.txt").write_text("a")
        (d2 / "same.txt").write_text("b")

        result = get_unique_filenames_in_dirs([str(d1), str(d2)])
        assert len(result) == 1
        assert "same.txt" in result[0]

    def test_filters_by_type_file(self, patch_base_dir):
        from python.helpers.files import get_unique_filenames_in_dirs

        d = patch_base_dir / "d"
        d.mkdir()
        sub = d / "subdir"
        sub.mkdir()
        (d / "f.txt").write_text("x")

        result = get_unique_filenames_in_dirs([str(d)], type="file")
        assert len(result) == 1
        assert "f.txt" in result[0]


# --- find_existing_paths_by_pattern ---


class TestFindExistingPathsByPattern:
    def test_empty_pattern_returns_empty(self):
        from python.helpers.files import find_existing_paths_by_pattern

        assert find_existing_paths_by_pattern("") == []

    def test_returns_sorted_matches(self, patch_base_dir):
        from python.helpers.files import find_existing_paths_by_pattern

        (patch_base_dir / "work_dir").mkdir(exist_ok=True)
        (patch_base_dir / "work_dir" / "a.txt").write_text("")
        (patch_base_dir / "work_dir" / "b.txt").write_text("")

        result = find_existing_paths_by_pattern("work_dir/*.txt")
        assert len(result) >= 2
        assert result == sorted(result)


# --- read_file, write_file ---


class TestReadWriteFile:
    def test_write_and_read_file(self, patch_base_dir):
        from python.helpers.files import read_file, write_file

        write_file("work_dir/test.txt", "hello world")
        assert read_file("work_dir/test.txt") == "hello world"

    def test_write_and_read_binary(self, patch_base_dir):
        from python.helpers.files import read_file_bin, write_file_bin

        data = b"\x00\x01\x02"
        write_file_bin("work_dir/binary.bin", data)
        assert read_file_bin("work_dir/binary.bin") == data

    def test_write_and_read_base64(self, patch_base_dir):
        from python.helpers.files import read_file_base64, write_file_base64

        encoded = base64.b64encode(b"binary data").decode("utf-8")
        write_file_base64("work_dir/b64.txt", encoded)
        assert read_file_base64("work_dir/b64.txt") == encoded

    def test_read_file_raises_for_nonexistent(self, patch_base_dir):
        from python.helpers.files import read_file

        with pytest.raises(FileNotFoundError):
            read_file("work_dir/nonexistent.txt")


# --- is_probably_binary_file ---


class TestIsProbablyBinaryFile:
    def test_text_file_returns_false(self, patch_base_dir):
        from python.helpers.files import is_probably_binary_file

        p = patch_base_dir / "text.txt"
        p.write_text("Hello world")
        assert is_probably_binary_file(str(p)) is False

    def test_binary_file_returns_true(self, patch_base_dir):
        from python.helpers.files import is_probably_binary_file

        p = patch_base_dir / "bin.dat"
        p.write_bytes(b"hello\x00world")
        assert is_probably_binary_file(str(p)) is True

    def test_raises_for_nonexistent_file(self):
        from python.helpers.files import is_probably_binary_file

        with pytest.raises(OSError, match="Unable to read"):
            is_probably_binary_file("/nonexistent/path/file.dat")


# --- create_dir, delete_dir, exists ---


class TestCreateDeleteDir:
    def test_create_dir(self, patch_base_dir):
        from python.helpers.files import create_dir, exists

        create_dir("work_dir/new_folder")
        assert exists("work_dir/new_folder")

    def test_delete_dir(self, patch_base_dir):
        from python.helpers.files import create_dir, delete_dir, exists

        create_dir("work_dir/to_delete")
        (patch_base_dir / "work_dir" / "to_delete" / "f.txt").write_text("x")
        delete_dir("work_dir/to_delete")
        assert not exists("work_dir/to_delete")


# --- move_dir, move_dir_safe, create_dir_safe ---


class TestMoveCreateDirSafe:
    def test_move_dir(self, patch_base_dir):
        from python.helpers.files import create_dir, exists, move_dir

        create_dir("work_dir/old")
        (patch_base_dir / "work_dir" / "old" / "f.txt").write_text("x")
        move_dir("work_dir/old", "work_dir/new")
        assert exists("work_dir/new")
        assert not exists("work_dir/old")

    def test_move_dir_safe_renames_when_exists(self, patch_base_dir):
        from python.helpers.files import create_dir, move_dir_safe

        create_dir("work_dir/dst")
        create_dir("work_dir/src")
        (patch_base_dir / "work_dir" / "src" / "f.txt").write_text("x")
        result = move_dir_safe("work_dir/src", "work_dir/dst")
        assert "dst_2" in result or "2" in result

    def test_create_dir_safe_renames_when_exists(self, patch_base_dir):
        from python.helpers.files import create_dir, create_dir_safe, exists

        create_dir("work_dir/target")
        result = create_dir_safe("work_dir/target")
        assert "target_2" in result or "2" in result
        assert exists(result)


# --- list_files, list_files_in_dir_recursively ---


class TestListFiles:
    def test_list_files_with_filter(self, patch_base_dir):
        from python.helpers.files import list_files, write_file

        write_file("work_dir/a.txt", "")
        write_file("work_dir/b.txt", "")
        write_file("work_dir/c.log", "")
        result = list_files("work_dir", "*.txt")
        assert set(result) == {"a.txt", "b.txt"}

    def test_list_files_returns_empty_for_nonexistent(self):
        from python.helpers.files import list_files

        with patch.object(_files_mod, "get_abs_path", return_value="/nonexistent/dir"):
            assert list_files("nonexistent") == []

    def test_list_files_in_dir_recursively(self, patch_base_dir):
        from python.helpers.files import create_dir, list_files_in_dir_recursively, write_file

        create_dir("work_dir/sub1/sub2")
        write_file("work_dir/a.txt", "")
        write_file("work_dir/sub1/b.txt", "")
        write_file("work_dir/sub1/sub2/c.txt", "")
        result = list_files_in_dir_recursively("work_dir")
        assert "a.txt" in result
        assert "sub1/b.txt" in result
        assert "sub1/sub2/c.txt" in result


# --- get_abs_path, deabsolute_path, basename, dirname ---


class TestPathHelpers:
    def test_get_abs_path_joins_with_base(self):
        from python.helpers.files import get_abs_path, get_base_dir

        result = get_abs_path("a", "b")
        assert result == os.path.join(get_base_dir(), "a", "b")

    def test_deabsolute_path(self, patch_base_dir):
        from python.helpers.files import deabsolute_path, get_abs_path

        abs_p = get_abs_path("work_dir", "f.txt")
        rel = deabsolute_path(abs_p)
        assert "work_dir" in rel
        assert "f.txt" in rel

    def test_basename_without_suffix(self):
        from python.helpers.files import basename

        assert basename("/path/to/file.txt") == "file.txt"

    def test_basename_with_suffix(self):
        from python.helpers.files import basename

        assert basename("/path/to/file.txt", ".txt") == "file"

    def test_dirname(self):
        from python.helpers.files import dirname

        assert dirname("/path/to/file.txt") == "/path/to"


# --- is_in_dir, is_in_base_dir ---


class TestIsInDir:
    def test_is_in_dir_true(self):
        from python.helpers.files import is_in_dir

        assert is_in_dir("/a/b/c/file.txt", "/a/b") is True

    def test_is_in_dir_false(self):
        from python.helpers.files import is_in_dir

        assert is_in_dir("/x/y/file.txt", "/a/b") is False


# --- get_subdirectories ---


class TestGetSubdirectories:
    def test_returns_matching_subdirs(self, patch_base_dir):
        from python.helpers.files import create_dir, get_subdirectories

        create_dir("work_dir/foo")
        create_dir("work_dir/bar")
        create_dir("work_dir/baz")
        result = get_subdirectories("work_dir", include="f*")
        assert "foo" in result
        assert "bar" not in result

    def test_exclude_pattern(self, patch_base_dir):
        from python.helpers.files import create_dir, get_subdirectories

        create_dir("work_dir/keep")
        create_dir("work_dir/skip")
        result = get_subdirectories("work_dir", exclude="skip")
        assert "keep" in result
        assert "skip" not in result


# --- zip_dir ---


class TestZipDir:
    def test_zip_dir_creates_valid_zip(self, patch_base_dir):
        from python.helpers.files import create_dir, write_file, zip_dir

        create_dir("work_dir/sub")
        write_file("work_dir/a.txt", "content")
        write_file("work_dir/sub/b.txt", "nested")
        zip_path = zip_dir("work_dir")
        try:
            with zipfile.ZipFile(zip_path, "r") as z:
                names = z.namelist()
                assert any("a.txt" in n for n in names)
                assert any("b.txt" in n for n in names)
        finally:
            if os.path.exists(zip_path):
                os.unlink(zip_path)


# --- move_file ---


class TestMoveFile:
    def test_move_file(self, patch_base_dir):
        from python.helpers.files import exists, move_file, write_file

        write_file("work_dir/origin.txt", "data")
        move_file("work_dir/origin.txt", "work_dir/dest.txt")
        assert exists("work_dir/dest.txt")
        assert not exists("work_dir/origin.txt")


# --- safe_file_name ---


class TestSafeFileName:
    def test_replaces_invalid_chars(self):
        from python.helpers.files import safe_file_name

        assert safe_file_name("file name.txt") == "file_name.txt"
        assert safe_file_name("a/b\\c") == "a_b_c"

    def test_preserves_valid_chars(self):
        from python.helpers.files import safe_file_name

        assert safe_file_name("valid-name_123.txt") == "valid-name_123.txt"


# --- read_text_files_in_dir ---


class TestReadTextFilesInDir:
    def test_reads_text_files(self, patch_base_dir):
        from python.helpers.files import read_text_files_in_dir, write_file

        write_file("work_dir/a.txt", "content a")
        write_file("work_dir/b.txt", "content b")
        result = read_text_files_in_dir("work_dir")
        assert result["a.txt"] == "content a"
        assert result["b.txt"] == "content b"

    def test_respects_pattern(self, patch_base_dir):
        from python.helpers.files import read_text_files_in_dir, write_file

        write_file("work_dir/a.txt", "x")
        write_file("work_dir/b.log", "y")
        result = read_text_files_in_dir("work_dir", pattern="*.txt")
        assert "a.txt" in result
        assert "b.log" not in result

    def test_returns_empty_for_nonexistent_dir(self):
        from python.helpers.files import read_text_files_in_dir

        with patch.object(_files_mod, "get_abs_path", return_value="/nonexistent"):
            assert read_text_files_in_dir("nonexistent") == {}


# --- process_includes ---


class TestProcessIncludes:
    def test_replaces_include_with_file_content(self, patch_base_dir):
        from python.helpers.files import process_includes

        content = "Before {{ include 'work_dir/included.txt' }} After"
        with patch.object(_files_mod, "read_prompt_file", return_value="included content"):
            result = process_includes(content, [str(patch_base_dir)])
        assert result == "Before included content After"

    def test_leaves_absolute_path_unchanged(self):
        from python.helpers.files import process_includes

        content = "{{ include '/abs/path/file.txt' }}"
        result = process_includes(content, [])
        assert "{{ include" in result
        assert "/abs/path" in result


# --- parse_file ---


class TestParseFile:
    def test_parse_json_template_file(self, patch_base_dir):
        from python.helpers.files import parse_file, write_file

        content = '```json\n{"key": "value"}\n```'
        write_file("work_dir/data.json", content)
        result = parse_file("work_dir/data.json", [str(patch_base_dir)])
        assert result == {"key": "value"}

    def test_parse_text_file_returns_string(self, patch_base_dir):
        from python.helpers.files import parse_file, write_file

        write_file("work_dir/plain.txt", "Hello {{name}}")
        with patch.object(_files_mod, "load_plugin_variables", return_value={}):
            result = parse_file("work_dir/plain.txt", [str(patch_base_dir)], name="World")
        assert result == "Hello World"
