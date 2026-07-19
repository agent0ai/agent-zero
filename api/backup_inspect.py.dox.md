# backup_inspect.py DOX

## Purpose

- Own the `backup_inspect.py` API endpoint.
- This module handles backup inspect requests.
- Keep this file-level DOX profile synchronized with `backup_inspect.py` because this directory is intentionally flat.

## Ownership

- `backup_inspect.py` owns the runtime implementation.
- `backup_inspect.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `BackupInspect` (`ApiHandler`)
  - `requires_auth(cls) -> bool`
  - `requires_loopback(cls) -> bool`
  - `async process(self, input: dict, request: Request) -> dict | Response`

## Runtime Contracts

- HTTP handlers must derive from `helpers.api.ApiHandler`; WebSocket handlers must derive from `helpers.ws.WsHandler`.
- Update this file whenever request payloads, authentication or CSRF requirements, response shapes, route side effects, or WebSocket event contracts change.
- `BackupInspect` is an `ApiHandler`.
- `BackupInspect` defines `process(...)`.
- `BackupInspect` defines `requires_auth(...)`.
- `BackupInspect` defines `requires_loopback(...)`.
- Imported dependency areas include: `helpers.api`, `helpers.backup`, `werkzeug.datastructures`.

## Key Concepts

- Important called helpers/classes observed in the source: `BackupService`, `backup_service.inspect_backup`.
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
