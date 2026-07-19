# ephemeral_images.py DOX

## Purpose

- Own the `ephemeral_images.py` helper module.
- This module stores temporary image payloads by reference for safe short-lived access.
- Keep this file-level DOX profile synchronized with `ephemeral_images.py` because this directory is intentionally flat.

## Ownership

- `ephemeral_images.py` owns the runtime implementation.
- `ephemeral_images.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `EphemeralImage` (no explicit base class)
  - `data_url(self) -> str`
  - `display_name(self) -> str`
- Top-level functions:
- `put_image_bytes(context_id: str, mime: str, payload: bytes, name: str=..., ttl_seconds: float=...) -> str`
- `put_image(context_id: str, mime: str, data: str, name: str=..., ttl_seconds: float=...) -> str`
- `is_ref(value: object) -> bool`
- `display_ref(ref: str) -> str`
- `get_image(ref: str, context_id: str=...) -> EphemeralImage | None`
- `consume_image(ref: str, context_id: str=...) -> EphemeralImage | None`
- `delete_image(ref: str) -> None`
- `clear_context(context_id: str) -> None`
- `_resolve_image(ref: str, context_id: str=..., consume: bool) -> EphemeralImage | None`
- `_compact_base64(data: str) -> str`
- `_normalize_mime(mime: str) -> str`
- `_prune_expired_locked(now: float | None=...) -> None`
- Notable constants/configuration names: `REF_PREFIX`, `DEFAULT_TTL_SECONDS`.

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Observed side-effect areas: filesystem deletion.
- Imported dependency areas include: `__future__`, `base64`, `dataclasses`, `threading`, `time`, `uuid`.

## Key Concepts

- Important called helpers/classes observed in the source: `dataclass`, `threading.RLock`, `base64.b64encode.decode`, `put_image`, `_compact_base64`, `base64.b64decode`, `_normalize_mime`, `time.time`, `EphemeralImage`, `str.strip.startswith`, `str.strip`, `_resolve_image`, `join`, `str.strip.lower`, `ValueError`, `_prune_expired_locked`, `is_ref`, `_store.pop`, `value.startswith`, `display_ref`.
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
