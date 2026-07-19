# upload_work_dir_files.py DOX

## Purpose

- Own the `upload_work_dir_files.py` API endpoint.
- This module handles workdir file operations for upload work dir files.
- Keep this file-level DOX profile synchronized with `upload_work_dir_files.py` because this directory is intentionally flat.

## Ownership

- `upload_work_dir_files.py` owns the runtime implementation.
- `upload_work_dir_files.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `UploadWorkDirFiles` (`ApiHandler`)
  - `async process(self, input: dict, request: Request) -> dict | Response`
- Top-level functions:
- `async upload_files(uploaded_files: list[FileStorage], current_path: str)`
- `async upload_file(current_path: str, filename: str, base64_content: str)`

## Runtime Contracts

- HTTP handlers must derive from `helpers.api.ApiHandler`; WebSocket handlers must derive from `helpers.ws.WsHandler`.
- Update this file whenever request payloads, authentication or CSRF requirements, response shapes, route side effects, or WebSocket event contracts change.
- `UploadWorkDirFiles` is an `ApiHandler`.
- `UploadWorkDirFiles` defines `process(...)`.
- Observed side-effect areas: filesystem writes.
- Imported dependency areas include: `api`, `base64`, `helpers`, `helpers.api`, `helpers.file_browser`, `os`, `posixpath`, `werkzeug.datastructures`.

## Key Concepts

- Important called helpers/classes observed in the source: `runtime.is_development`, `FileBrowser`, `browser.save_file_b64`, `request.files.getlist`, `browser.save_files`, `Exception`, `upload_files`, `runtime.call_development_function`, `file.stream.read`, `base64.b64encode.decode`, `extension.call_extensions_async`, `base64.b64encode`, `posixpath.join`, `str.rstrip`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve authentication, CSRF, loopback, and API-key checks unless the endpoint contract explicitly changes.
- Update frontend callers, plugin callers, and tests together when payload shape changes.
- Use `helpers.api.Response` for non-JSON responses, files, redirects, or status-specific replies.

## Verification

- Run endpoint-specific or API/WebSocket tests for changed behavior; smoke-test browser callers when no focused test exists.
- No direct test reference was found by name search; choose the nearest behavioral test or perform a focused smoke check.

## Child DOX Index

No child DOX files.
