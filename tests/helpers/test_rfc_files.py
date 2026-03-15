"""Tests for python/helpers/rfc_files.py."""

import base64
import os
import sys
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# --- Fixtures ---


def _call_impl_directly(func, *args, **kwargs):
    """Bypass RFC routing and call the implementation function directly."""
    return func(*args, **kwargs)


@pytest.fixture
def patch_rfc_runtime(tmp_workdir):
    """Patch runtime to call impl functions directly and use tmp_workdir as base."""
    with patch(
        "python.helpers.rfc_files.runtime.call_development_function_sync",
        side_effect=_call_impl_directly,
    ):
        with patch(
            "python.helpers.rfc_files.get_abs_path",
            side_effect=lambda *parts: str(tmp_workdir.joinpath(*[str(p) for p in parts])) if parts else str(tmp_workdir),
        ):
            yield tmp_workdir


@pytest.fixture
def patch_rfc_for_impl_tests(tmp_workdir):
    """Patch get_abs_path so RFC public API uses tmp_workdir; impl tests use real paths."""
    def _get_abs_path(*relative_paths):
        if not relative_paths:
            return str(tmp_workdir)
        return str(tmp_workdir.joinpath(*[str(p) for p in relative_paths]))

    with patch("python.helpers.rfc_files.get_abs_path", side_effect=_get_abs_path):
        with patch(
            "python.helpers.rfc_files.runtime.call_development_function_sync",
            side_effect=_call_impl_directly,
        ):
            yield tmp_workdir


# --- get_abs_path ---


class TestGetAbsPath:
    def test_get_abs_path_empty_returns_base_dir(self):
        from python.helpers.rfc_files import get_abs_path

        result = get_abs_path()
        assert os.path.isabs(result)
        assert "agent-zero" in result

    def test_get_abs_path_joins_parts(self):
        from python.helpers.rfc_files import get_abs_path

        result = get_abs_path("a", "b", "c.txt")
        assert result.endswith(os.path.join("a", "b", "c.txt"))


# --- Implementation functions (tested via patched runtime) ---


class TestReadFileBin:
    def test_read_file_bin_returns_content(self, patch_rfc_for_impl_tests):
        from python.helpers.rfc_files import read_file_bin

        p = patch_rfc_for_impl_tests / "work_dir" / "test.bin"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"binary content\x00\x01")

        result = read_file_bin("work_dir/test.bin")
        assert result == b"binary content\x00\x01"

    def test_read_file_bin_with_backup_dirs(self, patch_rfc_for_impl_tests):
        from python.helpers.rfc_files import read_file_bin

        backup = patch_rfc_for_impl_tests / "backup"
        backup.mkdir()
        (backup / "work_dir").mkdir()
        (backup / "work_dir" / "alt.txt").write_bytes(b"from backup")

        result = read_file_bin("work_dir/alt.txt", backup_dirs=[str(backup)])
        assert result == b"from backup"

    def test_read_file_bin_raises_when_not_found(self, patch_rfc_for_impl_tests):
        from python.helpers.rfc_files import read_file_bin

        with pytest.raises(FileNotFoundError, match="not found"):
            read_file_bin("nonexistent/file.bin")


class TestReadFileBase64:
    def test_read_file_base64_returns_encoded_string(self, patch_rfc_for_impl_tests):
        from python.helpers.rfc_files import read_file_base64

        p = patch_rfc_for_impl_tests / "work_dir" / "data.bin"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"hello")

        result = read_file_base64("work_dir/data.bin")
        assert result == base64.b64encode(b"hello").decode("utf-8")


class TestWriteFileBinary:
    def test_write_file_binary_creates_file(self, patch_rfc_for_impl_tests):
        from python.helpers.rfc_files import read_file_bin, write_file_binary

        write_file_binary("work_dir/out.bin", b"written content")
        result = read_file_bin("work_dir/out.bin")
        assert result == b"written content"

    def test_write_file_binary_creates_parent_dirs(self, patch_rfc_for_impl_tests):
        from python.helpers.rfc_files import read_file_bin, write_file_binary

        write_file_binary("work_dir/sub1/sub2/file.bin", b"nested")
        result = read_file_bin("work_dir/sub1/sub2/file.bin")
        assert result == b"nested"


class TestWriteFileBase64:
    def test_write_file_base64_decodes_and_writes(self, patch_rfc_for_impl_tests):
        from python.helpers.rfc_files import read_file_bin, write_file_base64

        encoded = base64.b64encode(b"base64 content").decode("utf-8")
        write_file_base64("work_dir/b64.bin", encoded)
        result = read_file_bin("work_dir/b64.bin")
        assert result == b"base64 content"


class TestDeleteFile:
    def test_delete_file_removes_file(self, patch_rfc_for_impl_tests):
        from python.helpers.rfc_files import delete_file, file_exists, write_file_binary

        write_file_binary("work_dir/to_delete.bin", b"x")
        assert file_exists("work_dir/to_delete.bin")
        result = delete_file("work_dir/to_delete.bin")
        assert result is True
        assert not file_exists("work_dir/to_delete.bin")

    def test_delete_file_raises_for_nonexistent(self, patch_rfc_for_impl_tests):
        from python.helpers.rfc_files import delete_file

        with pytest.raises(FileNotFoundError, match="not found"):
            delete_file("work_dir/nonexistent.bin")


class TestDeleteDirectory:
    def test_delete_directory_removes_recursively(self, patch_rfc_for_impl_tests):
        from python.helpers.rfc_files import delete_directory, folder_exists, write_file_binary

        write_file_binary("work_dir/subdir/file.txt", b"x")
        assert folder_exists("work_dir/subdir")
        result = delete_directory("work_dir/subdir")
        assert result is True
        assert not folder_exists("work_dir/subdir")

    def test_delete_directory_raises_for_nonexistent(self, patch_rfc_for_impl_tests):
        from python.helpers.rfc_files import delete_directory

        with pytest.raises(FileNotFoundError, match="Folder not found"):
            delete_directory("work_dir/nonexistent_folder")


class TestListDirectory:
    def test_list_directory_returns_items(self, patch_rfc_for_impl_tests):
        from python.helpers.rfc_files import list_directory, write_file_binary

        write_file_binary("work_dir/a.txt", b"a")
        write_file_binary("work_dir/b.txt", b"b")
        (patch_rfc_for_impl_tests / "work_dir" / "subdir").mkdir()

        result = list_directory("work_dir")
        names = [item["name"] for item in result]
        assert "a.txt" in names
        assert "b.txt" in names
        assert "subdir" in names
        assert all("is_file" in item and "is_dir" in item for item in result)

    def test_list_directory_excludes_hidden_by_default(self, patch_rfc_for_impl_tests):
        from python.helpers.rfc_files import list_directory

        (patch_rfc_for_impl_tests / "work_dir").mkdir(exist_ok=True)
        (patch_rfc_for_impl_tests / "work_dir" / ".hidden").write_bytes(b"x")
        (patch_rfc_for_impl_tests / "work_dir" / "visible").write_bytes(b"y")

        result = list_directory("work_dir", include_hidden=False)
        names = [item["name"] for item in result]
        assert ".hidden" not in names
        assert "visible" in names

    def test_list_directory_includes_hidden_when_requested(self, patch_rfc_for_impl_tests):
        from python.helpers.rfc_files import list_directory

        (patch_rfc_for_impl_tests / "work_dir").mkdir(exist_ok=True)
        (patch_rfc_for_impl_tests / "work_dir" / ".hidden").write_bytes(b"x")

        result = list_directory("work_dir", include_hidden=True)
        names = [item["name"] for item in result]
        assert ".hidden" in names


class TestMakeDirectories:
    def test_make_directories_creates_path(self, patch_rfc_for_impl_tests):
        from python.helpers.rfc_files import folder_exists, make_directories

        result = make_directories("work_dir/new/nested/path")
        assert result is True
        assert folder_exists("work_dir/new/nested/path")


class TestPathExists:
    def test_path_exists_true_for_file(self, patch_rfc_for_impl_tests):
        from python.helpers.rfc_files import path_exists, write_file_binary

        write_file_binary("work_dir/exists.bin", b"x")
        assert path_exists("work_dir/exists.bin") is True

    def test_path_exists_true_for_dir(self, patch_rfc_for_impl_tests):
        from python.helpers.rfc_files import path_exists

        (patch_rfc_for_impl_tests / "work_dir").mkdir(exist_ok=True)
        assert path_exists("work_dir") is True

    def test_path_exists_false_for_nonexistent(self, patch_rfc_for_impl_tests):
        from python.helpers.rfc_files import path_exists

        assert path_exists("work_dir/nonexistent") is False


class TestFileExists:
    def test_file_exists_true_for_file(self, patch_rfc_for_impl_tests):
        from python.helpers.rfc_files import file_exists, write_file_binary

        write_file_binary("work_dir/f.txt", b"x")
        assert file_exists("work_dir/f.txt") is True

    def test_file_exists_false_for_dir(self, patch_rfc_for_impl_tests):
        from python.helpers.rfc_files import file_exists

        (patch_rfc_for_impl_tests / "work_dir").mkdir(exist_ok=True)
        assert file_exists("work_dir") is False


class TestFolderExists:
    def test_folder_exists_true_for_dir(self, patch_rfc_for_impl_tests):
        from python.helpers.rfc_files import folder_exists

        (patch_rfc_for_impl_tests / "work_dir").mkdir(exist_ok=True)
        assert folder_exists("work_dir") is True

    def test_folder_exists_false_for_file(self, patch_rfc_for_impl_tests):
        from python.helpers.rfc_files import folder_exists, write_file_binary

        write_file_binary("work_dir/f.txt", b"x")
        assert folder_exists("work_dir/f.txt") is False


class TestGetSubdirectories:
    def test_get_subdirectories_with_include_pattern(self, patch_rfc_for_impl_tests):
        from python.helpers.rfc_files import get_subdirectories

        base = patch_rfc_for_impl_tests / "work_dir"
        base.mkdir(exist_ok=True)
        (base / "foo").mkdir()
        (base / "bar").mkdir()
        (base / "baz").mkdir()

        result = get_subdirectories("work_dir", include="f*")
        assert "foo" in result
        assert "bar" not in result
        assert "baz" not in result

    def test_get_subdirectories_with_exclude_pattern(self, patch_rfc_for_impl_tests):
        from python.helpers.rfc_files import get_subdirectories

        base = patch_rfc_for_impl_tests / "work_dir"
        base.mkdir(exist_ok=True)
        (base / "keep").mkdir()
        (base / "skip").mkdir()

        result = get_subdirectories("work_dir", include="*", exclude="skip")
        assert "keep" in result
        assert "skip" not in result

    def test_get_subdirectories_returns_empty_for_nonexistent(self, patch_rfc_for_impl_tests):
        from python.helpers.rfc_files import get_subdirectories

        result = get_subdirectories("work_dir/nonexistent")
        assert result == []


class TestZipDirectory:
    def test_zip_directory_creates_valid_zip(self, patch_rfc_for_impl_tests):
        from python.helpers.rfc_files import zip_directory

        base = patch_rfc_for_impl_tests / "work_dir"
        base.mkdir(exist_ok=True)
        (base / "a.txt").write_text("content a")
        (base / "sub").mkdir()
        (base / "sub" / "b.txt").write_text("content b")

        zip_path = zip_directory("work_dir")
        assert os.path.exists(zip_path)
        try:
            with zipfile.ZipFile(zip_path, "r") as z:
                names = z.namelist()
                assert any("a.txt" in n for n in names)
                assert any("b.txt" in n for n in names)
        finally:
            if os.path.exists(zip_path):
                os.unlink(zip_path)


class TestMoveFile:
    def test_move_file_relocates(self, patch_rfc_for_impl_tests):
        from python.helpers.rfc_files import file_exists, move_file, read_file_bin, write_file_binary

        write_file_binary("work_dir/source.txt", b"moved content")
        result = move_file("work_dir/source.txt", "work_dir/dest.txt")
        assert result is True
        assert not file_exists("work_dir/source.txt")
        assert file_exists("work_dir/dest.txt")
        assert read_file_bin("work_dir/dest.txt") == b"moved content"


class TestReadDirectoryAsZip:
    def test_read_directory_as_zip_returns_bytes(self, patch_rfc_for_impl_tests):
        from python.helpers.rfc_files import read_directory_as_zip

        base = patch_rfc_for_impl_tests / "work_dir"
        base.mkdir(exist_ok=True)
        (base / "f.txt").write_text("x")

        result = read_directory_as_zip("work_dir")
        assert isinstance(result, bytes)
        assert len(result) > 0
        with zipfile.ZipFile(__import__("io").BytesIO(result), "r") as z:
            assert len(z.namelist()) >= 1

    def test_read_directory_as_zip_raises_for_nonexistent(self, patch_rfc_for_impl_tests):
        from python.helpers.rfc_files import read_directory_as_zip

        with pytest.raises(FileNotFoundError, match="Directory not found"):
            read_directory_as_zip("work_dir/nonexistent")


class TestFindFileInDirs:
    def test_find_file_in_dirs_returns_main_path_first(self, patch_rfc_for_impl_tests):
        from python.helpers.rfc_files import find_file_in_dirs, write_file_binary

        write_file_binary("work_dir/found.txt", b"main")
        result = find_file_in_dirs("work_dir/found.txt", [])
        assert "found.txt" in result
        assert "work_dir" in result

    def test_find_file_in_dirs_falls_back_to_backup(self, patch_rfc_for_impl_tests):
        from python.helpers.rfc_files import find_file_in_dirs

        backup = patch_rfc_for_impl_tests / "backup"
        backup.mkdir()
        (backup / "work_dir").mkdir()
        (backup / "work_dir" / "alt.txt").write_bytes(b"backup")

        result = find_file_in_dirs("work_dir/alt.txt", [str(backup)])
        assert "backup" in result
        assert "alt.txt" in result

    def test_find_file_in_dirs_raises_when_not_found(self, patch_rfc_for_impl_tests):
        from python.helpers.rfc_files import find_file_in_dirs

        with pytest.raises(FileNotFoundError, match="File not found"):
            find_file_in_dirs("work_dir/missing.txt", [])


# --- Implementation edge cases ---


class TestImplEdgeCases:
    def test_read_file_binary_raises_for_directory(self, patch_rfc_for_impl_tests):
        from python.helpers.rfc_files import _read_file_binary_impl

        (patch_rfc_for_impl_tests / "work_dir").mkdir(exist_ok=True)
        path = str(patch_rfc_for_impl_tests / "work_dir")

        with pytest.raises(Exception, match="not a file"):
            _read_file_binary_impl(path)

    def test_write_file_binary_handles_empty_content(self, patch_rfc_for_impl_tests):
        from python.helpers.rfc_files import _read_file_binary_impl, _write_file_binary_impl

        path = str(patch_rfc_for_impl_tests / "work_dir" / "empty.bin")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        _write_file_binary_impl(path, base64.b64encode(b"").decode("utf-8"))
        result = _read_file_binary_impl(path)
        assert base64.b64decode(result) == b""
