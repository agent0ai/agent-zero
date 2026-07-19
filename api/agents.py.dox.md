# agents.py DOX

## Purpose

- Own the `agents.py` API endpoint.
- This module lists available agent profiles for selection and delegation UI flows.
- Keep this file-level DOX profile synchronized with `agents.py` because this directory is intentionally flat.

## Ownership

- `agents.py` owns the runtime implementation.
- `agents.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `Agents` (`ApiHandler`)
  - `async process(self, input: Input, request: Request) -> Output`

## Runtime Contracts

- HTTP handlers must derive from `helpers.api.ApiHandler`; WebSocket handlers must derive from `helpers.ws.WsHandler`.
- Update this file whenever request payloads, authentication or CSRF requirements, response shapes, route side effects, or WebSocket event contracts change.
- `Agents` is an `ApiHandler`.
- `Agents` defines `process(...)`.
- Imported dependency areas include: `helpers`, `helpers.api`.

## Key Concepts

- Important called helpers/classes observed in the source: `subagents.get_all_agents_list`, `Exception`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve authentication, CSRF, loopback, and API-key checks unless the endpoint contract explicitly changes.
- Update frontend callers, plugin callers, and tests together when payload shape changes.
- Use `helpers.api.Response` for non-JSON responses, files, redirects, or status-specific replies.

## Verification

- Run endpoint-specific or API/WebSocket tests for changed behavior; smoke-test browser callers when no focused test exists.
- Related tests observed by source search:
  - `tests/test_default_prompt_budget.py`
  - `tests/test_office_document_store.py`
  - `tests/test_projects.py`
  - `tests/test_skills_runtime.py`
  - `tests/test_time_travel.py`

## Child DOX Index

No child DOX files.
