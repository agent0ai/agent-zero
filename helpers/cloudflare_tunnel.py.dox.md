# cloudflare_tunnel.py DOX

## Purpose

- Own the `cloudflare_tunnel.py` helper module.
- This module implements Cloudflare tunnel provider lifecycle behavior.
- Keep this file-level DOX profile synchronized with `cloudflare_tunnel.py` because this directory is intentionally flat.

## Ownership

- `cloudflare_tunnel.py` owns the runtime implementation.
- `cloudflare_tunnel.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `CloudflareTunnel` (`FlaredanticTunnelHelper`)
  - `build_tunnel(self)`

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Observed side-effect areas: settings/state persistence, tunnel state.
- Imported dependency areas include: `flaredantic`, `helpers.tunnel_common`.

## Key Concepts

- Important called helpers/classes observed in the source: `FlareConfig`, `FlareTunnel`.
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
