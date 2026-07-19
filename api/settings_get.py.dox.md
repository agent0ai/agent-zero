# settings_get.py DOX

## Purpose

- Own the `settings_get.py` API endpoint.
- This module returns current application settings.
- Keep this file-level DOX profile synchronized with `settings_get.py` because this directory is intentionally flat.

## Ownership

- `settings_get.py` owns the runtime implementation.
- `settings_get.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `GetSettings` (`ApiHandler`)
  - `async process(self, input: dict, request: Request) -> dict | Response`
  - `get_methods(cls) -> list[str]`

## Runtime Contracts

- HTTP handlers must derive from `helpers.api.ApiHandler`; WebSocket handlers must derive from `helpers.ws.WsHandler`.
- Update this file whenever request payloads, authentication or CSRF requirements, response shapes, route side effects, or WebSocket event contracts change.
- `GetSettings` is an `ApiHandler`.
- `GetSettings` defines `process(...)`.
- `GetSettings` defines `get_methods(...)`.
- Observed side-effect areas: settings/state persistence.
- Imported dependency areas include: `helpers`, `helpers.api`.

## Key Concepts

- Important called helpers/classes observed in the source: `settings.get_settings`, `settings.convert_out`.
- The returned settings map includes normalized `ui_control_visibility` mobile and desktop flags for the configurable WebUI controls.
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
