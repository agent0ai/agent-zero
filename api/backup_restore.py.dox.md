# backup_restore.py DOX

## Purpose

- Own the `backup_restore.py` API endpoint.
- This module handles backup restore requests.
- Keep this file-level DOX profile synchronized with `backup_restore.py` because this directory is intentionally flat.

## Ownership

- `backup_restore.py` owns the runtime implementation.
- `backup_restore.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `BackupRestore` (`ApiHandler`)
  - `requires_auth(cls) -> bool`
  - `requires_loopback(cls) -> bool`
  - `async process(self, input: dict, request: Request) -> dict | Response`

## Runtime Contracts

- HTTP handlers must derive from `helpers.api.ApiHandler`; WebSocket handlers must derive from `helpers.ws.WsHandler`.
- Update this file whenever request payloads, authentication or CSRF requirements, response shapes, route side effects, or WebSocket event contracts change.
- `BackupRestore` is an `ApiHandler`.
- `BackupRestore` defines `process(...)`.
- `BackupRestore` defines `requires_auth(...)`.
- `BackupRestore` defines `requires_loopback(...)`.
- Observed side-effect areas: filesystem writes, filesystem deletion, settings/state persistence.
- Imported dependency areas include: `helpers.api`, `helpers.backup`, `helpers.persist_chat`, `json`, `werkzeug.datastructures`.

## Key Concepts

- Important called helpers/classes observed in the source: `request.form.get.lower`, `json.loads`, `BackupService`, `load_tmp_chats`, `backup_service.restore_backup`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve authentication, CSRF, loopback, and API-key checks unless the endpoint contract explicitly changes.
- Update frontend callers, plugin callers, and tests together when payload shape changes.
- Use `helpers.api.Response` for non-JSON responses, files, redirects, or status-specific replies.

## Verification

- Run endpoint-specific or API/WebSocket tests for changed behavior; smoke-test browser callers when no focused test exists.
- Related tests observed by source search:
  - `tests/test_self_update_tag_filter.py`

## Child DOX Index

No child DOX files.
