# performance.py DOX

## Purpose

- Own the `performance.py` helper module.
- This module provides lightweight performance tracing helpers.
- Keep this file-level DOX profile synchronized with `performance.py` because this directory is intentionally flat.

## Ownership

- `performance.py` owns the runtime implementation.
- `performance.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Top-level functions:
- `trace_performance(show_all=..., color=..., unicode=...)`: Decorator that profiles a function and prints a call tree when it finishes.

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Imported dependency areas include: `functools`, `inspect`, `pyinstrument`.

## Key Concepts

- Important called helpers/classes observed in the source: `inspect.iscoroutinefunction`, `functools.wraps`, `Profiler`, `profiler.start`, `profiler.stop`, `func`, `profiler.output_text`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve public helper APIs used by core code and plugins unless every caller is updated.
- Keep path, auth, secret, persistence, network, and subprocess behavior explicit and bounded.
- Prefer adding cohesive helper functions here only when behavior is reused across modules.

## Verification

- Run targeted tests for changed helper behavior; run security regressions for auth, filesystem, WebSocket, tunnel, upload, or secret-handling helpers.
- Related tests observed by source search:
  - `tests/test_extensions_stress.py`
  - `tests/test_ws_manager.py`

## Child DOX Index

No child DOX files.
