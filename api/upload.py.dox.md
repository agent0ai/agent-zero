# upload.py DOX

## Purpose

- Own the `upload.py` API endpoint.
- This module accepts general uploads into runtime upload storage.
- Keep this file-level DOX profile synchronized with `upload.py` because this directory is intentionally flat.

## Ownership

- `upload.py` owns the runtime implementation.
- `upload.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `UploadFile` (`ApiHandler`)
  - `async process(self, input: dict, request: Request) -> dict | Response`
  - `allowed_file(self, filename)`
- Top-level functions:
- `save_upload_atomic(file_storage, target_path) -> dict`: Stream one upload to
  a same-directory `.partial-*` file, hash and fsync it, atomically replace the
  final path, fsync the directory where supported, and remove the partial on
  every failure.

## Runtime Contracts

- `save_upload_atomic` accepts an optional byte ceiling for temporary host File Browser receipts; exceeding it removes the partial file and preserves the destination. Ordinary upload callers retain their existing limit policy.

- HTTP handlers must derive from `helpers.api.ApiHandler`; WebSocket handlers must derive from `helpers.ws.WsHandler`.
- Update this file whenever request payloads, authentication or CSRF requirements, response shapes, route side effects, or WebSocket event contracts change.
- `UploadFile` is an `ApiHandler`.
- `UploadFile` defines `process(...)`.
- The response retains legacy `filenames` and adds ordered `files` entries with
  `filename`, byte `size`, and `sha256` so streaming clients can verify what Core
  committed.
- Observed side-effect areas: filesystem reads, settings/state persistence.
- Imported dependency areas include: `helpers`, `helpers.api`, `helpers.security`.

## Key Concepts

- Important called helpers/classes observed in the source: `request.files.getlist`, `Exception`, `self.allowed_file`, `safe_filename`, `file.save`, `files.get_abs_path`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve authentication, CSRF, loopback, and API-key checks unless the endpoint contract explicitly changes.
- Update frontend callers, plugin callers, and tests together when payload shape changes.
- Use `helpers.api.Response` for non-JSON responses, files, redirects, or status-specific replies.

## Verification

- Run endpoint-specific or API/WebSocket tests for changed behavior; smoke-test browser callers when no focused test exists.
- Related tests observed by source search:
  - `tests/test_browser_agent_regressions.py`
  - `tests/test_image_get_security.py`

## Child DOX Index

No child DOX files.
