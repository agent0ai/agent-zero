# docker.py DOX

## Purpose

- Own the `docker.py` helper module.
- This module manages Docker container operations used by runtime helpers.
- Keep this file-level DOX profile synchronized with `docker.py` because this directory is intentionally flat.

## Ownership

- `docker.py` owns the runtime implementation.
- `docker.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `DockerContainerManager` (no explicit base class)
  - `init_docker(self)`
  - `cleanup_container(self) -> None`
  - `get_image_containers(self)`
  - `start_container(self) -> None`

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Observed side-effect areas: filesystem reads, filesystem deletion, subprocess/runtime control, WebSocket state.
- Imported dependency areas include: `atexit`, `docker`, `helpers.errors`, `helpers.files`, `helpers.log`, `helpers.print_style`, `time`, `typing`.

## Key Concepts

- Important called helpers/classes observed in the source: `self.init_docker`, `PrintStyle.standard`, `self.client.containers.run`, `time.sleep`, `docker.from_env`, `self.container.stop`, `self.container.remove`, `existing_container.start`, `self.logger.log`, `format_error`, `PrintStyle.error`, `PrintStyle.hint`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve public helper APIs used by core code and plugins unless every caller is updated.
- Keep path, auth, secret, persistence, network, and subprocess behavior explicit and bounded.
- Prefer adding cohesive helper functions here only when behavior is reused across modules.

## Verification

- Run targeted tests for changed helper behavior; run security regressions for auth, filesystem, WebSocket, tunnel, upload, or secret-handling helpers.
- Related tests observed by source search:
  - `tests/test_browser_agent_regressions.py`
  - `tests/test_default_prompt_budget.py`
  - `tests/test_docker_release_plan.py`
  - `tests/test_document_query_plugin.py`
  - `tests/test_host_browser_connector.py`
  - `tests/test_model_search.py`
  - `tests/test_office_canvas_setup.py`
  - `tests/test_office_document_store.py`

## Child DOX Index

No child DOX files.
