# api_files_get.py DOX

## Purpose

- Own the `api_files_get.py` API endpoint.
- This module returns downloadable or inspectable files exposed through the external API surface.
- Keep this file-level DOX profile synchronized with `api_files_get.py` because this directory is intentionally flat.

## Ownership

- `api_files_get.py` owns the runtime implementation.
- `api_files_get.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `ApiFilesGet` (`ApiHandler`)
  - `requires_auth(cls) -> bool`
  - `requires_csrf(cls) -> bool`
  - `requires_api_key(cls) -> bool`
  - `get_methods(cls) -> list[str]`
  - `async process(self, input: dict, request: Request) -> dict | Response`

## Runtime Contracts

- HTTP handlers must derive from `helpers.api.ApiHandler`; WebSocket handlers must derive from `helpers.ws.WsHandler`.
- Update this file whenever request payloads, authentication or CSRF requirements, response shapes, route side effects, or WebSocket event contracts change.
- `ApiFilesGet` is an `ApiHandler`.
- `ApiFilesGet` defines `process(...)`.
- `ApiFilesGet` defines `get_methods(...)`.
- `ApiFilesGet` defines `requires_auth(...)`.
- `ApiFilesGet` defines `requires_csrf(...)`.
- `ApiFilesGet` defines `requires_api_key(...)`.
- Observed side-effect areas: filesystem reads, filesystem writes, settings/state persistence.
- Imported dependency areas include: `base64`, `helpers`, `helpers.api`, `helpers.print_style`, `json`, `os`.

## Key Concepts

- Important called helpers/classes observed in the source: `Response`, `PrintStyle.error`, `path.startswith`, `PrintStyle`, `json.dumps`, `path.replace`, `files.get_abs_path`, `os.path.basename`, `os.path.exists`, `PrintStyle.warning`, `f.read`, `base64.b64encode.decode`, `base64.b64encode`.
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
