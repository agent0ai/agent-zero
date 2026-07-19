# delete_work_dir_files.py DOX

## Purpose

- Own the `delete_work_dir_files.py` API endpoint.
- This module handles workdir file operations for delete work dir files.
- Keep this file-level DOX profile synchronized with `delete_work_dir_files.py` because this directory is intentionally flat.

## Ownership

- `delete_work_dir_files.py` owns the runtime implementation.
- `delete_work_dir_files.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `DeleteWorkDirFiles` (`ApiHandler`)
  - `async process(self, input: Input, request: Request) -> Output`
- Top-level functions:
- `async delete_files(paths: list[str]) -> dict`
- `collapse_nested_paths(paths: list[str]) -> list[str]`

## Runtime Contracts

- HTTP handlers must derive from `helpers.api.ApiHandler`; WebSocket handlers must derive from `helpers.ws.WsHandler`.
- Update this file whenever request payloads, authentication or CSRF requirements, response shapes, route side effects, or WebSocket event contracts change.
- `DeleteWorkDirFiles` is an `ApiHandler`.
- `DeleteWorkDirFiles` defines `process(...)`.
- Observed side-effect areas: filesystem deletion.
- Imported dependency areas include: `api`, `api.download_work_dir_files`, `helpers`, `helpers.api`, `helpers.file_browser`.

## Key Concepts

- Important called helpers/classes observed in the source: `FileBrowser`, `collapse_nested_paths`, `browser.delete_file`, `normalize_paths`, `runtime.call_development_function`, `path.strip`, `extension.call_extensions_async`, `item.count`, `clean_path.startswith`, `parent.rstrip`.
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
