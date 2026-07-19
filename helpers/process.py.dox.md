# process.py DOX

## Purpose

- Own the `process.py` helper module.
- This module manages process reload, restart, exit, and server references.
- Keep this file-level DOX profile synchronized with `process.py` because this directory is intentionally flat.

## Ownership

- `process.py` owns the runtime implementation.
- `process.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Top-level functions:
- `set_server(server)`
- `get_server(server)`
- `stop_server()`
- `reload()`
- `restart_process()`
- `exit_process()`

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Observed side-effect areas: subprocess/runtime control.
- Imported dependency areas include: `helpers`, `helpers.print_style`, `os`, `sys`.

## Key Concepts

- Important called helpers/classes observed in the source: `stop_server`, `runtime.is_dockerized`, `PrintStyle.standard`, `os.execv`, `sys.exit`, `_server.shutdown`, `exit_process`, `restart_process`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve public helper APIs used by core code and plugins unless every caller is updated.
- Keep path, auth, secret, persistence, network, and subprocess behavior explicit and bounded.
- Prefer adding cohesive helper functions here only when behavior is reused across modules.

## Verification

- Run targeted tests for changed helper behavior; run security regressions for auth, filesystem, WebSocket, tunnel, upload, or secret-handling helpers.
- Related tests observed by source search:
  - `tests/test_api_chat_lifetime.py`
  - `tests/test_browser_agent_regressions.py`
  - `tests/test_docker_release_plan.py`
  - `tests/test_document_query_plugin.py`
  - `tests/test_download_toast_regressions.py`
  - `tests/test_git_version_label.py`
  - `tests/test_image_get_security.py`
  - `tests/test_model_config_project_presets.py`

## Child DOX Index

No child DOX files.
