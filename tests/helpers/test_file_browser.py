"""Comprehensive unit tests for python/helpers/file_browser.py."""

import base64
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# --- Fixtures ---


@pytest.fixture
def file_browser(tmp_workdir):
    """FileBrowser instance with base_dir set to tmp_workdir."""
    with patch("python.helpers.file_browser.PrintStyle") as mock_style:
        mock_style.error = MagicMock()
        mock_style.warning = MagicMock()
        from python.helpers.file_browser import FileBrowser

        browser = FileBrowser()
        browser.base_dir = Path(tmp_workdir)
        yield browser


@pytest.fixture
def populated_workdir(tmp_workdir):
    """Create a populated directory structure for browsing tests."""
    (tmp_workdir / "subdir").mkdir()
    (tmp_workdir / "subdir" / "nested").mkdir()
    (tmp_workdir / "subdir" / "nested" / "deep.txt").write_text("deep content")
    (tmp_workdir / "subdir" / "inner.txt").write_text("inner")
    (tmp_workdir / "a.txt").write_text("a")
    (tmp_workdir / "b.txt").write_text("b")
    (tmp_workdir / "readme.md").write_text("# Readme")
    (tmp_workdir / "data.json").write_text("{}")
    return tmp_workdir


# --- Browsing ---


class TestFileBrowserGetFiles:
    def test_get_files_root_returns_entries(self, file_browser, populated_workdir):
        result = file_browser.get_files("")
        assert "entries" in result
        assert "current_path" in result
        assert "parent_path" in result
        assert result["current_path"] == ""
        assert result["parent_path"] == ""

    def test_get_files_lists_folders_first(self, file_browser, populated_workdir):
        result = file_browser.get_files("")
        entries = result["entries"]
        folders = [e for e in entries if e.get("is_dir")]
        files_list = [e for e in entries if not e.get("is_dir")]
        assert all(f["type"] == "folder" for f in folders)
        assert all(not f["is_dir"] for f in files_list)
        folder_indices = [entries.index(f) for f in folders]
        file_indices = [entries.index(f) for f in files_list]
        if folder_indices and file_indices:
            assert max(folder_indices) < min(file_indices)

    def test_get_files_subdir(self, file_browser, populated_workdir):
        result = file_browser.get_files("subdir")
        assert result["current_path"] == "subdir"
        assert result["parent_path"] == ""
        entries = result["entries"]
        names = [e["name"] for e in entries]
        assert "inner.txt" in names
        assert "nested" in names

    def test_get_files_nested_subdir(self, file_browser, populated_workdir):
        result = file_browser.get_files("subdir/nested")
        assert result["current_path"] == "subdir/nested"
        assert result["parent_path"] == "subdir"
        entries = result["entries"]
        names = [e["name"] for e in entries]
        assert "deep.txt" in names

    def test_get_files_empty_dir(self, file_browser, tmp_workdir):
        (tmp_workdir / "empty_folder").mkdir()
        result = file_browser.get_files("empty_folder")
        assert result["entries"] == []
        assert result["current_path"] == "empty_folder"

    def test_get_files_invalid_path_returns_empty(self, file_browser, tmp_workdir):
        result = file_browser.get_files("../../../etc")
        assert result["entries"] == []
        assert result["current_path"] == ""
        assert result["parent_path"] == ""


# --- Path resolution ---


class TestFileBrowserPathResolution:
    def test_get_full_path_returns_absolute_path(self, file_browser, populated_workdir):
        full = file_browser.get_full_path("a.txt")
        assert os.path.isabs(full)
        assert full.endswith("a.txt")
        assert os.path.exists(full)

    def test_get_full_path_subdir_file(self, file_browser, populated_workdir):
        full = file_browser.get_full_path("subdir/inner.txt")
        assert os.path.isabs(full)
        assert "inner.txt" in full
        assert os.path.exists(full)

    def test_get_full_path_raises_when_not_found(self, file_browser, tmp_workdir):
        with pytest.raises(ValueError, match="not found"):
            file_browser.get_full_path("nonexistent.txt")

    def test_get_full_path_raises_for_nonexistent_in_subpath(self, file_browser, tmp_workdir):
        (tmp_workdir / "sub").mkdir()
        with pytest.raises(ValueError, match="not found"):
            file_browser.get_full_path("sub/nonexistent.txt")


# --- Save operations ---


class TestFileBrowserSaveOperations:
    def test_save_file_b64_creates_file(self, file_browser, tmp_workdir):
        content = base64.b64encode(b"hello world").decode("utf-8")
        result = file_browser.save_file_b64("", "test.txt", content)
        assert result is True
        path = tmp_workdir / "test.txt"
        assert path.exists()
        assert path.read_bytes() == b"hello world"

    def test_save_file_b64_in_subdir(self, file_browser, tmp_workdir):
        (tmp_workdir / "sub").mkdir()
        content = base64.b64encode(b"data").decode("utf-8")
        result = file_browser.save_file_b64("sub", "file.bin", content)
        assert result is True
        assert (tmp_workdir / "sub" / "file.bin").exists()

    def test_save_file_b64_rejects_traversal(self, file_browser, tmp_workdir):
        content = base64.b64encode(b"x").decode("utf-8")
        result = file_browser.save_file_b64("../../../tmp", "evil.txt", content)
        assert result is False

    def test_save_text_file_creates_file(self, file_browser, tmp_workdir):
        result = file_browser.save_text_file("doc.txt", "Hello, world!")
        assert result is True
        assert (tmp_workdir / "doc.txt").read_text() == "Hello, world!"

    def test_save_text_file_in_subdir(self, file_browser, tmp_workdir):
        (tmp_workdir / "docs").mkdir()
        result = file_browser.save_text_file("docs/note.md", "# Note")
        assert result is True
        assert (tmp_workdir / "docs" / "note.md").read_text() == "# Note"

    def test_save_text_file_rejects_non_string(self, file_browser, tmp_workdir):
        with pytest.raises(ValueError, match="Content must be a string"):
            file_browser.save_text_file("x.txt", 123)

    def test_save_text_file_rejects_oversized(self, file_browser, tmp_workdir):
        large = "x" * (2 * 1024 * 1024)  # 2MB
        with pytest.raises(ValueError, match="1 MB"):
            file_browser.save_text_file("big.txt", large)


# --- Delete ---


class TestFileBrowserDelete:
    def test_delete_file_removes_file(self, file_browser, tmp_workdir):
        (tmp_workdir / "to_delete.txt").write_text("x")
        result = file_browser.delete_file("to_delete.txt")
        assert result is True
        assert not (tmp_workdir / "to_delete.txt").exists()

    def test_delete_empty_dir(self, file_browser, tmp_workdir):
        (tmp_workdir / "empty_dir").mkdir()
        result = file_browser.delete_file("empty_dir")
        assert result is True
        assert not (tmp_workdir / "empty_dir").exists()

    def test_delete_dir_with_contents(self, file_browser, tmp_workdir):
        (tmp_workdir / "dir_with_files").mkdir()
        (tmp_workdir / "dir_with_files" / "f.txt").write_text("x")
        result = file_browser.delete_file("dir_with_files")
        assert result is True
        assert not (tmp_workdir / "dir_with_files").exists()

    def test_delete_nonexistent_returns_false(self, file_browser, tmp_workdir):
        result = file_browser.delete_file("nonexistent.txt")
        assert result is False

    def test_delete_rejects_traversal(self, file_browser, tmp_workdir):
        result = file_browser.delete_file("../../../etc/passwd")
        assert result is False


# --- Rename ---


class TestFileBrowserRename:
    def test_rename_file(self, file_browser, tmp_workdir):
        (tmp_workdir / "old.txt").write_text("content")
        result = file_browser.rename_item("old.txt", "new.txt")
        assert result is True
        assert not (tmp_workdir / "old.txt").exists()
        assert (tmp_workdir / "new.txt").read_text() == "content"

    def test_rename_folder(self, file_browser, tmp_workdir):
        (tmp_workdir / "old_dir").mkdir()
        (tmp_workdir / "old_dir" / "f.txt").write_text("x")
        result = file_browser.rename_item("old_dir", "new_dir")
        assert result is True
        assert not (tmp_workdir / "old_dir").exists()
        assert (tmp_workdir / "new_dir" / "f.txt").exists()

    def test_rename_rejects_invalid_name_dot(self, file_browser, tmp_workdir):
        (tmp_workdir / "f.txt").write_text("x")
        with pytest.raises(ValueError, match="Invalid new name"):
            file_browser.rename_item("f.txt", ".")

    def test_rename_rejects_path_separator_in_name(self, file_browser, tmp_workdir):
        (tmp_workdir / "f.txt").write_text("x")
        with pytest.raises(ValueError, match="path separators"):
            file_browser.rename_item("f.txt", "a/b.txt")

    def test_rename_rejects_empty_name(self, file_browser, tmp_workdir):
        (tmp_workdir / "f.txt").write_text("x")
        with pytest.raises(ValueError, match="Invalid new name"):
            file_browser.rename_item("f.txt", "")

    def test_rename_same_name_returns_true(self, file_browser, tmp_workdir):
        (tmp_workdir / "same.txt").write_text("x")
        result = file_browser.rename_item("same.txt", "same.txt")
        assert result is True


# --- Create folder ---


class TestFileBrowserCreateFolder:
    def test_create_folder(self, file_browser, tmp_workdir):
        result = file_browser.create_folder("", "new_folder")
        assert result is True
        assert (tmp_workdir / "new_folder").is_dir()

    def test_create_folder_in_subdir(self, file_browser, tmp_workdir):
        (tmp_workdir / "parent").mkdir()
        result = file_browser.create_folder("parent", "child")
        assert result is True
        assert (tmp_workdir / "parent" / "child").is_dir()

    def test_create_folder_rejects_invalid_name(self, file_browser, tmp_workdir):
        with pytest.raises(ValueError, match="Invalid folder name"):
            file_browser.create_folder("", ".")

    def test_create_folder_rejects_path_in_name(self, file_browser, tmp_workdir):
        with pytest.raises(ValueError, match="path separators"):
            file_browser.create_folder("", "a/b")

    def test_create_folder_raises_when_exists(self, file_browser, tmp_workdir):
        (tmp_workdir / "existing").mkdir()
        with pytest.raises(FileExistsError, match="already exists"):
            file_browser.create_folder("", "existing")


# --- Save files (upload) ---


class TestFileBrowserSaveFiles:
    def test_save_files_single_file(self, file_browser, tmp_workdir):
        mock_file = MagicMock()
        mock_file.filename = "uploaded.txt"
        mock_file.save = MagicMock(side_effect=lambda path: Path(path).write_text("uploaded"))

        def safe_fn(name):
            return name

        with patch("python.helpers.file_browser.safe_filename", side_effect=safe_fn):
            success, failed = file_browser.save_files([mock_file], "")
        assert "uploaded.txt" in success
        assert failed == []
        assert (tmp_workdir / "uploaded.txt").read_text() == "uploaded"

    def test_save_files_in_subdir(self, file_browser, tmp_workdir):
        (tmp_workdir / "uploads").mkdir()
        mock_file = MagicMock()
        mock_file.filename = "data.csv"
        mock_file.save = MagicMock(side_effect=lambda path: Path(path).write_text("csv,data"))

        def safe_fn(name):
            return name

        with patch("python.helpers.file_browser.safe_filename", side_effect=safe_fn):
            success, failed = file_browser.save_files([mock_file], "uploads")
        assert "data.csv" in success
        assert (tmp_workdir / "uploads" / "data.csv").read_text() == "csv,data"


# --- File type detection ---


class TestFileBrowserFileTypes:
    def test_get_files_includes_type_for_files(self, file_browser, populated_workdir):
        result = file_browser.get_files("")
        files_list = [e for e in result["entries"] if not e.get("is_dir")]
        for f in files_list:
            assert "type" in f
            assert f["type"] in ("image", "code", "document", "folder", "unknown")

    def test_image_extension_detected(self, file_browser, tmp_workdir):
        (tmp_workdir / "photo.png").write_bytes(b"\x89PNG")
        result = file_browser.get_files("")
        files_list = [e for e in result["entries"] if e["name"] == "photo.png"]
        assert len(files_list) == 1
        assert files_list[0]["type"] == "image"

    def test_code_extension_detected(self, file_browser, tmp_workdir):
        (tmp_workdir / "script.py").write_text("print(1)")
        result = file_browser.get_files("")
        files_list = [e for e in result["entries"] if e["name"] == "script.py"]
        assert len(files_list) == 1
        assert files_list[0]["type"] == "code"


# --- Constants ---


class TestFileBrowserConstants:
    def test_allowed_extensions_defined(self):
        from python.helpers.file_browser import FileBrowser

        assert "image" in FileBrowser.ALLOWED_EXTENSIONS
        assert "code" in FileBrowser.ALLOWED_EXTENSIONS
        assert "document" in FileBrowser.ALLOWED_EXTENSIONS
        assert "jpg" in FileBrowser.ALLOWED_EXTENSIONS["image"]
        assert "py" in FileBrowser.ALLOWED_EXTENSIONS["code"]

    def test_max_file_size_defined(self):
        from python.helpers.file_browser import FileBrowser

        assert FileBrowser.MAX_FILE_SIZE == 100 * 1024 * 1024

    def test_max_text_file_size_defined(self):
        from python.helpers.file_browser import FileBrowser

        assert FileBrowser.MAX_TEXT_FILE_SIZE == 1 * 1024 * 1024
