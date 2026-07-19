# self_update_tags.py DOX

## Purpose

- Own the `self_update_tags.py` API endpoint.
- This module handles self update tags API requests.
- Keep this file-level DOX profile synchronized with `self_update_tags.py` because this directory is intentionally flat.

## Ownership

- `self_update_tags.py` owns the runtime implementation.
- `self_update_tags.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `SelfUpdateTags` (`ApiHandler`)
  - `async process(self, input: dict, request: Request) -> dict | Response`

## Runtime Contracts

- HTTP handlers must derive from `helpers.api.ApiHandler`; WebSocket handlers must derive from `helpers.ws.WsHandler`.
- Update this file whenever request payloads, authentication or CSRF requirements, response shapes, route side effects, or WebSocket event contracts change.
- `SelfUpdateTags` is an `ApiHandler`.
- `SelfUpdateTags` defines `process(...)`.
- Imported dependency areas include: `helpers`, `helpers.api`.

## Key Concepts

- Important called helpers/classes observed in the source: `str.strip.lower`, `self_update.get_repo_version_info.get.strip.lower`, `self_update.get_available_branch_values`, `self_update.get_selector_tag_options`, `str.strip`, `self_update.get_repo_version_info.get.strip`, `runtime.is_dockerized`, `self_update.get_repo_version_info`.
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
