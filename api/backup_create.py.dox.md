# backup_create.py DOX

## Purpose

- Own the `backup_create.py` API endpoint.
- This module handles backup create requests.
- Keep this file-level DOX profile synchronized with `backup_create.py` because this directory is intentionally flat.

## Ownership

- `backup_create.py` owns the runtime implementation.
- `backup_create.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `BackupCreate` (`ApiHandler`)
  - `requires_auth(cls) -> bool`
  - `requires_loopback(cls) -> bool`
  - `async process(self, input: dict, request: Request) -> dict | Response`

## Runtime Contracts

- HTTP handlers must derive from `helpers.api.ApiHandler`; WebSocket handlers must derive from `helpers.ws.WsHandler`.
- Update this file whenever request payloads, authentication or CSRF requirements, response shapes, route side effects, or WebSocket event contracts change.
- `BackupCreate` is an `ApiHandler`.
- `BackupCreate` defines `process(...)`.
- `BackupCreate` defines `requires_auth(...)`.
- `BackupCreate` defines `requires_loopback(...)`.
- Observed side-effect areas: filesystem writes.
- Imported dependency areas include: `helpers.api`, `helpers.backup`, `helpers.persist_chat`.

## Key Concepts

- Important called helpers/classes observed in the source: `save_tmp_chats`, `BackupService`, `send_file`, `backup_service.create_backup`, `line.strip`, `line.startswith`, `patterns_string.split`, `line.strip.startswith`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve authentication, CSRF, loopback, and API-key checks unless the endpoint contract explicitly changes.
- Update frontend callers, plugin callers, and tests together when payload shape changes.
- Use `helpers.api.Response` for non-JSON responses, files, redirects, or status-specific replies.

## Verification

- Run endpoint-specific or API/WebSocket tests for changed behavior; smoke-test browser callers when no focused test exists.
- Related tests observed by source search:
  - `tests/test_download_toast_regressions.py`

## Child DOX Index

No child DOX files.
