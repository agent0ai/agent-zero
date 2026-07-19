from __future__ import annotations

from pathlib import Path
import shutil
import stat
import subprocess
import tarfile
import zipfile

from helpers import extension, files, runtime
from helpers.api import ApiHandler, Input, Output, Request
from api import get_work_dir_files


ARCHIVE_SUFFIXES = (
    ".tar.gz", ".tar.bz2", ".tar.xz", ".tar.zst", ".tar", ".tgz", ".tbz", ".tbz2", ".txz",
    ".zip", ".rar", ".7z", ".gz", ".bz2", ".xz", ".zst",
)
TAR_SUFFIXES = (".tar.gz", ".tar.bz2", ".tar.xz", ".tar", ".tgz", ".tbz", ".tbz2", ".txz")


class ExtractWorkDirArchive(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        path = str(input.get("path") or "").strip()
        if not path:
            return {"error": "Archive path is required"}
        if not path.startswith("/"):
            path = f"/{path}"

        try:
            extracted_path = await runtime.call_development_function(extract_archive, path)
        except (OSError, ValueError) as exc:
            return {"error": str(exc)}

        current_path = str(input.get("currentPath") or "")
        await extension.call_extensions_async(
            "workdir_file_mutation_after",
            agent=None,
            data={
                "action": "extract",
                "path": extracted_path,
                "paths": [path, extracted_path],
                "current_path": current_path,
            },
        )
        listing = await runtime.call_development_function(get_work_dir_files.get_files, current_path)
        return {"data": listing, "extracted_path": extracted_path}


def extract_archive(path: str) -> str:
    source = resolve_archive_path(path)
    target = create_target_directory(source)
    try:
        kind = archive_kind(source)
        if kind == "zip":
            extract_zip(source, target)
        elif kind == "tar":
            extract_tar(source, target)
        else:
            extract_with_7zip(source, target)
    except Exception:
        shutil.rmtree(target, ignore_errors=True)
        raise
    return str(target)


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
    target.mkdir()
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


def extract_zip(source: Path, target: Path) -> None:
    with zipfile.ZipFile(source) as archive:
        for member in archive.infolist():
            safe_member_path(target, member.filename)
            if stat.S_ISLNK(member.external_attr >> 16):
                raise ValueError("Archive contains a symbolic link")
        archive.extractall(target)


def extract_tar(source: Path, target: Path) -> None:
    with tarfile.open(source, "r:*") as archive:
        for member in archive.getmembers():
            safe_member_path(target, member.name)
            if member.issym() or member.islnk() or member.isdev():
                raise ValueError("Archive contains a symbolic link or device")
        archive.extractall(target, filter="data")


def extract_with_7zip(source: Path, target: Path) -> None:
    binary = shutil.which("7z") or shutil.which("7zz")
    if not binary:
        raise ValueError("This archive format requires 7-Zip in the runtime image")
    listing = subprocess.run(
        [binary, "l", "-slt", str(source)],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    marker = "----------"
    if marker not in listing:
        raise ValueError("Could not inspect archive safely")
    for line in listing.split(marker, 1)[1].splitlines():
        if line.startswith("Path = "):
            safe_member_path(target, line.removeprefix("Path = "))
    subprocess.run([binary, "x", "-y", f"-o{target}", str(source)], check=True, capture_output=True)
    if any(path.is_symlink() for path in target.rglob("*")):
        raise ValueError("Archive contains a symbolic link")
