# tokens.py DOX

## Purpose

- Own the `tokens.py` helper module.
- This module counts and approximates tokens and trims text to budgets.
- Keep this file-level DOX profile synchronized with `tokens.py` because this directory is intentionally flat.

## Ownership

- `tokens.py` owns the runtime implementation.
- `tokens.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Top-level functions:
- `count_tokens(text: str, encoding_name=...) -> int`
- `approximate_tokens(text: str) -> int`
- `sanitize_embedded_image_data_urls(text: str) -> str`
- `approximate_prompt_tokens(text: str) -> int`
- `trim_to_tokens(text: str, max_tokens: int, direction: Literal['start', 'end'], ellipsis: str=...) -> str`
- Notable constants/configuration names: `APPROX_BUFFER`, `TRIM_BUFFER`, `EMBEDDED_IMAGE_DATA_PLACEHOLDER`, `_EMBEDDED_IMAGE_DATA_URL_PATTERN`.

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Observed side-effect areas: secret handling.
- Imported dependency areas include: `re`, `tiktoken`, `typing`.

## Key Concepts

- Important called helpers/classes observed in the source: `re.compile`, `tiktoken.get_encoding`, `encoding.encode`, `_EMBEDDED_IMAGE_DATA_URL_PATTERN.sub`, `approximate_tokens`, `count_tokens`, `sanitize_embedded_image_data_urls`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve public helper APIs used by core code and plugins unless every caller is updated.
- Keep path, auth, secret, persistence, network, and subprocess behavior explicit and bounded.
- Prefer adding cohesive helper functions here only when behavior is reused across modules.

## Verification

- Run targeted tests for changed helper behavior; run security regressions for auth, filesystem, WebSocket, tunnel, upload, or secret-handling helpers.
- Related tests observed by source search:
  - `tests/test_chat_compaction.py`
  - `tests/test_default_prompt_budget.py`
  - `tests/test_history_compression_wait.py`
  - `tests/test_mcp_handler_multimodal.py`
  - `tests/test_oauth_codex.py`
  - `tests/test_oauth_gemini_api.py`
  - `tests/test_oauth_xai_grok.py`
  - `tests/test_ws_security.py`

## Child DOX Index

No child DOX files.
