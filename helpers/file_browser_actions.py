"""Local Files actions with exclusive publication and recoverable removal."""
import errno
import json
import os
from pathlib import Path
import re
import shutil
import stat
import tempfile
import uuid

from helpers import file_connections, files
from helpers.file_archives import create_selected_zip
from helpers.file_browser import FileBrowser, rename_no_replace


def local_entry(path):
    if not isinstance(path, str) or not path.startswith("/") or file_connections.is_remote(path):
        raise ValueError("Choose an item on the local filesystem.")
    return FileBrowser()._entry_path(path)


def properties(paths):
    entries = []
    for value in dict.fromkeys(paths):
        path = Path("/") if value == "/" else local_entry(value)
        info = path.lstat()
        link = stat.S_ISLNK(info.st_mode)
        entries.append({
            "name": path.name or "/", "path": str(path), "size": info.st_size,
            "is_dir": stat.S_ISDIR(info.st_mode), "is_symlink": link,
            "symlink_target": os.readlink(path) if link else None,
            "mode": format(stat.S_IMODE(info.st_mode), "03o"),
            "uid": info.st_uid, "gid": info.st_gid,
            "modified": info.st_mtime * 1000, "accessed": info.st_atime * 1000,
            "changed": info.st_ctime * 1000,
        })
    return entries


def selection_size(paths):
    def fail(error):
        raise error

    total = 0
    for entry in properties(paths):
        if not entry["is_dir"]:
            total += entry["size"]
            continue
        for _, directories, files_in_dir, fd in os.fwalk(entry["path"], onerror=fail):
            for name in directories + files_in_dir:
                info = os.stat(name, dir_fd=fd, follow_symlinks=False)
                if not stat.S_ISDIR(info.st_mode):
                    total += info.st_size
    return total


def change_permissions(value, mode):
    if not isinstance(mode, str) or not re.fullmatch("[0-7]{3,4}", mode):
        raise ValueError("Enter three or four octal digits (0–7).")
    path = local_entry(value)
    # Pin the inode without requiring read permission or following the final link.
    fd = os.open(path, os.O_PATH | os.O_NOFOLLOW)
    try:
        kind = os.fstat(fd).st_mode
        if not (stat.S_ISREG(kind) or stat.S_ISDIR(kind)):
            raise ValueError("Permissions can only be changed on files and folders.")
        os.chmod(f"/proc/self/fd/{fd}", int(mode, 8))
    finally:
        os.close(fd)
    return str(path)


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
