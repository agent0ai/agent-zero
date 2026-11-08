# print_style.py DOX

## Purpose

- Own the `print_style.py` helper module.
- This module formats console/debug output and persists plain application logs.
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
- `print()` and `stream()` append UTF-8 plain text to one uniquely created `log_<UTC timestamp>_<random>.log` per process under `files.get_abs_path(files.USER_DIR, "logs")`. Creation is lazy, uses owner-only file permissions, and never truncates a prior run. The directory follows the native project root or mounted Docker `/a0/usr`.
- File output preserves payload whitespace, Unicode, literal markup/entities, prefixes and the console's padding/line boundaries. Streaming appends without inserting chunk separators. CSI/OSC terminal escapes (including split chunks) and non-whitespace control characters are removed only from the file sink; no HTML wrappers or encoding are added.
- Incomplete escapes carry only between consecutive stream chunks. A print/padding boundary discards pending control state, and a print's explicit ending is sanitized separately so an unfinished payload escape cannot swallow that ending or later records.
- A shared reentrant lock keeps each print/stream operation and its file append ordered across threads. File handles close after each write; there is no retention/deletion policy.
- Secret masking remains in `get()` and upstream model streaming filters. The file sink masks again after terminal-control removal and substitutes an omission marker if masking fails; console fallback behavior is unchanged. Callers streaming raw secret fragments still need the existing `StreamingSecretsFilter`, as model stream hooks already do.
- `log_only=True` suppresses console output but persists the file output. Filesystem errors report a fixed warning to stderr and leave the application/console running; subsequent writes retry.
- Structured chat logs, chat persistence, Supervisor stdout/stderr, self-update and sandbox diagnostic logs retain their existing contracts. User-data mounts/backups include the new application files; historical top-level logs remain untouched.
- `get()` preserves its plain-text, ANSI-styled, and HTML-styled return values for existing callers and does not write files.
- Imported dependency areas include: `collections.abc`, `datetime`, `files`, `html`, `os`, `re`, `strings`, `sys`, `tempfile`, `threading`, `webcolors`.

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
  - `tests/test_plain_response_logging.py`
  - `tests/test_warning_log_prefixes.py`
  - `tests/test_persist_chat_log_ids.py`
  - `tests/test_tool_action_contracts.py`
  - `tests/test_ws_manager.py`

## Child DOX Index

No child DOX files.
