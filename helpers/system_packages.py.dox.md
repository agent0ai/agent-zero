# system_packages.py DOX

## Purpose

- Own the `system_packages.py` helper module.
- Run serialized APT operations with lock retries and the shared Desktop/Office repair policy.
- Keep this file-level DOX profile synchronized with `system_packages.py` because this directory is intentionally flat.

## Ownership

- `system_packages.py` owns the runtime implementation.
- `system_packages.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Top-level functions:
- `run_runtime_apt(command, timeout)`: Run a runtime repair command with the shared Kali compatibility policy. Migrate the two standard source files to `kali-last-snapshot`, preserving mirror/key/architecture settings. Commands pass through unchanged; source I/O failures propagate to the caller.
- `run_apt_with_retries(runner: Callable[[], subprocess.CompletedProcess[str]], lock_timeout_seconds: int=..., retry_seconds: int=...) -> subprocess.CompletedProcess[str]`: Run an apt/dpkg command, serializing in-process callers and waiting out apt locks.
- `is_apt_lock_error(result: subprocess.CompletedProcess[str]) -> bool`
- Notable constants/configuration names: `APT_LOCK_TIMEOUT_SECONDS`, `APT_LOCK_RETRY_SECONDS`, `KALI_SUITE`, `KALI_SOURCE_FILES`.

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Side effects: subprocess/runtime control and idempotent edits to `/etc/apt/sources.list` and `/etc/apt/sources.list.d/kali.sources` on Kali. Other distributions retain their existing package policy.
- Dependencies: standard-library `os`, `platform`, `pathlib`, `subprocess`, `threading`, `time`, and `typing`.

## Key Concepts

- Important called helpers/classes observed in the source: `threading.RLock`, `lower`, `time.monotonic`, `runner`, `time.sleep`, `is_apt_lock_error`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve public helper APIs used by core code and plugins unless every caller is updated.
- Keep path, auth, secret, persistence, network, and subprocess behavior explicit and bounded.
- Prefer adding cohesive helper functions here only when behavior is reused across modules.

## Verification

- Run targeted tests for changed helper behavior; run security regressions for auth, filesystem, WebSocket, tunnel, upload, or secret-handling helpers.
- Related tests observed by source search:
  - `tests/test_office_document_store.py`
  - `tests/test_system_packages.py`

## Child DOX Index

No child DOX files.
