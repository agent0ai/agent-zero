# yaml.py DOX

## Purpose

- Own the `yaml.py` helper module.
- This module wraps YAML loading/dumping and JSON conversion helpers.
- Keep this file-level DOX profile synchronized with `yaml.py` because this directory is intentionally flat.

## Ownership

- `yaml.py` owns the runtime implementation.
- `yaml.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Top-level functions:
- `loads(text: str)`
- `dumps(obj, **kwargs) -> str`
- `from_json(text: str, **yaml_dump_kwargs) -> str`
- `to_json(text: str, **json_dump_kwargs) -> str`

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Observed side-effect areas: filesystem writes, settings/state persistence.
- Imported dependency areas include: `json`, `yaml`.

## Key Concepts

- Important called helpers/classes observed in the source: `yaml.safe_load`, `yaml.safe_dump`, `dumps`, `loads`, `json.dumps`, `json.loads`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve public helper APIs used by core code and plugins unless every caller is updated.
- Keep path, auth, secret, persistence, network, and subprocess behavior explicit and bounded.
- Prefer adding cohesive helper functions here only when behavior is reused across modules.

## Verification

- Run targeted tests for changed helper behavior; run security regressions for auth, filesystem, WebSocket, tunnel, upload, or secret-handling helpers.
- Related tests observed by source search:
  - `tests/test_a0_connector_prompt_gating.py`
  - `tests/test_browser_agent_regressions.py`
  - `tests/test_document_query_plugin.py`
  - `tests/test_model_config_api_keys.py`
  - `tests/test_model_config_project_presets.py`
  - `tests/test_oauth_codex.py`
  - `tests/test_oauth_providers.py`
  - `tests/test_office_canvas_setup.py`

## Child DOX Index

No child DOX files.
