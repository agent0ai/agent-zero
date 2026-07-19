# plugins.py DOX

## Purpose

- Own the `plugins.py` API endpoint.
- This module manages plugin actions and plugin settings through the core API.
- Keep this file-level DOX profile synchronized with `plugins.py` because this directory is intentionally flat.

## Ownership

- `plugins.py` owns the runtime implementation.
- `plugins.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `Plugins` (`ApiHandler`)
  - `async process(self, input: dict, request: Request) -> dict | Response`

## Runtime Contracts

- HTTP handlers must derive from `helpers.api.ApiHandler`; WebSocket handlers must derive from `helpers.ws.WsHandler`.
- Update this file whenever request payloads, authentication or CSRF requirements, response shapes, route side effects, or WebSocket event contracts change.
- `Plugins` is an `ApiHandler`.
- `Plugins` defines `process(...)`.
- Observed side-effect areas: filesystem reads, filesystem writes, filesystem deletion, subprocess/runtime control, plugin state, settings/state persistence.
- Imported dependency areas include: `helpers`, `helpers.api`, `helpers.localization`, `json`, `os`, `subprocess`, `sys`.

## Key Concepts

- Important called helpers/classes observed in the source: `Response`, `plugins.find_plugin_assets`, `plugins.get_plugin_meta`, `plugins.get_default_plugin_config`, `plugins.save_plugin_config`, `plugins.toggle_plugin`, `plugins.find_plugin_dir`, `files.get_abs_path`, `Localization.get.now_iso`, `plugins.determine_plugin_asset_path`, `self._get_config`, `self._get_toggle_status`, `self._list_configs`, `self._delete_config`, `self._delete_plugin`, `self._get_default_config`, `self._save_config`, `self._toggle_plugin`, `self._get_doc`, `self._run_execute_script`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve authentication, CSRF, loopback, and API-key checks unless the endpoint contract explicitly changes.
- Update frontend callers, plugin callers, and tests together when payload shape changes.
- Use `helpers.api.Response` for non-JSON responses, files, redirects, or status-specific replies.

## Verification

- Run endpoint-specific or API/WebSocket tests for changed behavior; smoke-test browser callers when no focused test exists.
- Related tests observed by source search:
  - `tests/test_a0_connector_computer_use_metadata.py`
  - `tests/test_a0_connector_prompt_gating.py`
  - `tests/test_browser_agent_regressions.py`
  - `tests/test_chat_compaction.py`
  - `tests/test_default_prompt_budget.py`
  - `tests/test_document_query_plugin.py`
  - `tests/test_error_retry_plugin.py`
  - `tests/test_host_browser_connector.py`

## Child DOX Index

No child DOX files.
