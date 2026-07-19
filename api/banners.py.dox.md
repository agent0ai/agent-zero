# banners.py DOX

## Purpose

- Own the `banners.py` API endpoint.
- This module collects alert banners and discovery cards from backend extensions.
- Keep this file-level DOX profile synchronized with `banners.py` because this directory is intentionally flat.

## Ownership

- `banners.py` owns the runtime implementation.
- `banners.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `GetBanners` (`ApiHandler`)
  - `async process(self, input: dict, request: Request) -> dict | Response`

## Runtime Contracts

- HTTP handlers must derive from `helpers.api.ApiHandler`; WebSocket handlers must derive from `helpers.ws.WsHandler`.
- Update this file whenever request payloads, authentication or CSRF requirements, response shapes, route side effects, or WebSocket event contracts change.
- `GetBanners` is an `ApiHandler`.
- `GetBanners` defines `process(...)`.
- Imported dependency areas include: `helpers.api`, `helpers.extension`.

## Key Concepts

- Important called helpers/classes observed in the source: `call_extensions_async`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve authentication, CSRF, loopback, and API-key checks unless the endpoint contract explicitly changes.
- Update frontend callers, plugin callers, and tests together when payload shape changes.
- Use `helpers.api.Response` for non-JSON responses, files, redirects, or status-specific replies.

## Verification

- Run endpoint-specific or API/WebSocket tests for changed behavior; smoke-test browser callers when no focused test exists.
- Related tests observed by source search:
  - `tests/test_model_config_api_keys.py`
  - `tests/test_oauth_static.py`
  - `tests/test_webui_extension_surfaces.py`

## Child DOX Index

No child DOX files.
