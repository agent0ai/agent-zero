# get_work_dir_files.py DOX

## Purpose

- Own the `get_work_dir_files.py` API endpoint.
- This module handles workdir file operations for get work dir files.
- Keep this file-level DOX profile synchronized with `get_work_dir_files.py` because this directory is intentionally flat.

## Ownership

- `get_work_dir_files.py` owns the runtime implementation.
- `get_work_dir_files.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `GetWorkDirFiles` (`ApiHandler`)
  - `get_methods(cls)`
  - `async process(self, input: dict, request: Request) -> dict | Response`
- Top-level functions:
- `async get_files(path)`

## Runtime Contracts

- HTTP handlers must derive from `helpers.api.ApiHandler`; WebSocket handlers must derive from `helpers.ws.WsHandler`.
- Update this file whenever request payloads, authentication or CSRF requirements, response shapes, route side effects, or WebSocket event contracts change.
- `GetWorkDirFiles` is an `ApiHandler`.
- `GetWorkDirFiles` defines `process(...)`.
- `GetWorkDirFiles` defines `get_methods(...)`.
- Imported dependency areas include: `helpers`, `helpers.api`, `helpers.file_browser`.

## Key Concepts

- Important called helpers/classes observed in the source: `FileBrowser`, `browser.get_files`, `runtime.call_development_function`.
- Empty `path` requests and explicit `$WORK_DIR` requests resolve to the default workdir path before `FileBrowser` is called, so the WebUI never receives an empty startup path for the default file browser view.
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
