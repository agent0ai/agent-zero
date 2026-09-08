"""Bounded archive creation and extraction with owned temporary cleanup."""
import os
from pathlib import Path
import tempfile
import zipfile
from helpers.localization import Localization
from helpers import files
import shutil
import stat
import tarfile
import subprocess
import threading
from contextlib import contextmanager
from helpers.file_transfers import copy_stream, FileLimitExceeded


def normalize_paths(paths) -> list[str]:
    if not isinstance(paths, list):
        raise ValueError("Paths must be a list")

    normalized: list[str] = []
    seen: set[str] = set()
    for raw_path in paths:
        if not isinstance(raw_path, str):
            continue
        path = raw_path.strip()
        if not path:
            continue
        if not path.startswith("/"):
            path = f"/{path}"
        if path not in seen:
            normalized.append(path)
            seen.add(path)

    return normalized


def selected_archive_name(count: int) -> str:
    stamp = Localization.get().now().strftime("%Y%m%d-%H%M%S")
    return f"agent-zero-selected-{count}-{stamp}.zip"


def create_selected_zip(paths: list[str], current_path: str = "", max_bytes=None, max_entries=None) -> str:
    base_dir = Path("/")
    current_dir = resolve_download_path(current_path, base_dir) if current_path else None
    if current_dir and current_dir.is_file():
        current_dir = current_dir.parent

    selected_paths = []
    for path in normalize_paths(paths):
        resolved = resolve_download_path(path, base_dir)
        if resolved.exists():
            selected_paths.append(resolved)

    selected_paths = collapse_nested_paths(selected_paths)
    if not selected_paths:
        raise FileNotFoundError("No selected files were found")

    zip_file_path = tempfile.NamedTemporaryFile(suffix=".zip", delete=False).name
    used_names: set[str] = set()

    remaining = [max_bytes, max_entries]
    try:
        with zipfile.ZipFile(zip_file_path, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=True) as zipped:
            for source_path in selected_paths:
                arc_root = unique_archive_name(archive_root_name(source_path, current_dir, base_dir), used_names)
                write_zip_entry(zipped, source_path, arc_root, remaining)
        if max_bytes is not None and os.path.getsize(zip_file_path) > max_bytes:
            raise FileLimitExceeded(max_bytes)
    except BaseException:
        Path(zip_file_path).unlink(missing_ok=True)
        raise

    return zip_file_path


def resolve_download_path(path: str, base_dir: Path) -> Path:
    if not path:
        raise ValueError("Invalid file path")

    candidate = Path(path)
    resolved = candidate.resolve() if candidate.is_absolute() else (base_dir / candidate).resolve()

    try:
        resolved.relative_to(base_dir)
    except ValueError as exc:
        raise ValueError("Invalid file path") from exc

    return resolved


def collapse_nested_paths(paths: list[Path]) -> list[Path]:
    collapsed: list[Path] = []
    for path in sorted(paths, key=lambda item: len(item.parts)):
        if any(path == parent or parent in path.parents for parent in collapsed):
            continue
        collapsed.append(path)
    return collapsed


def archive_root_name(source_path: Path, current_dir: Path | None, base_dir: Path) -> str:
    if current_dir:
        try:
            return source_path.relative_to(current_dir).as_posix().strip("/")
        except ValueError:
            pass

    try:
        return source_path.relative_to(base_dir).as_posix().strip("/")
    except ValueError:
        return source_path.name


def unique_archive_name(name: str, used_names: set[str]) -> str:
    clean_name = name or "selection"
    if clean_name not in used_names:
        used_names.add(clean_name)
        return clean_name

    stem, suffix = os.path.splitext(clean_name)
    index = 2
    while True:
        candidate = f"{stem}-{index}{suffix}"
        if candidate not in used_names:
            used_names.add(candidate)
            return candidate
        index += 1


def write_zip_entry(zipped, source_path, arc_root, remaining=None):
    remaining = remaining if remaining is not None else [None, None]
    if source_path.is_symlink():
        raise ValueError("Archive selection contains a symbolic link.")
    if remaining[1] is not None:
        remaining[1] -= 1
        if remaining[1] < 0:
            raise ValueError("Archive exceeds the configured entry limit.")
    if source_path.is_dir():
        zipped.writestr(arc_root.rstrip("/") + "/", "")
        for child in sorted(source_path.iterdir()):
            write_zip_entry(zipped, child, arc_root.rstrip("/") + "/" + child.name, remaining)
        return
    descriptor = os.open(source_path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
    with os.fdopen(descriptor, "rb") as source:
        import stat
        if not stat.S_ISREG(os.fstat(source.fileno()).st_mode):
            raise ValueError("Archive entries must be regular files.")
        entry = zipfile.ZipInfo.from_file(source_path, arc_root)
        entry.compress_type = zipfile.ZIP_DEFLATED
        with zipped.open(entry, "w", force_zip64=True) as target:
            receipt = copy_stream(source, target, remaining[0])
        if remaining[0] is not None:
            remaining[0] -= receipt["size"]


ARCHIVE_SUFFIXES = (
    ".tar.gz", ".tar.bz2", ".tar.xz", ".tar.zst", ".tar", ".tgz", ".tbz", ".tbz2", ".txz",
    ".zip", ".rar", ".7z", ".gz", ".bz2", ".xz", ".zst",
)
TAR_SUFFIXES = (".tar.gz", ".tar.bz2", ".tar.xz", ".tar", ".tgz", ".tbz", ".tbz2", ".txz")



def resolve_archive_path(path: str) -> Path:
    base = Path(files.get_base_dir()).resolve()
    candidate = Path(path)
    resolved = candidate.resolve() if candidate.is_absolute() else (base / candidate).resolve()
    try:
        resolved.relative_to(base)
    except ValueError as exc:
        raise ValueError("Invalid archive path") from exc
    if not resolved.is_file():
        raise ValueError("Archive file was not found")
    return resolved


def archive_kind(path: Path) -> str:
    name = path.name.lower()
    if name.endswith(".zip"):
        return "zip"
    if name.endswith(TAR_SUFFIXES):
        return "tar"
    if name.endswith(ARCHIVE_SUFFIXES):
        return "7zip"
    raise ValueError("Unsupported archive format")


def create_target_directory(source: Path) -> Path:
    name = source.name
    for suffix in ARCHIVE_SUFFIXES:
        if name.lower().endswith(suffix):
            name = name[:-len(suffix)]
            break
    name = name or "extracted"
    target = source.parent / name
    index = 2
    while target.exists():
        target = source.parent / f"{name}-{index}"
        index += 1
    target.mkdir(mode=0o700)
    return target


def safe_member_path(target: Path, name: str) -> Path:
    if not name or name.startswith(("/", "\\")) or "\\" in name or ".." in Path(name).parts:
        raise ValueError("Archive contains an unsafe path")
    destination = (target / name).resolve(strict=False)
    try:
        destination.relative_to(target.resolve())
    except ValueError as exc:
        raise ValueError("Archive contains an unsafe path") from exc
    return destination




def extract_archive(path):
    from helpers.file_browser import FileBrowser
    source = resolve_archive_path(path)
    target = create_target_directory(source)
    limit, count = FileBrowser.max_extract_bytes(), FileBrowser.max_archive_entries()
    try:
        kind = archive_kind(source)
        if kind == "zip":
            extract_zip(source, target, limit, count)
        elif kind == "tar":
            extract_tar(source, target, limit, count)
        else:
            extract_with_7zip(source, target, limit, count)
    except BaseException:
        shutil.rmtree(target, ignore_errors=True)
        raise
    return str(target)


def check_members(target, members, limit, count):
    total, seen = 0, set()
    for index, (name, size, directory) in enumerate(members, 1):
        if index > count:
            raise ValueError("Archive exceeds the configured entry limit.")
        destination = safe_member_path(target, name)
        if destination in seen:
            raise ValueError("Archive contains duplicate destinations.")
        seen.add(destination)
        if size < 0:
            raise ValueError("Archive contains an invalid size.")
        total += size
        if total > limit:
            raise FileLimitExceeded(limit)


def extract_member(target, name, source, remaining, expected):
    destination = safe_member_path(target, name)
    destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with destination.open("xb") as output:
        receipt = copy_stream(source, output, remaining)
    if receipt["size"] != expected:
        raise ValueError("Extracted size differs from archive metadata.")
    return remaining - receipt["size"]


def extract_zip(source, target, limit, count):
    with zipfile.ZipFile(source) as archive:
        members = archive.infolist()
        check_members(target, ((m.filename, m.file_size, m.is_dir()) for m in members), limit, count)
        for member in members:
            mode = member.external_attr >> 16
            if stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR):
                raise ValueError("Archive contains a link or special file.")
        remaining = limit
        for member in members:
            if member.is_dir():
                safe_member_path(target, member.filename).mkdir(mode=0o700, parents=True, exist_ok=True)
            else:
                with archive.open(member) as stream:
                    remaining = extract_member(target, member.filename, stream, remaining, member.file_size)
                mode = (member.external_attr >> 16) & 0o777
                if mode:
                    safe_member_path(target, member.filename).chmod(mode)


def extract_tar(source, target, limit, count):
    with tarfile.open(source, "r:*") as archive:
        members = []
        for member in archive:
            if len(members) >= count:
                raise ValueError("Archive exceeds the configured entry limit.")
            if not member.isfile() and not member.isdir():
                raise ValueError("Archive contains a link or special file.")
            members.append(member)
        check_members(target, ((m.name, m.size, m.isdir()) for m in members), limit, count)
        remaining = limit
        for member in members:
            if member.isdir():
                safe_member_path(target, member.name).mkdir(mode=0o700, parents=True, exist_ok=True)
            else:
                with archive.extractfile(member) as stream:
                    remaining = extract_member(target, member.name, stream, remaining, member.size)
                safe_member_path(target, member.name).chmod(member.mode & 0o777)


@contextmanager
def seven_zip(args):
    binary = shutil.which("7z") or shutil.which("7zz")
    if not binary:
        raise ValueError("This archive format requires 7-Zip in the runtime image")
    with subprocess.Popen([binary, *args], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL) as process:
        timer = threading.Timer(300, process.kill)
        timer.daemon = True
        timer.start()
        try:
            yield process.stdout
            if process.wait() != 0:
                raise ValueError("7-Zip failed or exceeded its five-minute processing timeout.")
        finally:
            timer.cancel()
            if process.poll() is None:
                process.kill()
            process.wait()


def extract_with_7zip(source, target, limit, count):
    import io
    entries, block, started = [], {}, False
    with seven_zip(["l", "-slt", "--", str(source)]) as output:
        for line in io.TextIOWrapper(output, encoding="utf-8", errors="strict"):
            line = line.rstrip("\r\n")
            if line == "----------":
                started = True
                continue
            if not started:
                continue
            if not line and block:
                entries.append(block)
                block = {}
                if len(entries) > count:
                    raise ValueError("Archive exceeds the configured entry limit.")
            elif " = " in line:
                key, value = line.split(" = ", 1)
                block[key] = value
        if block:
            entries.append(block)
    if not started:
        raise ValueError("Could not inspect archive safely.")
    members = []
    for entry in entries:
        if entry.get("Symbolic Link") or entry.get("Hard Link"):
            raise ValueError("Archive contains a link.")
        name = entry.get("Path", "")
        directory = entry.get("Folder") == "+" or entry.get("Attributes", "").startswith("D")
        size = int(entry.get("Size") or 0)
        members.append((name, size, directory))
    check_members(target, members, limit, count)
    remaining = limit
    for name, size, directory in members:
        if directory:
            safe_member_path(target, name).mkdir(mode=0o700, parents=True, exist_ok=True)
        else:
            with seven_zip(["x", "-so", "-spd", "--", str(source), name]) as stream:
                remaining = extract_member(target, name, stream, remaining, size)
