# load_webui_extensions.py DOX

## Purpose

- Own the `load_webui_extensions.py` API endpoint.
- This module returns frontend extension manifests/files for a WebUI extension point.
- Keep this file-level DOX profile synchronized with `load_webui_extensions.py` because this directory is intentionally flat.

## Ownership

- `load_webui_extensions.py` owns the runtime implementation.
- `load_webui_extensions.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `LoadWebuiExtensions` (`ApiHandler`)
  - `async process(self, input: dict, request: Request) -> dict | Response`

## Runtime Contracts

- HTTP handlers must derive from `helpers.api.ApiHandler`; WebSocket handlers must derive from `helpers.ws.WsHandler`.
- Update this file whenever request payloads, authentication or CSRF requirements, response shapes, route side effects, or WebSocket event contracts change.
- `LoadWebuiExtensions` is an `ApiHandler`.
- `LoadWebuiExtensions` defines `process(...)`.
- Imported dependency areas include: `helpers`, `helpers.api`.

## Key Concepts

- Important called helpers/classes observed in the source: `extension.get_webui_extensions`, `Response`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve authentication, CSRF, loopback, and API-key checks unless the endpoint contract explicitly changes.
- Update frontend callers, plugin callers, and tests together when payload shape changes.
- Use `helpers.api.Response` for non-JSON responses, files, redirects, or status-specific replies.

## Verification

- Run endpoint-specific or API/WebSocket tests for changed behavior; smoke-test browser callers when no focused test exists.
- Related tests observed by source search:
  - `tests/test_webui_extension_surfaces.py`

## Child DOX Index

No child DOX files.
