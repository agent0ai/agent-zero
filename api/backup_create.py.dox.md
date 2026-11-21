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
- POST requests without `action` retain the synchronous ZIP response and legacy `patterns` support.
- `action: start` accepts the existing backup metadata and immediately returns `{success, job_id, status: "running"}`. Chat persistence and archive generation run in a dedicated worker.
- `action: status` accepts `job_id` and returns `running`, `completed`, or `failed`; failed results include an error message. Jobs live in the current server process.
- `action: download` accepts `job_id` and streams the completed ZIP with its original download name. It holds an archive lease until WSGI closes the response, including interrupted downloads.
- Job actions return JSON errors with HTTP 400 for invalid actions/names, 404 with `code: "backup_not_found"` for missing/expired jobs, 409 for busy/not-ready jobs, and 500 for unexpected failures. Detailed unexpected exceptions remain in the server log.
- Every action retains authentication and CSRF protection. Clients provide opaque job IDs; archive paths remain server-owned. One active job or download is allowed per process; results expire one hour after completion or when another backup starts.
- Observed side-effect areas: filesystem writes.
- Imported dependency areas include: `helpers.api`, `helpers.backup`, `helpers.persist_chat`.

## Key Concepts

- Background download responses include `Content-Length` and `X-Content-SHA256`. The digest is prepared by the background worker before completion and reused for each download.

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
  - `tests/test_backup_jobs.py`
  - `tests/test_backup_store.mjs`

## Child DOX Index

No child DOX files.
