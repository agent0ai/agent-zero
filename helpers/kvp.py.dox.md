# kvp.py DOX

## Purpose

- Own the `kvp.py` helper module.
- This module provides runtime and persistent key-value storage helpers.
- Keep this file-level DOX profile synchronized with `kvp.py` because this directory is intentionally flat.

## Ownership

- `kvp.py` owns the runtime implementation.
- `kvp.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Top-level functions:
- `_persistent_dir() -> str`
- `_validate_key(key: str) -> None`
- `_key_to_path(key: str) -> str`
- `get_runtime(key: str, default: Any=...) -> Any`
- `set_runtime(key: str, value: Any) -> None`
- `remove_runtime(key: str) -> None`
- `find_runtime(pattern: str) -> list[str]`
- `get_persistent(key: str, default: Any=...) -> Any`
- `set_persistent(key: str, value: Any) -> None`
- `remove_persistent(key: str) -> None`
- `find_persistent(pattern: str) -> list[str]`

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Observed side-effect areas: filesystem reads, filesystem writes, filesystem deletion, settings/state persistence.
- Imported dependency areas include: `fnmatch`, `glob`, `helpers.files`, `json`, `os`, `tempfile`, `threading`, `typing`.

## Key Concepts

- Important called helpers/classes observed in the source: `threading.RLock`, `get_abs_path`, `_validate_key`, `os.path.join`, `_key_to_path`, `os.path.dirname`, `_persistent_dir`, `ValueError`, `_runtime_store.pop`, `os.makedirs`, `tempfile.mkstemp`, `glob.glob`, `keys.sort`, `os.replace`, `os.unlink`, `os.path.isdir`, `json.load`, `os.fdopen`, `json.dump`, `f.flush`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve public helper APIs used by core code and plugins unless every caller is updated.
- Keep path, auth, secret, persistence, network, and subprocess behavior explicit and bounded.
- Prefer adding cohesive helper functions here only when behavior is reused across modules.

## Verification

- Run targeted tests for changed helper behavior; run security regressions for auth, filesystem, WebSocket, tunnel, upload, or secret-handling helpers.
- Related tests observed by source search:
  - `tests/test_browser_agent_regressions.py`

## Child DOX Index

No child DOX files.
