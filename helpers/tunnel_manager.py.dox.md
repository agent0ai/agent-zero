# tunnel_manager.py DOX

## Purpose

- Own the `tunnel_manager.py` helper module.
- This module selects and coordinates configured tunnel providers.
- Keep this file-level DOX profile synchronized with `tunnel_manager.py` because this directory is intentionally flat.

## Ownership

- `tunnel_manager.py` owns the runtime implementation.
- `tunnel_manager.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `TunnelManager` (no explicit base class)
  - `get_instance(cls)`
  - `get_notifications(self)`
  - `get_last_error(self)`
  - `start_tunnel(self, port=..., provider=...)`
  - `stop_tunnel(self)`
  - `get_tunnel_url(self)`
- Top-level functions:
- `normalize_provider(provider)`
- Notable constants/configuration names: `SUPPORTED_TUNNEL_PROVIDERS`, `TUNNEL_PROVIDER_ALIASES`.

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Observed side-effect areas: tunnel state.
- Imported dependency areas include: `collections`, `flaredantic`, `helpers.cloudflare_tunnel`, `helpers.microsoft_tunnel`, `helpers.print_style`, `helpers.serveo_tunnel`, `helpers.tailscale_tunnel`, `helpers.tunnel_common`, `threading`, `time`.

## Key Concepts

- Important called helpers/classes observed in the source: `strip.lower`, `threading.Lock`, `join`, `ValueError`, `deque`, `self.notifications.clear`, `ServeoTunnelHelper`, `self._ensure_subscribed`, `strip`, `notifier.subscribe`, `CloudflareTunnel`, `MicrosoftDevTunnel`, `TailscaleTunnel`, `normalize_provider`, `threading.Thread`, `tunnel_thread.start`, `cls`, `event_value`, `PrintStyle.error`, `self._append_notification`.
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
