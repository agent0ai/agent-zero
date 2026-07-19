# download_work_dir_file.py DOX

## Purpose

- Own the `download_work_dir_file.py` API endpoint.
- This module handles workdir file operations for download work dir file.
- Keep this file-level DOX profile synchronized with `download_work_dir_file.py` because this directory is intentionally flat.

## Ownership

- `download_work_dir_file.py` owns the runtime implementation.
- `download_work_dir_file.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `DownloadFile` (`ApiHandler`)
  - `get_methods(cls)`
  - `async process(self, input: Input, request: Request) -> Output`
- Top-level functions:
- `stream_file_download(file_source, download_name, chunk_size=...)`: Create a streaming response for file downloads that shows progress in browser.
- `make_disposition(download_name: str) -> str`
- `resolve_download_path(path: str) -> str`: Resolve a requested download path and keep it within the runtime base dir.
- `async fetch_file(path)`

## Runtime Contracts

- HTTP handlers must derive from `helpers.api.ApiHandler`; WebSocket handlers must derive from `helpers.ws.WsHandler`.
- Update this file whenever request payloads, authentication or CSRF requirements, response shapes, route side effects, or WebSocket event contracts change.
- `DownloadFile` is an `ApiHandler`.
- `DownloadFile` defines `process(...)`.
- `DownloadFile` defines `get_methods(...)`.
- Observed side-effect areas: filesystem reads, network calls.
- Imported dependency areas include: `api`, `base64`, `flask`, `helpers`, `helpers.api`, `io`, `mimetypes`, `os`, `pathlib`, `urllib.parse`.

## Key Concepts

- Important called helpers/classes observed in the source: `mimetypes.guess_type`, `Response`, `quote`, `Path.resolve`, `Path`, `candidate.is_absolute`, `os.path.getsize`, `generate`, `download_name.encode.decode`, `candidate.resolve`, `resolve`, `resolved.relative_to`, `Exception`, `file.read`, `base64.b64encode.decode`, `file_source.tell`, `file_source.seek`, `ValueError`, `file_path.startswith`, `runtime.call_development_function`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve authentication, CSRF, loopback, and API-key checks unless the endpoint contract explicitly changes.
- Update frontend callers, plugin callers, and tests together when payload shape changes.
- Use `helpers.api.Response` for non-JSON responses, files, redirects, or status-specific replies.

## Verification

- Run endpoint-specific or API/WebSocket tests for changed behavior; smoke-test browser callers when no focused test exists.
- Related tests observed by source search:
  - `tests/test_download_toast_regressions.py`
  - `tests/test_office_canvas_setup.py`

## Child DOX Index

No child DOX files.
