# browser.py DOX

## Purpose

- Own the `browser.py` helper module.
- This module holds shared browser helper state used by browser-facing integrations.
- Keep this file-level DOX profile synchronized with `browser.py` because this directory is intentionally flat.

## Ownership

- `browser.py` owns the runtime implementation.
- `browser.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Observed side-effect areas: filesystem reads, filesystem deletion.

## Key Concepts

- This module is primarily declarative or delegates behavior through classes/imported objects.
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
  - `tests/test_download_toast_regressions.py`
  - `tests/test_host_browser_connector.py`
  - `tests/test_oauth_gemini_api.py`
  - `tests/test_oauth_providers.py`
  - `tests/test_oauth_static.py`
  - `tests/test_oauth_xai_grok.py`

## Child DOX Index

No child DOX files.
