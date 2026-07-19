# rate_limiter.py DOX

## Purpose

- Own the `rate_limiter.py` helper module.
- This module provides simple rate-limiting primitives.
- Keep this file-level DOX profile synchronized with `rate_limiter.py` because this directory is intentionally flat.

## Ownership

- `rate_limiter.py` owns the runtime implementation.
- `rate_limiter.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `RateLimiter` (no explicit base class)
  - `add(self, **kwargs)`
  - `async cleanup(self)`
  - `async get_total(self, key: str) -> int`
  - `async wait(self, callback: Callable[[str, str, int, int], Awaitable[bool]] | None=...)`

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Imported dependency areas include: `asyncio`, `time`, `typing`.

## Key Concepts

- Important called helpers/classes observed in the source: `asyncio.Lock`, `time.time`, `self.cleanup`, `asyncio.sleep`, `self.get_total`, `callback`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve public helper APIs used by core code and plugins unless every caller is updated.
- Keep path, auth, secret, persistence, network, and subprocess behavior explicit and bounded.
- Prefer adding cohesive helper functions here only when behavior is reused across modules.

## Verification

- Run targeted tests for changed helper behavior; run security regressions for auth, filesystem, WebSocket, tunnel, upload, or secret-handling helpers.
- Related tests observed by source search:
  - `tests/test_stream_tool_early_stop.py`

## Child DOX Index

No child DOX files.
