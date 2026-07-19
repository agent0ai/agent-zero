# errors.py DOX

## Purpose

- Own the `errors.py` helper module.
- This module defines framework exceptions and safe error formatting.
- Keep this file-level DOX profile synchronized with `errors.py` because this directory is intentionally flat.

## Ownership

- `errors.py` owns the runtime implementation.
- `errors.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `RepairableException` (`Exception`)
- `InterventionException` (`Exception`)
- `HandledException` (`Exception`)
- Top-level functions:
- `handle_error(e: Exception)`
- `error_text(e: Exception)`
- `format_error(e: Exception, start_entries=..., end_entries=..., error_message_position: Literal['top', 'bottom', 'none']=...)`

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Imported dependency areas include: `asyncio`, `re`, `traceback`, `typing`.

## Key Concepts

- Important called helpers/classes observed in the source: `join`, `traceback_text.split`, `traceback.format_exception`, `re.match`, `type`, `line.strip.startswith`, `trimmed_lines.strip`, `error_message.strip`, `line.strip`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve public helper APIs used by core code and plugins unless every caller is updated.
- Keep path, auth, secret, persistence, network, and subprocess behavior explicit and bounded.
- Prefer adding cohesive helper functions here only when behavior is reused across modules.

## Verification

- Run targeted tests for changed helper behavior; run security regressions for auth, filesystem, WebSocket, tunnel, upload, or secret-handling helpers.
- Related tests observed by source search:
  - `tests/test_browser_agent_regressions.py`
  - `tests/test_fasta2a_client.py`
  - `tests/test_host_browser_connector.py`
  - `tests/test_office_desktop_state.py`
  - `tests/test_office_document_store.py`
  - `tests/test_skills_runtime.py`
  - `tests/test_speech_plugin_split.py`
  - `tests/test_time_travel.py`

## Child DOX Index

No child DOX files.
