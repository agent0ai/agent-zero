"""Filesystem-sourced zip writers must tolerate mtimes outside the ZIP range.

Package registries (cargo, npm, pip) extract entries with an epoch-zero mtime.
``zipfile`` refuses those timestamps by default, which aborted the whole
operation. Backups and the self-update archive already clamp with
``strict_timestamps=False``; the remaining zip writers do the same.
"""

import base64
import io
import os
import zipfile
from pathlib import Path

import pytest

from helpers import files, rfc_files
from helpers.file_archives import write_zip_entry


def _make_old_file(folder: Path) -> Path:
    source = folder / "old.txt"
    source.write_bytes(b"payload from an epoch-dated registry file")
    os.utime(source, (0, 0))
    assert source.stat().st_mtime == 0
    return source


def _read_entry(archive: zipfile.ZipFile, arcname: str) -> zipfile.ZipInfo:
    names = {info.filename.replace("\\", "/"): info for info in archive.infolist()}
    assert arcname in names, names.keys()
    return names[arcname]


def test_write_zip_entry_stores_pre_1980_mtime(tmp_path: Path):
    source = _make_old_file(tmp_path)
    zip_path = tmp_path / "out.zip"

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=True) as zipped:
        write_zip_entry(zipped, source, "old.txt")

    try:
        with zipfile.ZipFile(zip_path) as archive:
            assert archive.read("old.txt") == source.read_bytes()
            assert archive.getinfo("old.txt").date_time == (1980, 1, 1, 0, 0, 0)
    finally:
        zip_path.unlink(missing_ok=True)


def test_files_zip_dir_stores_pre_1980_mtime(tmp_path, monkeypatch):
    base = tmp_path / "base"
    folder = base / "folder"
    folder.mkdir(parents=True)
    _make_old_file(folder)
    monkeypatch.setattr(files, "_base_dir", str(base))

    zip_path = Path(files.zip_dir("folder"))
    try:
        with zipfile.ZipFile(zip_path) as archive:
            info = _read_entry(archive, "folder/old.txt")
            assert archive.read(info.filename) == b"payload from an epoch-dated registry file"
            assert info.date_time == (1980, 1, 1, 0, 0, 0)
    finally:
        zip_path.unlink(missing_ok=True)


def test_rfc_zip_directory_impl_stores_pre_1980_mtime(tmp_path: Path):
    folder = tmp_path / "folder"
    folder.mkdir()
    _make_old_file(folder)

    zip_path = Path(rfc_files._zip_dir_impl(str(folder)))
    try:
        with zipfile.ZipFile(zip_path) as archive:
            info = _read_entry(archive, "folder/old.txt")
            assert archive.read(info.filename) == b"payload from an epoch-dated registry file"
            assert info.date_time == (1980, 1, 1, 0, 0, 0)
    finally:
        zip_path.unlink(missing_ok=True)


def test_rfc_read_directory_impl_stores_pre_1980_mtime(tmp_path: Path):
    folder = tmp_path / "folder"
    folder.mkdir()
    source = _make_old_file(folder)

    b64_zip = rfc_files._read_directory_impl(str(folder))
    with zipfile.ZipFile(io.BytesIO(base64.b64decode(b64_zip))) as archive:
        info = _read_entry(archive, "old.txt")
        assert archive.read(info.filename) == source.read_bytes()
        assert info.date_time == (1980, 1, 1, 0, 0, 0)


def test_write_zip_entry_still_raises_on_unreadable_files(tmp_path: Path):
    # A symlink is rejected as before; clamping timestamps must not relax other checks.
    target = tmp_path / "real.txt"
    target.write_bytes(b"payload")
    source = tmp_path / "link.txt"
    try:
        source.symlink_to(target)
    except OSError:
        pytest.skip("symlinks not available")
    with zipfile.ZipFile(tmp_path / "out.zip", "w") as zipped:
        with pytest.raises(ValueError, match="symbolic link"):
            write_zip_entry(zipped, source, "link.txt")
