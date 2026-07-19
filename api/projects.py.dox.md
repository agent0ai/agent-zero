# projects.py DOX

## Purpose

- Own the `projects.py` API endpoint.
- This module manages project create, update, delete, clone, and metadata flows.
- Keep this file-level DOX profile synchronized with `projects.py` because this directory is intentionally flat.

## Ownership

- `projects.py` owns the runtime implementation.
- `projects.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `Projects` (`ApiHandler`)
  - `async process(self, input: Input, request: Request) -> Output`
  - `get_active_projects_list(self)`
  - `get_active_projects_options(self)`
  - `create_project(self, project: dict | None)`
  - `clone_project(self, project: dict | None)`
  - `load_project(self, name: str | None)`
  - `update_project(self, project: dict | None)`
  - `delete_project(self, name: str | None)`

## Runtime Contracts

- HTTP handlers must derive from `helpers.api.ApiHandler`; WebSocket handlers must derive from `helpers.ws.WsHandler`.
- Update this file whenever request payloads, authentication or CSRF requirements, response shapes, route side effects, or WebSocket event contracts change.
- `Projects` is an `ApiHandler`.
- `Projects` defines `process(...)`.
- Observed side-effect areas: filesystem deletion, settings/state persistence.
- Imported dependency areas include: `helpers`, `helpers.api`, `helpers.notification`.

## Key Concepts

- Important called helpers/classes observed in the source: `projects.get_active_projects_list`, `projects.BasicProjectData`, `projects.create_project`, `projects.load_edit_project_data`, `NotificationManager.send_notification`, `projects.EditProjectData`, `projects.update_project`, `projects.delete_project`, `projects.activate_project`, `projects.deactivate_project`, `projects.load_basic_project_data`, `projects.get_file_structure`, `self.use_context`, `Exception`, `projects.clone_git_project`, `self.get_active_projects_list`, `self.get_active_projects_options`, `self.load_project`, `self.create_project`, `self.clone_project`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve authentication, CSRF, loopback, and API-key checks unless the endpoint contract explicitly changes.
- Update frontend callers, plugin callers, and tests together when payload shape changes.
- Use `helpers.api.Response` for non-JSON responses, files, redirects, or status-specific replies.

## Verification

- Run endpoint-specific or API/WebSocket tests for changed behavior; smoke-test browser callers when no focused test exists.
- Related tests observed by source search:
  - `tests/test_model_config_project_presets.py`
  - `tests/test_office_document_store.py`
  - `tests/test_plugin_activation_ui.py`
  - `tests/test_projects.py`
  - `tests/test_skills_runtime.py`
  - `tests/test_task_scheduler_timezone.py`
  - `tests/test_time_travel.py`
  - `tests/test_tool_action_contracts.py`

## Child DOX Index

No child DOX files.
