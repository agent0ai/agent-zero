# print_style.py DOX

## Purpose

- Own the `print_style.py` helper module.
- This module formats console/debug output consistently.
- Keep this file-level DOX profile synchronized with `print_style.py` because this directory is intentionally flat.

## Ownership

- `print_style.py` owns the runtime implementation.
- `print_style.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `PrintStyle` (no explicit base class)
  - `get(self, *args, sep=..., **kwargs)`
  - `print(self, *args, sep=..., end=..., flush=...)`
  - `stream(self, *args, sep=..., flush=...)`
  - `is_last_line_empty(self)`
  - `standard(*args, sep=..., end=..., flush=...)`
  - `hint(*args, sep=..., end=..., flush=...)`
  - `info(*args, sep=..., end=..., flush=...)`
  - `success(*args, sep=..., end=..., flush=...)`
- Top-level functions:
- `_get_runtime()`

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- `PrintStyle` emits sanitized, secret-masked console output and does not create filesystem log files.
- `get()` preserves its plain-text, ANSI-styled, and HTML-styled return values for existing callers.
- Imported dependency areas include: `collections.abc`, `files`, `html`, `strings`, `sys`, `webcolors`.

## Key Concepts

- Important called helpers/classes observed in the source: `self._get_rgb_color_code`, `html.escape.replace`, `sep.join`, `self._format_args`, `sanitize_string`, `self._add_padding_if_needed`, `end.endswith`, `sys.stdin.readlines`, `PrintStyle._prefixed_args`, `self.secrets_mgr.mask_values`, `self._get_styled_text`, `self._get_html_styled_text`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve public helper APIs used by core code and plugins unless every caller is updated.
- Keep path, auth, secret, persistence, network, and subprocess behavior explicit and bounded.
- Prefer adding cohesive helper functions here only when behavior is reused across modules.

## Verification

- Run targeted tests for changed helper behavior; run security regressions for auth, filesystem, WebSocket, tunnel, upload, or secret-handling helpers.
- Related tests observed by source search:
  - `tests/test_print_style.py`
  - `tests/test_tool_action_contracts.py`
  - `tests/test_ws_manager.py`

## Child DOX Index

No child DOX files.
