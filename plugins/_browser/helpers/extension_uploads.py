"""Context-owned user attachment sources; never arbitrary tool-selected paths."""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import mimetypes
import os
from pathlib import Path
import re
import stat
import threading
import uuid

STORE_KEY = "browser_extension_upload_sources_v1"
MAX_BYTES = 25 * 1024 * 1024
MAX_SOURCES = 32
_source_lock = threading.RLock()
_MIME = re.compile(r"[A-Za-z0-9][A-Za-z0-9!#$&^_.+-]{0,126}/[A-Za-z0-9][A-Za-z0-9!#$&^_.+-]{0,126}")


class UploadSourceDenied(ValueError):
    def __init__(self):
        super().__init__("Upload source unavailable; attach the file to this chat again.")


def _root():
    from helpers import files
    return Path(files.get_abs_path("usr/uploads")).resolve()


def _relative(path, root):
    if not isinstance(path, str) or not path or len(path) > 4096 or "\x00" in path:
        raise UploadSourceDenied()
    from helpers import files
    actual = Path(files.fix_dev_path(path))
    try:
        relative = actual.relative_to(root)
    except ValueError:
        raise UploadSourceDenied() from None
    if not relative.parts or any(part in {"", ".", ".."} for part in relative.parts):
        raise UploadSourceDenied()
    return relative


def _read_exact(root: Path, relative: Path, expected=None):
    """Open each component relative to the retained root; reject link aliases."""
    if not hasattr(os, "O_NOFOLLOW"):
        raise UploadSourceDenied()
    directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    descriptor = None
    try:
        def check_directory(fd):
            info = os.fstat(fd)
            if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o022:
                raise UploadSourceDenied()
        check_directory(directory)
        for part in relative.parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
            os.close(directory)
            directory = child
            check_directory(directory)
        descriptor = os.open(relative.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        before = os.fstat(descriptor)
        identity = [before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns]
        if (not stat.S_ISREG(before.st_mode) or before.st_nlink != 1
            or before.st_uid != os.getuid() or before.st_mode & 0o022
            or not 1 <= before.st_size <= MAX_BYTES or (expected is not None and identity != expected)):
            raise UploadSourceDenied()
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            data = handle.read(MAX_BYTES + 1)
        after = os.fstat(descriptor)
        if identity != [after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns] or len(data) != before.st_size:
            raise UploadSourceDenied()
        return data, identity
    except (OSError, ValueError):
        raise UploadSourceDenied() from None
    finally:
        if descriptor is not None:
            os.close(descriptor)
        os.close(directory)


def record_user_attachments(context, paths, *, root=None):
    """Called only by the trusted user_message_ui hook after framework upload."""
    with _source_lock:
        _record_user_attachments(context, paths, root=root)


def _record_user_attachments(context, paths, *, root=None):
    if not isinstance(paths, list) or not paths:
        return
    root = root or _root()
    previous = context.get_data(STORE_KEY, recursive=False)
    records = list(previous) if isinstance(previous, list) and len(previous) <= MAX_SOURCES else []
    for path in paths[:MAX_SOURCES]:
        try:
            relative = _relative(path, root)
            data, identity = _read_exact(root, relative)
            mime = mimetypes.guess_type(relative.name)[0] or "application/octet-stream"
            if not _MIME.fullmatch(mime):
                mime = "application/octet-stream"
            record = {"context_id": str(context.id), "source": path, "relative": str(relative),
                      "identity": identity, "sha256": "sha256:" + hashlib.sha256(data).hexdigest(),
                      "mime_type": mime, "byte_count": len(data)}
            records = [item for item in records if isinstance(item, dict) and item.get("source") != path]
            records.append(record)
        except (UploadSourceDenied, OSError):
            continue  # Chat delivery is independent of optional browser upload support.
    context.set_data(STORE_KEY, records[-MAX_SOURCES:], recursive=False)


@dataclass(frozen=True, slots=True)
class PreparedUpload:
    context_id: str
    artifact_id: str
    mime_type: str
    byte_count: int
    sha256: str
    root: Path = field(repr=False)
    relative: Path = field(repr=False)
    identity: tuple[int, ...] = field(repr=False)

    def read(self) -> bytes:
        data, _ = _read_exact(self.root, self.relative, list(self.identity))
        if len(data) != self.byte_count or "sha256:" + hashlib.sha256(data).hexdigest() != self.sha256:
            raise UploadSourceDenied()
        return data


def prepare_upload(context, *, path="", paths=None, root=None) -> PreparedUpload:
    if not isinstance(path, str) or (paths is not None and not isinstance(paths, list)):
        raise UploadSourceDenied()
    choices = ([path] if path else []) + (paths or [])
    if len(choices) != 1 or not isinstance(choices[0], str):
        raise UploadSourceDenied()
    stored = context.get_data(STORE_KEY, recursive=False)
    if not isinstance(stored, list) or len(stored) > MAX_SOURCES:
        raise UploadSourceDenied()
    matches = [record for record in stored if isinstance(record, dict) and record.get("context_id") == str(context.id)
               and record.get("source") == choices[0]]
    if len(matches) != 1:
        raise UploadSourceDenied()
    record = matches[0]
    root = root or _root()
    relative = _relative(choices[0], root)
    identity = record.get("identity")
    if (set(record) != {"context_id", "source", "relative", "identity", "sha256", "mime_type", "byte_count"}
        or str(relative) != record["relative"] or not isinstance(identity, list) or len(identity) != 5
        or any(type(value) is not int or value < 0 for value in identity)
        or not isinstance(record["sha256"], str) or not re.fullmatch(r"sha256:[a-f0-9]{64}", record["sha256"])
        or not isinstance(record["mime_type"], str) or not _MIME.fullmatch(record["mime_type"])
        or type(record["byte_count"]) is not int or not 1 <= record["byte_count"] <= MAX_BYTES):
        raise UploadSourceDenied()
    return PreparedUpload(str(context.id), str(uuid.uuid4()), record["mime_type"], record["byte_count"],
                          record["sha256"], root, relative, tuple(identity))
