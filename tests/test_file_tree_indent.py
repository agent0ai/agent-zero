from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from helpers.file_tree import OUTPUT_MODE_INDENT, file_tree
from helpers.files import create_dir, delete_dir, write_file


BASE_TEMP = "tmp/tests/file_tree/indent"


@pytest.fixture()
def tree_root():
    rel = BASE_TEMP
    delete_dir(rel)
    create_dir(rel)
    write_file(os.path.join(rel, "top_file.txt"), "a")
    create_dir(os.path.join(rel, "sub"))
    write_file(os.path.join(rel, "sub", "nested.txt"), "b")
    create_dir(os.path.join(rel, "sub", "deep"))
    write_file(os.path.join(rel, "sub", "deep", "leaf.txt"), "c")
    yield rel
    delete_dir(rel)


def test_indent_mode_returns_compact_indented_string(tree_root):
    result = file_tree(tree_root, max_depth=5, output_mode=OUTPUT_MODE_INDENT)
    assert isinstance(result, str)
    lines = result.splitlines()
    # root line ends with path separator and contains the relative path
    assert lines[0].endswith("/")
    assert tree_root in lines[0]
    # top-level file has no indent (folders_first default puts sub/ first)
    file_line = next(line for line in lines if line.lstrip().startswith("top_file.txt"))
    assert file_line.startswith("    ") is False
    # nested file uses 4-space indent per level
    nested_line = next(line for line in lines if line.lstrip().startswith("nested.txt"))
    assert nested_line.startswith("    " * 1)
    leaf_line = next(line for line in lines if line.lstrip().startswith("leaf.txt"))
    assert leaf_line.startswith("    " * 2)


def test_indent_mode_marks_folders_with_trailing_slash(tree_root):
    result = file_tree(tree_root, max_depth=5, output_mode=OUTPUT_MODE_INDENT)
    lines = result.splitlines()
    folder_lines = [line for line in lines if line.rstrip().endswith("/")]
    assert any("sub/" in line for line in folder_lines)
    assert any("deep/" in line for line in folder_lines)


def test_indent_mode_rejects_unknown_output_mode(tree_root):
    with pytest.raises(ValueError):
        file_tree(tree_root, output_mode="bogus")