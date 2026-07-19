# file_info.py DOX

## Purpose

- Own the `file_info.py` API endpoint.
- This module handles file info API requests.
- Keep this file-level DOX profile synchronized with `file_info.py` because this directory is intentionally flat.

## Ownership

- `file_info.py` owns the runtime implementation.
- `file_info.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `FileInfoApi` (`ApiHandler`)
  - `async process(self, input: Input, request: Request) -> Output`
- `FileInfo` (`TypedDict`)
- Top-level functions:
- `async get_file_info(path: str) -> FileInfo`

## Runtime Contracts

- HTTP handlers must derive from `helpers.api.ApiHandler`; WebSocket handlers must derive from `helpers.ws.WsHandler`.
- Update this file whenever request payloads, authentication or CSRF requirements, response shapes, route side effects, or WebSocket event contracts change.
- `FileInfoApi` is an `ApiHandler`.
- `FileInfoApi` defines `process(...)`.
- Observed side-effect areas: filesystem reads.
- Imported dependency areas include: `helpers`, `helpers.api`, `os`, `typing`.

## Key Concepts

- Important called helpers/classes observed in the source: `files.get_abs_path`, `os.path.exists`, `os.path.dirname`, `os.path.basename`, `runtime.call_development_function`, `os.path.isdir`, `os.path.isfile`, `os.path.islink`, `os.path.getsize`, `os.path.getmtime`, `os.path.getctime`, `os.path.splitext`, `os.stat`.
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
