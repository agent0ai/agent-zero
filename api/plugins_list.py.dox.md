# plugins_list.py DOX

## Purpose

- Own the `plugins_list.py` API endpoint.
- This module returns plugin inventory and activation metadata for plugin UI surfaces.
- Keep this file-level DOX profile synchronized with `plugins_list.py` because this directory is intentionally flat.

## Ownership

- `plugins_list.py` owns the runtime implementation.
- `plugins_list.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `PluginsList` (`ApiHandler`)
  - `async process(self, input: Input, request: Request) -> Output`

## Runtime Contracts

- HTTP handlers must derive from `helpers.api.ApiHandler`; WebSocket handlers must derive from `helpers.ws.WsHandler`.
- Update this file whenever request payloads, authentication or CSRF requirements, response shapes, route side effects, or WebSocket event contracts change.
- `PluginsList` is an `ApiHandler`.
- `PluginsList` defines `process(...)`.
- Observed side-effect areas: plugin state, settings/state persistence.
- Imported dependency areas include: `helpers`, `helpers.api`.

## Key Concepts

- Important called helpers/classes observed in the source: `plugins.get_enhanced_plugins_list`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve authentication, CSRF, loopback, and API-key checks unless the endpoint contract explicitly changes.
- Update frontend callers, plugin callers, and tests together when payload shape changes.
- Use `helpers.api.Response` for non-JSON responses, files, redirects, or status-specific replies.

## Verification

- Run endpoint-specific or API/WebSocket tests for changed behavior; smoke-test browser callers when no focused test exists.
- Related tests observed by source search:
  - `tests/test_plugin_activation_ui.py`
  - `tests/test_speech_plugin_split.py`

## Child DOX Index

No child DOX files.
