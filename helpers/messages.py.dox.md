# messages.py DOX

## Purpose

- Own the `messages.py` helper module.
- This module truncates message payloads for display and storage safety.
- Keep this file-level DOX profile synchronized with `messages.py` because this directory is intentionally flat.

## Ownership

- `messages.py` owns the runtime implementation.
- `messages.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Top-level functions:
- `truncate_text(agent, output, threshold=...)`
- `truncate_dict_by_ratio(agent, data: dict | list | str, threshold_chars: int, truncate_to: int)`

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Observed side-effect areas: filesystem reads, filesystem writes, settings/state persistence.
- Imported dependency areas include: `json`.

## Key Concepts

- Important called helpers/classes observed in the source: `agent.read_prompt`, `process_item`, `json.dumps`, `truncate_text`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve public helper APIs used by core code and plugins unless every caller is updated.
- Keep path, auth, secret, persistence, network, and subprocess behavior explicit and bounded.
- Prefer adding cohesive helper functions here only when behavior is reused across modules.

## Verification

- Run targeted tests for changed helper behavior; run security regressions for auth, filesystem, WebSocket, tunnel, upload, or secret-handling helpers.
- Related tests observed by source search:
  - `tests/email_parser_test.py`
  - `tests/test_browser_agent_regressions.py`
  - `tests/test_chat_compaction.py`
  - `tests/test_document_query_fallback.py`
  - `tests/test_download_toast_regressions.py`
  - `tests/test_fasta2a_client.py`
  - `tests/test_mcp_handler_multimodal.py`
  - `tests/test_oauth_codex.py`

## Child DOX Index

No child DOX files.
