# skills_import.py DOX

## Purpose

- Own the `skills_import.py` API endpoint.
- This module handles skills import API requests.
- Keep this file-level DOX profile synchronized with `skills_import.py` because this directory is intentionally flat.

## Ownership

- `skills_import.py` owns the runtime implementation.
- `skills_import.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `SkillsImport` (`ApiHandler`)
  - `async process(self, input: dict, request: Request) -> dict | Response`

## Runtime Contracts

- HTTP handlers must derive from `helpers.api.ApiHandler`; WebSocket handlers must derive from `helpers.ws.WsHandler`.
- Update this file whenever request payloads, authentication or CSRF requirements, response shapes, route side effects, or WebSocket event contracts change.
- `SkillsImport` is an `ApiHandler`.
- `SkillsImport` defines `process(...)`.
- Observed side-effect areas: filesystem reads, filesystem writes, filesystem deletion.
- Imported dependency areas include: `__future__`, `helpers`, `helpers.api`, `helpers.skills_import`, `os`, `pathlib`, `time`, `uuid`, `werkzeug.datastructures`, `werkzeug.utils`.

## Key Concepts

- Important called helpers/classes observed in the source: `self.use_context`, `strip.lower`, `Path`, `tmp_dir.mkdir`, `secure_filename`, `time.strftime`, `skills_file.save`, `strip`, `files.get_abs_path`, `base.lower.endswith`, `import_skills`, `files.deabsolute_path`, `uuid.uuid4`, `tmp_path.unlink`, `base.lower`.
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
