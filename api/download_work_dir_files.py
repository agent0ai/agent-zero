import base64
from datetime import datetime
from io import BytesIO
import os
from pathlib import Path
import tempfile
import zipfile

from flask import Response

from helpers.api import ApiHandler, Input, Output, Request
from helpers import files, runtime
from api.download_work_dir_file import fetch_file, stream_file_download


class DownloadFiles(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        try:
            paths = normalize_paths(input.get("paths", []))
        except ValueError as exc:
            return Response(str(exc), status=400)

        current_path = input.get("currentPath", "")

        if not paths:
            return Response("No file paths provided", status=400)

        try:
            zip_file = await runtime.call_development_function(
                create_selected_zip, paths, current_path
            )
        except ValueError as exc:
            return Response(str(exc), status=400)
        except FileNotFoundError as exc:
            return Response(str(exc), status=404)

        download_name = selected_archive_name(len(paths))
        if runtime.is_development():
            b64 = await runtime.call_development_function(fetch_file, zip_file)
            file_data = BytesIO(base64.b64decode(b64))
            return stream_file_download(file_data, download_name=download_name)

        return stream_file_download(zip_file, download_name=download_name)


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
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"agent-zero-selected-{count}-{stamp}.zip"


def create_selected_zip(paths: list[str], current_path: str = "") -> str:
    base_dir = Path(files.get_base_dir()).resolve()
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

    with zipfile.ZipFile(
        zip_file_path, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=True
    ) as zip_file:
        for source_path in selected_paths:
            arc_root = unique_archive_name(
                archive_root_name(source_path, current_dir, base_dir), used_names
            )
            write_zip_entry(zip_file, source_path, arc_root)

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


def write_zip_entry(zip_file: zipfile.ZipFile, source_path: Path, arc_root: str) -> None:
    if source_path.is_dir():
        wrote_any = False
        for root, dirs, file_names in os.walk(source_path):
            dirs.sort()
            file_names.sort()
            root_path = Path(root)
            rel_root = root_path.relative_to(source_path)

            if not dirs and not file_names:
                empty_dir = Path(arc_root) / rel_root
                zip_file.writestr(empty_dir.as_posix().rstrip("/") + "/", "")

            for file_name in file_names:
                file_path = root_path / file_name
                rel_path = file_path.relative_to(source_path)
                zip_file.write(file_path, (Path(arc_root) / rel_path).as_posix())
                wrote_any = True

        if not wrote_any:
            zip_file.writestr(Path(arc_root).as_posix().rstrip("/") + "/", "")
        return

    zip_file.write(source_path, arc_root)
