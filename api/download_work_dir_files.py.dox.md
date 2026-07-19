# download_work_dir_files.py DOX

## Purpose

- Own the `download_work_dir_files.py` API endpoint.
- This module handles workdir file operations for download work dir files.
- Keep this file-level DOX profile synchronized with `download_work_dir_files.py` because this directory is intentionally flat.

## Ownership

- `download_work_dir_files.py` owns the runtime implementation.
- `download_work_dir_files.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `DownloadFiles` (`ApiHandler`)
  - `async process(self, input: Input, request: Request) -> Output`
- Top-level functions:
- `normalize_paths(paths) -> list[str]`
- `selected_archive_name(count: int) -> str`
- `create_selected_zip(paths: list[str], current_path: str=...) -> str`
- `resolve_download_path(path: str, base_dir: Path) -> Path`
- `collapse_nested_paths(paths: list[Path]) -> list[Path]`
- `archive_root_name(source_path: Path, current_dir: Path | None, base_dir: Path) -> str`
- `unique_archive_name(name: str, used_names: set[str]) -> str`
- `write_zip_entry(zip_file: zipfile.ZipFile, source_path: Path, arc_root: str) -> None`

## Runtime Contracts

- HTTP handlers must derive from `helpers.api.ApiHandler`; WebSocket handlers must derive from `helpers.ws.WsHandler`.
- Update this file whenever request payloads, authentication or CSRF requirements, response shapes, route side effects, or WebSocket event contracts change.
- `DownloadFiles` is an `ApiHandler`.
- `DownloadFiles` defines `process(...)`.
- Observed side-effect areas: filesystem reads, filesystem writes, filesystem deletion.
- Imported dependency areas include: `api.download_work_dir_file`, `base64`, `flask`, `helpers`, `helpers.api`, `helpers.localization`, `io`, `os`, `pathlib`, `tempfile`, `zipfile`.

## Key Concepts

- Important called helpers/classes observed in the source: `Localization.get.now.strftime`, `Path.resolve`, `normalize_paths`, `collapse_nested_paths`, `Path`, `os.path.splitext`, `source_path.is_dir`, `zip_file.write`, `selected_archive_name`, `runtime.is_development`, `stream_file_download`, `ValueError`, `raw_path.strip`, `resolve_download_path`, `current_dir.is_file`, `resolved.exists`, `FileNotFoundError`, `tempfile.NamedTemporaryFile`, `zipfile.ZipFile`, `candidate.is_absolute`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve authentication, CSRF, loopback, and API-key checks unless the endpoint contract explicitly changes.
- Update frontend callers, plugin callers, and tests together when payload shape changes.
- Use `helpers.api.Response` for non-JSON responses, files, redirects, or status-specific replies.

## Verification

- Run endpoint-specific or API/WebSocket tests for changed behavior; smoke-test browser callers when no focused test exists.
- Related tests observed by source search:
  - `tests/test_download_toast_regressions.py`

## Child DOX Index

No child DOX files.
