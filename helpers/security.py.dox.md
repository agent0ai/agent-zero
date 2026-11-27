# security.py DOX

## Purpose

- Own the `security.py` helper module.
- This module contains small security helpers such as filename sanitization.
- Keep this file-level DOX profile synchronized with `security.py` because this directory is intentionally flat.

## Ownership

- `security.py` owns the runtime implementation.
- `security.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Top-level functions:
- `safe_filename(filename: str) -> Optional[str]`
- Notable constants/configuration names: `FORBIDDEN_CHARS_RE`, `WINDOWS_RESERVED`, `FILENAME_MAX_LENGTH`.

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- `safe_filename` is the shared framework upload-name cleaner: replace path separators and control characters, preserve Unicode, handle reserved names, and return `None` for an empty/dot-only name. Callers choose their existing rejection or fallback behavior before joining a trusted destination directory.
- Chat, API, file-browser, knowledge, Telegram, WhatsApp staging, email persistence, and skill/plugin archive uploads use this cleaner. It cleans a filename, not a directory or an archive member; retain separate containment, symlink, and archive checks.
- This helper has no filesystem side effects.
- Imported dependency areas include: `pathlib`, `re`, `typing`, `unicodedata`.

## Key Concepts

- Important called helpers/classes observed in the source: `re.compile`, `frozenset`, `unicodedata.normalize`, `FORBIDDEN_CHARS_RE.sub`, `filename.lstrip.rstrip`, `Path`, `join`, `stem.upper`, `filename.lstrip`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve public helper APIs used by core code and plugins unless every caller is updated.
- Keep path, auth, secret, persistence, network, and subprocess behavior explicit and bounded.
- Prefer adding cohesive helper functions here only when behavior is reused across modules.

## Verification

- Run targeted tests for changed helper behavior; run security regressions for auth, filesystem, WebSocket, tunnel, upload, or secret-handling helpers.
- Related tests observed by source search:
  - `tests/test_upload_filenames.py`
  - `tests/test_telegram_media_delivery.py`
  - `tests/test_fastmcp_openapi_security.py`
  - `tests/test_image_get_security.py`
  - `tests/test_ws_security.py`

## Child DOX Index

No child DOX files.
