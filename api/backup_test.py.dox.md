# backup_test.py DOX

## Purpose

- Own the `backup_test.py` API endpoint.
- This module handles backup test requests.
- Keep this file-level DOX profile synchronized with `backup_test.py` because this directory is intentionally flat.

## Ownership

- `backup_test.py` owns the runtime implementation.
- `backup_test.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `BackupTest` (`ApiHandler`)
  - `requires_auth(cls) -> bool`
  - `requires_loopback(cls) -> bool`
  - `async process(self, input: dict, request: Request) -> dict | Response`

## Runtime Contracts

- HTTP handlers must derive from `helpers.api.ApiHandler`; WebSocket handlers must derive from `helpers.ws.WsHandler`.
- Update this file whenever request payloads, authentication or CSRF requirements, response shapes, route side effects, or WebSocket event contracts change.
- `BackupTest` is an `ApiHandler`.
- `BackupTest` defines `process(...)`.
- `BackupTest` defines `requires_auth(...)`.
- `BackupTest` defines `requires_loopback(...)`.
- Imported dependency areas include: `helpers.api`, `helpers.backup`.
- The `truncated` response flag is true only when a finite `max_files` limit is supplied and the result reaches that limit.

## Key Concepts

- Important called helpers/classes observed in the source: `BackupService`, `backup_service.test_patterns`, `line.strip`, `line.startswith`, `patterns_string.split`, `line.strip.startswith`.
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
