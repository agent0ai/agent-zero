# edit_work_dir_file.py DOX

## Purpose

- Own the `edit_work_dir_file.py` API endpoint.
- This module handles workdir file operations for edit work dir file.
- Keep this file-level DOX profile synchronized with `edit_work_dir_file.py` because this directory is intentionally flat.

## Ownership

- `edit_work_dir_file.py` owns the runtime implementation.
- `edit_work_dir_file.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `EditWorkDirFile` (`ApiHandler`)
  - `get_methods(cls)`
  - `async process(self, input: Input, request: Request) -> Output`
- Top-level functions:
- `async load_file(file_path: str) -> dict`
- `save_file(file_path: str, content: str) -> bool`
- Notable constants/configuration names: `MAX_EDIT_FILE_SIZE`, `BINARY_SAMPLE_SIZE`.

## Runtime Contracts

- HTTP handlers must derive from `helpers.api.ApiHandler`; WebSocket handlers must derive from `helpers.ws.WsHandler`.
- Update this file whenever request payloads, authentication or CSRF requirements, response shapes, route side effects, or WebSocket event contracts change.
- `EditWorkDirFile` is an `ApiHandler`.
- `EditWorkDirFile` defines `process(...)`.
- `EditWorkDirFile` defines `get_methods(...)`.
- Observed side-effect areas: filesystem reads, filesystem writes.
- Imported dependency areas include: `helpers`, `helpers.api`, `helpers.file_browser`, `mimetypes`, `os`.

## Key Concepts

- Important called helpers/classes observed in the source: `FileBrowser`, `browser.get_full_path`, `os.path.isdir`, `os.path.getsize`, `files.is_probably_binary_file`, `mimetypes.guess_type`, `browser.save_text_file`, `error_str.strip`, `Exception`, `os.path.basename`, `error_str.split`, `file.read`, `line.split.strip`, `file_path.startswith`, `content.encode`, `runtime.call_development_function`, `extension.call_extensions_async`, `self._extract_error_message`, `line.split`.
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
