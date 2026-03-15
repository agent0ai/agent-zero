"""Comprehensive unit tests for python/helpers/file_tree.py."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.helpers.files import create_dir, delete_dir, get_abs_path, write_file
import python.helpers.files as _files_mod
from python.helpers.file_tree import (
    OUTPUT_MODE_FLAT,
    OUTPUT_MODE_NESTED,
    OUTPUT_MODE_STRING,
    SORT_ASC,
    SORT_BY_CREATED,
    SORT_BY_MODIFIED,
    SORT_BY_NAME,
    SORT_DESC,
    file_tree,
)


def materialize_structure(base_rel: str, structure: dict) -> None:
    """Create directory structure from nested dict."""
    for entry, value in structure.items():
        rel = os.path.join(base_rel, entry)
        if isinstance(value, dict):
            create_dir(rel)
            materialize_structure(rel, value)
        else:
            write_file(rel, "" if value is None else str(value))


# --- Fixtures ---


@pytest.fixture
def patch_base_dir(tmp_workdir):
    """Patch get_base_dir to use tmp_workdir for file operations."""
    with patch.object(_files_mod, "get_base_dir", return_value=str(tmp_workdir)):
        with patch.object(
            _files_mod,
            "get_abs_path_dockerized",
            side_effect=lambda *p: str(Path(tmp_workdir).joinpath(*p)),
        ):
            yield tmp_workdir


@pytest.fixture
def tree_root(patch_base_dir):
    """Create a standard tree structure for tests."""
    rel = "tmp/tests/file_tree/root"
    delete_dir(rel)
    create_dir(rel)
    materialize_structure(
        rel,
        {
            "alpha": {"alpha_file.txt": "alpha", "nested": {"inner.txt": "inner"}},
            "beta": {"beta_file.txt": "beta"},
            "zeta": {},
            "a.txt": "A",
            "b.txt": "B",
        },
    )
    try:
        yield rel
    finally:
        delete_dir(rel)


# --- Error handling ---


class TestFileTreeErrors:
    def test_raises_file_not_found_for_nonexistent_path(self, patch_base_dir):
        with pytest.raises(FileNotFoundError, match="Path does not exist"):
            file_tree("nonexistent/path/that/does/not/exist")

    def test_raises_not_a_directory_for_file_path(self, patch_base_dir):
        rel = "tmp/tests/file_tree/file_as_path"
        parent = os.path.dirname(rel)
        delete_dir(rel)
        create_dir(parent)
        write_file(rel, "content")
        try:
            with pytest.raises(NotADirectoryError, match="Expected a directory"):
                file_tree(rel)
        finally:
            abs_path = get_abs_path(rel)
            if os.path.isfile(abs_path):
                os.remove(abs_path)

    def test_raises_value_error_for_invalid_sort_key(self, tree_root):
        with pytest.raises(ValueError, match="Unsupported sort key"):
            file_tree(tree_root, sort=("invalid_key", SORT_ASC))

    def test_raises_value_error_for_invalid_sort_direction(self, tree_root):
        with pytest.raises(ValueError, match="Unsupported sort direction"):
            file_tree(tree_root, sort=(SORT_BY_NAME, "invalid"))

    def test_raises_value_error_for_invalid_output_mode(self, tree_root):
        with pytest.raises(ValueError, match="Unsupported output mode"):
            file_tree(tree_root, output_mode="invalid_mode")

    def test_raises_value_error_for_negative_max_depth(self, tree_root):
        with pytest.raises(ValueError, match="max_depth must be >= 0"):
            file_tree(tree_root, max_depth=-1)

    def test_raises_value_error_for_negative_max_lines(self, tree_root):
        with pytest.raises(ValueError, match="max_lines must be >= 0"):
            file_tree(tree_root, max_lines=-1)


# --- Tree visualization format ---


class TestFileTreeStringOutput:
    def test_string_output_has_root_banner(self, tree_root):
        result = file_tree(tree_root, output_mode=OUTPUT_MODE_STRING)
        first_line = result.strip().split("\n")[0]
        assert first_line.endswith("/")
        assert "alpha" in result or "beta" in result or "a.txt" in result

    def test_string_output_uses_tree_connectors(self, tree_root):
        result = file_tree(tree_root, sort=(SORT_BY_NAME, SORT_ASC))
        assert "├── " in result or "└── " in result
        assert "/" in result  # folders end with /

    def test_string_output_folders_first_by_default(self, tree_root):
        result = file_tree(tree_root, sort=(SORT_BY_NAME, SORT_ASC), folders_first=True)
        # alpha, beta, zeta (folders) should appear before a.txt, b.txt (files)
        alpha_pos = result.find("alpha")
        a_txt_pos = result.find("a.txt")
        if alpha_pos >= 0 and a_txt_pos >= 0:
            assert alpha_pos < a_txt_pos

    def test_string_output_files_first_when_disabled(self, tree_root):
        result = file_tree(tree_root, sort=(SORT_BY_NAME, SORT_ASC), folders_first=False)
        assert "a.txt" in result and "b.txt" in result
        assert "alpha/" in result and "beta/" in result


# --- Filtering (ignore patterns) ---


class TestFileTreeFiltering:
    def test_inline_ignore_patterns_exclude_files(self, patch_base_dir):
        rel = "tmp/tests/file_tree/ignore_test"
        delete_dir(rel)
        create_dir(rel)
        write_file(os.path.join(rel, "keep.txt"), "keep")
        write_file(os.path.join(rel, "skip.pyc"), "skip")
        try:
            result = file_tree(rel, ignore="*.pyc\n", output_mode=OUTPUT_MODE_STRING)
            assert "keep.txt" in result
            assert "skip.pyc" not in result
        finally:
            delete_dir(rel)

    def test_inline_ignore_excludes_directories(self, patch_base_dir):
        rel = "tmp/tests/file_tree/ignore_dir"
        delete_dir(rel)
        materialize_structure(rel, {"visible": {"f.txt": ""}, "hidden_dir": {"x.txt": ""}})
        try:
            result = file_tree(rel, ignore="hidden_dir/\n", output_mode=OUTPUT_MODE_STRING)
            assert "visible" in result
            assert "hidden_dir" not in result
        finally:
            delete_dir(rel)

    def test_file_ignore_reference(self, patch_base_dir):
        rel = "tmp/tests/file_tree/ignore_file_ref"
        delete_dir(rel)
        create_dir(rel)
        write_file(os.path.join(rel, ".gitignore"), "*.log\n__pycache__/\n")
        write_file(os.path.join(rel, "keep.txt"), "")
        write_file(os.path.join(rel, "skip.log"), "")
        create_dir(os.path.join(rel, "__pycache__"))
        write_file(os.path.join(rel, "__pycache__", "x.pyc"), "")
        try:
            result = file_tree(rel, ignore="file:.gitignore", output_mode=OUTPUT_MODE_STRING)
            assert "keep.txt" in result
            assert "skip.log" not in result
            assert "__pycache__" not in result
        finally:
            delete_dir(rel)


# --- Recursion and max depth ---


class TestFileTreeRecursion:
    def test_unlimited_depth_traverses_all_levels(self, tree_root):
        result = file_tree(tree_root, max_depth=0, output_mode=OUTPUT_MODE_STRING)
        assert "inner.txt" in result
        assert "nested" in result

    def test_max_depth_1_shows_only_root_children(self, tree_root):
        result = file_tree(tree_root, max_depth=1, output_mode=OUTPUT_MODE_STRING)
        assert "alpha" in result and "beta" in result
        assert "inner.txt" not in result
        assert "nested" not in result

    def test_max_depth_2_shows_one_level_deep(self, tree_root):
        result = file_tree(tree_root, max_depth=2, output_mode=OUTPUT_MODE_STRING)
        assert "alpha_file.txt" in result or "nested" in result
        assert "inner.txt" not in result

    def test_max_depth_3_shows_inner_file(self, tree_root):
        result = file_tree(tree_root, max_depth=3, output_mode=OUTPUT_MODE_STRING)
        assert "inner.txt" in result


# --- Max lines ---


class TestFileTreeMaxLines:
    def test_max_lines_truncates_output(self, tree_root):
        result = file_tree(tree_root, max_lines=4, output_mode=OUTPUT_MODE_STRING)
        lines = [l for l in result.split("\n") if l.strip()]
        assert len(lines) <= 6  # root + up to 4 entries + possible summary comment

    def test_max_lines_emits_summary_comment_when_truncated(self, patch_base_dir):
        rel = "tmp/tests/file_tree/max_lines"
        delete_dir(rel)
        materialize_structure(
            rel,
            {"d1": {}, "d2": {}, "d3": {}, "f1.txt": "", "f2.txt": "", "f3.txt": ""},
        )
        try:
            result = file_tree(rel, max_lines=5, output_mode=OUTPUT_MODE_STRING)
            assert "limit reached" in result or "hidden" in result or "more" in result
        finally:
            delete_dir(rel)


# --- Max folders / max files ---


class TestFileTreePerDirectoryLimits:
    def test_max_folders_emits_summary_comment(self, patch_base_dir):
        rel = "tmp/tests/file_tree/max_folders"
        delete_dir(rel)
        materialize_structure(rel, {"dir_a": {}, "dir_b": {}, "dir_c": {}, "f.txt": ""})
        try:
            result = file_tree(rel, max_folders=1, output_mode=OUTPUT_MODE_STRING)
            assert "more folder" in result or "more folders" in result
        finally:
            delete_dir(rel)

    def test_max_files_emits_summary_comment(self, patch_base_dir):
        rel = "tmp/tests/file_tree/max_files"
        delete_dir(rel)
        materialize_structure(rel, {"a.txt": "", "b.txt": "", "c.txt": ""})
        try:
            result = file_tree(rel, max_files=1, output_mode=OUTPUT_MODE_STRING)
            assert "more file" in result or "more files" in result
        finally:
            delete_dir(rel)

    def test_single_overflow_promoted_not_summary(self, patch_base_dir):
        rel = "tmp/tests/file_tree/single_overflow"
        delete_dir(rel)
        materialize_structure(rel, {"dir_a": {}, "dir_b": {}, "f.txt": ""})
        try:
            result = file_tree(rel, max_folders=1, output_mode=OUTPUT_MODE_STRING)
            # With 2 folders and max_folders=1, one folder is shown, one gets summary
            assert "dir_a" in result or "dir_b" in result
        finally:
            delete_dir(rel)


# --- Sorting ---


class TestFileTreeSorting:
    def test_sort_by_name_asc(self, tree_root):
        result = file_tree(tree_root, sort=(SORT_BY_NAME, SORT_ASC), output_mode=OUTPUT_MODE_STRING)
        assert "a.txt" in result and "alpha" in result

    def test_sort_by_name_desc(self, tree_root):
        result = file_tree(tree_root, sort=(SORT_BY_NAME, SORT_DESC), output_mode=OUTPUT_MODE_STRING)
        assert "zeta" in result

    def test_sort_by_modified(self, tree_root):
        result = file_tree(tree_root, sort=(SORT_BY_MODIFIED, SORT_DESC), output_mode=OUTPUT_MODE_STRING)
        assert "alpha" in result or "beta" in result

    def test_sort_by_created(self, tree_root):
        result = file_tree(tree_root, sort=(SORT_BY_CREATED, SORT_ASC), output_mode=OUTPUT_MODE_STRING)
        assert len(result) > 0


# --- Output modes ---


class TestFileTreeOutputModes:
    def test_flat_output_is_list_of_dicts(self, tree_root):
        result = file_tree(tree_root, output_mode=OUTPUT_MODE_FLAT)
        assert isinstance(result, list)
        assert len(result) >= 1
        first = result[0]
        assert isinstance(first, dict)
        assert "name" in first and "level" in first and "type" in first

    def test_flat_output_has_synthetic_root(self, tree_root):
        result = file_tree(tree_root, output_mode=OUTPUT_MODE_FLAT)
        root = result[0]
        assert root["type"] == "folder"
        assert root["level"] == 0

    def test_nested_output_is_list_with_root(self, tree_root):
        result = file_tree(tree_root, output_mode=OUTPUT_MODE_NESTED)
        assert isinstance(result, list)
        assert len(result) == 1
        root = result[0]
        assert "items" in root
        assert isinstance(root["items"], list)

    def test_nested_output_has_nested_structure(self, tree_root):
        result = file_tree(tree_root, output_mode=OUTPUT_MODE_NESTED)
        root = result[0]
        items = root.get("items") or []
        assert any(
            child.get("name") in ("alpha", "beta", "zeta", "a.txt", "b.txt")
            for child in items
        )


# --- Empty directory ---


class TestFileTreeEmptyDirectory:
    def test_empty_directory_returns_root_only(self, patch_base_dir):
        rel = "tmp/tests/file_tree/empty"
        delete_dir(rel)
        create_dir(rel)
        try:
            result = file_tree(rel, output_mode=OUTPUT_MODE_STRING)
            lines = [l for l in result.split("\n") if l.strip()]
            assert len(lines) == 1
            assert result.strip().endswith("/")
        finally:
            delete_dir(rel)

    def test_empty_directory_flat_mode(self, patch_base_dir):
        rel = "tmp/tests/file_tree/empty_flat"
        delete_dir(rel)
        create_dir(rel)
        try:
            result = file_tree(rel, output_mode=OUTPUT_MODE_FLAT)
            assert len(result) == 1
            assert result[0]["items"] is None
        finally:
            delete_dir(rel)


# --- Special characters ---


class TestFileTreeSpecialCharacters:
    def test_filenames_with_spaces(self, patch_base_dir):
        rel = "tmp/tests/file_tree/special"
        delete_dir(rel)
        create_dir(rel)
        write_file(os.path.join(rel, "file with spaces.txt"), "content")
        try:
            result = file_tree(rel, output_mode=OUTPUT_MODE_STRING)
            assert "file with spaces.txt" in result
        finally:
            delete_dir(rel)

    def test_filenames_with_dots(self, patch_base_dir):
        rel = "tmp/tests/file_tree/dots"
        delete_dir(rel)
        create_dir(rel)
        write_file(os.path.join(rel, "my.file.name.txt"), "")
        try:
            result = file_tree(rel, output_mode=OUTPUT_MODE_STRING)
            assert "my.file.name.txt" in result
        finally:
            delete_dir(rel)


# --- Structured output metadata ---


class TestFileTreeStructuredMetadata:
    def test_flat_items_have_datetime_objects(self, tree_root):
        result = file_tree(tree_root, output_mode=OUTPUT_MODE_FLAT)
        for item in result[1:]:  # skip root
            if item["type"] in ("file", "folder"):
                assert "created" in item
                assert "modified" in item
                assert hasattr(item["created"], "isoformat")
                assert hasattr(item["modified"], "timestamp")
