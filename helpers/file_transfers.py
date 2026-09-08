"""Bounded streaming and atomic publication shared by file operations."""
import hashlib
import os
from pathlib import Path
import stat
import tempfile
from threading import Lock, Timer



CHUNK_BYTES = 1024 * 1024


class FileLimitExceeded(ValueError):
    def __init__(self, limit):
        super().__init__(f"File exceeds the {limit / (1024 * 1024):g} MiB size limit.")


class TransferWriter:
    def __init__(self, destination, limit=None):
        self.destination, self.limit = destination, limit
        self.size = 0
        self.digest = hashlib.sha256()

    def write(self, chunk):
        if self.limit is not None and self.size + len(chunk) > self.limit:
            raise FileLimitExceeded(self.limit)
        if self.destination is not None:
            remaining = memoryview(chunk)
            while remaining:
                written = self.destination.write(remaining)
                if written is None:
                    break
                if written <= 0:
                    raise OSError("File write made no progress.")
                remaining = remaining[written:]
        self.size += len(chunk)
        self.digest.update(chunk)
        return len(chunk)

    def receipt(self):
        return {"size": self.size, "sha256": self.digest.hexdigest()}


def copy_stream(source, destination, limit=None):
    output = TransferWriter(destination, limit)
    while chunk := source.read(CHUNK_BYTES):
        output.write(chunk)
    return output.receipt()


def write_stream_atomic(source, target_path, *, max_bytes=None):
    target = Path(target_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    previous = target.lstat() if target.exists() or target.is_symlink() else None
    if previous and not stat.S_ISREG(previous.st_mode):
        raise ValueError("Choose a regular destination file.")
    descriptor, temporary = tempfile.mkstemp(prefix=".partial-", dir=target.parent)
    try:
        with os.fdopen(descriptor, "wb") as output:
            result = copy_stream(source, output, max_bytes)
            if previous:
                if hasattr(os, "geteuid") and os.geteuid() == 0:
                    os.fchown(output.fileno(), previous.st_uid, previous.st_gid)
                os.fchmod(output.fileno(), stat.S_IMODE(previous.st_mode))
            output.flush()
            os.fsync(output.fileno())
        if previous:
            current = target.lstat()
            if (current.st_dev, current.st_ino, current.st_size, current.st_mtime_ns) != (
                previous.st_dev, previous.st_ino, previous.st_size, previous.st_mtime_ns
            ):
                raise ValueError("The destination changed during upload. Try again.")
            os.replace(temporary, target)
        else:
            os.link(temporary, target)
        directory_fd = os.open(target.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
        return result
    finally:
        Path(temporary).unlink(missing_ok=True)


def make_disposition(name):
    from urllib.parse import quote
    ascii_name = name.encode("ascii", "ignore").decode() or "download"
    ascii_name = ascii_name.replace('"', "_").replace("\\", "_").replace("\r", "_").replace("\n", "_")
    return f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(name)}"


def stream_file_download(file_source, download_name, chunk_size=8192, max_bytes=None, delete_after=False):
    import mimetypes
    from flask import Response
    path = Path(file_source) if isinstance(file_source, (str, Path)) else None
    if path:
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            os.close(descriptor)
            raise ValueError("Choose a regular file for download.")
        stream = os.fdopen(descriptor, "rb")
    else:
        stream = file_source
    if delete_after and path and os.name != "nt":
        path.unlink()
        delete_after = False
    def close():
        stream.close()
        if delete_after and path:
            path.unlink(missing_ok=True)
    try:
        stream.seek(0)
        receipt = copy_stream(stream, None, max_bytes)
        stream.seek(0)
    except BaseException:
        close()
        raise
    def generate():
        remaining = receipt["size"]
        try:
            while remaining:
                chunk = stream.read(min(chunk_size, remaining))
                if not chunk:
                    break
                remaining -= len(chunk)
                yield chunk
        finally:
            close()
    response = Response(generate(), content_type=mimetypes.guess_type(download_name)[0] or "application/octet-stream",
                        headers={"Content-Disposition": make_disposition(download_name),
                                 "Content-Length": str(receipt["size"]), "X-Content-SHA256": receipt["sha256"],
                                 "Cache-Control": "no-cache", "X-Accel-Buffering": "no"}, direct_passthrough=True)
    response.call_on_close(close)
    return response


_DOWNLOADS = {}
_DOWNLOADS_LOCK = Lock()


def prepare_download_response(response, authorize=None):
    import secrets
    token = secrets.token_urlsafe(32)
    def expire():
        with _DOWNLOADS_LOCK:
            entry = _DOWNLOADS.pop(token, None)
        if entry:
            entry[0].close()
    timer = Timer(120, expire)
    timer.daemon = True
    with _DOWNLOADS_LOCK:
        _DOWNLOADS[token] = (response, timer, authorize)
    timer.start()
    return token


def take_download_response(token):
    with _DOWNLOADS_LOCK:
        entry = _DOWNLOADS.pop(token, None)
    if entry is None:
        raise FileNotFoundError("Download expired. Start it again from Files.")
    response, timer, authorize = entry
    timer.cancel()
    try:
        if authorize:
            authorize()
        return response
    except BaseException:
        response.close()
        raise
