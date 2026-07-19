# tunnel_common.py DOX

## Purpose

- Own the `tunnel_common.py` helper module.
- This module contains shared tunnel provider helper classes and event parsing.
- Keep this file-level DOX profile synchronized with `tunnel_common.py` because this directory is intentionally flat.

## Ownership

- `tunnel_common.py` owns the runtime implementation.
- `tunnel_common.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `TunnelHelper` (no explicit base class)
  - `notify_starting(self, label)`
  - `notify_url_ready(self, label, url)`
  - `notify_stopped(self, label)`
- `FlaredanticTunnelHelper` (`TunnelHelper`)
  - `build_tunnel(self)`
  - `start(self)`
  - `stop(self)`
- Top-level functions:
- `event_value(event)`

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Observed side-effect areas: tunnel state.
- Imported dependency areas include: `flaredantic`.

## Key Concepts

- Important called helpers/classes observed in the source: `callable`, `self._notify`, `self.notify_starting`, `self.build_tunnel`, `self.tunnel.start`, `self.notify_stopped`, `self.notify_callback`, `self.notify_url_ready`, `self.tunnel.stop`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve public helper APIs used by core code and plugins unless every caller is updated.
- Keep path, auth, secret, persistence, network, and subprocess behavior explicit and bounded.
- Prefer adding cohesive helper functions here only when behavior is reused across modules.

## Verification

- Run targeted tests for changed helper behavior; run security regressions for auth, filesystem, WebSocket, tunnel, upload, or secret-handling helpers.
- Related tests observed by source search:
  - `tests/test_tunnel_remote_link.py`

## Child DOX Index

No child DOX files.
