# backup_get_defaults.py DOX

## Purpose

- Own the `backup_get_defaults.py` API endpoint.
- This module handles backup get defaults requests.
- Keep this file-level DOX profile synchronized with `backup_get_defaults.py` because this directory is intentionally flat.

## Ownership

- `backup_get_defaults.py` owns the runtime implementation.
- `backup_get_defaults.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `BackupGetDefaults` (`ApiHandler`)
  - `requires_auth(cls) -> bool`
  - `requires_loopback(cls) -> bool`
  - `async process(self, input: dict, request: Request) -> dict | Response`

## Runtime Contracts

- HTTP handlers must derive from `helpers.api.ApiHandler`; WebSocket handlers must derive from `helpers.ws.WsHandler`.
- Update this file whenever request payloads, authentication or CSRF requirements, response shapes, route side effects, or WebSocket event contracts change.
- `BackupGetDefaults` is an `ApiHandler`.
- `BackupGetDefaults` defines `process(...)`.
- `BackupGetDefaults` defines `requires_auth(...)`.
- `BackupGetDefaults` defines `requires_loopback(...)`.
- Imported dependency areas include: `helpers.api`, `helpers.backup`.

## Key Concepts

- Important called helpers/classes observed in the source: `BackupService`, `backup_service.get_default_backup_metadata`.
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
