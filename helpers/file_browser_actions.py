"""Local Files actions with exclusive publication and recoverable removal."""
import errno
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
import uuid

from helpers import file_connections, files
from helpers.file_archives import create_selected_zip
from helpers.file_browser import FileBrowser, rename_no_replace


def local_entry(path):
    if not isinstance(path, str) or not path.startswith("/") or file_connections.is_remote(path):
        raise ValueError("Choose an item on the local filesystem.")
    return FileBrowser()._entry_path(path)


def compress(paths, directory, name):
    directory = Path(directory).resolve(strict=True)
    if not isinstance(name, str) or name in ("", ".", "..") or "/" in name or "\\" in name:
        raise ValueError("Enter an archive filename.")
    target = directory / (name if name.lower().endswith(".zip") else name + ".zip")
    sources = [local_entry(path) for path in paths]
    for source in sources:
        if source.parent != directory or source.is_symlink() or not source.exists():
            raise ValueError("Choose existing files and folders in the current directory.")
    temporary = Path(create_selected_zip([str(source) for source in sources], str(directory),
                                         FileBrowser.max_file_bytes(), FileBrowser.max_archive_entries()))
    try:
        with tempfile.TemporaryDirectory(prefix=".a0-zip-", dir=directory) as staging:
            staged = Path(staging) / "archive"
            shutil.move(temporary, staged)
            rename_no_replace(staged, target)
    finally:
        temporary.unlink(missing_ok=True)
    return str(target)


def trash_root():
    return Path(files.get_abs_path("usr", "trash"))


def trash_item(action, value):
    root = trash_root()
    if root.is_symlink():
        raise ValueError("The Trash location must be a directory.")
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    if action == "trash":
        source = local_entry(value)
        if source.is_relative_to(root) or root.is_relative_to(source):
            raise ValueError("The Trash location cannot be moved into itself.")
        entry = root / uuid.uuid4().hex
        entry.mkdir(mode=0o700)
        try:
            (entry / "original.json").write_text(json.dumps(str(source)), encoding="utf-8")
            rename_no_replace(source, entry / "item")
        except BaseException as error:
            (entry / "original.json").unlink(missing_ok=True)
            entry.rmdir()
            if isinstance(error, OSError) and error.errno == errno.EXDEV:
                raise ValueError("This item is on a different filesystem from Trash. Use Move to or Delete permanently.") from error
            raise
        return str(source)
    if action not in ("restore", "purge") or not isinstance(value, str) or not re.fullmatch("[0-9a-f]{32}", value):
        raise ValueError("Invalid Trash item.")
    entry = root / value
    if entry.is_symlink():
        raise ValueError("Invalid Trash item.")
    original = local_entry(json.loads((entry / "original.json").read_text(encoding="utf-8")))
    item = entry / "item"
    if action == "restore":
        rename_no_replace(item, original)
    elif not item.is_symlink() and item.is_dir():
        shutil.rmtree(item)
    else:
        item.unlink()
    (entry / "original.json").unlink()
    entry.rmdir()
    return str(original)


def list_trash():
    root = trash_root()
    if not root.exists():
        return []
    if root.is_symlink():
        raise ValueError("Invalid Trash location.")
    entries = []
    for entry in root.iterdir():
        if entry.is_symlink() or not re.fullmatch("[0-9a-f]{32}", entry.name):
            continue
        try:
            if os.path.lexists(entry / "item"):
                path = json.loads((entry / "original.json").read_text(encoding="utf-8"))
                entries.append({"id": entry.name, "path": path, "time": entry.stat().st_mtime})
        except FileNotFoundError:
            continue
    return sorted(entries, key=lambda item: item["time"], reverse=True)
