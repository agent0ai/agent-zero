# skills.py DOX

## Purpose

- Own the `skills.py` API endpoint.
- This module lists and manages available skills for settings and agent-facing skill flows.
- Keep this file-level DOX profile synchronized with `skills.py` because this directory is intentionally flat.

## Ownership

- `skills.py` owns the runtime implementation.
- `skills.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `Skills` (`ApiHandler`)
  - `async process(self, input: Input, request: Request) -> Output`
  - `list_skills(self, input: Input)`
  - `delete_skill(self, input: Input)`

## Runtime Contracts

- HTTP handlers must derive from `helpers.api.ApiHandler`; WebSocket handlers must derive from `helpers.ws.WsHandler`.
- Update this file whenever request payloads, authentication or CSRF requirements, response shapes, route side effects, or WebSocket event contracts change.
- `Skills` is an `ApiHandler`.
- `Skills` defines `process(...)`.
- Observed side-effect areas: filesystem reads, filesystem deletion.
- Imported dependency areas include: `helpers`, `helpers.api`.

## Key Concepts

- Important called helpers/classes observed in the source: `skills.list_skills`, `result.sort`, `str.strip`, `skills.delete_skill`, `projects.get_project_folder`, `runtime.is_development`, `Exception`, `self.list_skills`, `strip`, `files.normalize_a0_path`, `files.get_abs_path`, `self.delete_skill`, `files.is_in_dir`, `projects.get_project_meta`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve authentication, CSRF, loopback, and API-key checks unless the endpoint contract explicitly changes.
- Update frontend callers, plugin callers, and tests together when payload shape changes.
- Use `helpers.api.Response` for non-JSON responses, files, redirects, or status-specific replies.

## Verification

- Run endpoint-specific or API/WebSocket tests for changed behavior; smoke-test browser callers when no focused test exists.
- Related tests observed by source search:
  - `tests/test_a0_connector_prompt_gating.py`
  - `tests/test_browser_agent_regressions.py`
  - `tests/test_document_query_plugin.py`
  - `tests/test_fasta2a_client.py`
  - `tests/test_office_canvas_setup.py`
  - `tests/test_office_document_store.py`
  - `tests/test_skills_runtime.py`
  - `tests/test_time_travel.py`

## Child DOX Index

No child DOX files.
