# microsoft_tunnel.py DOX

## Purpose

- Own the `microsoft_tunnel.py` helper module.
- This module implements Microsoft Dev Tunnel provider behavior.
- Keep this file-level DOX profile synchronized with `microsoft_tunnel.py` because this directory is intentionally flat.

## Ownership

- `microsoft_tunnel.py` owns the runtime implementation.
- `microsoft_tunnel.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `AgentZeroMicrosoftTunnel` (`MicrosoftTunnel`)
  - `notify(self, event, message, data=...)`
  - `agent_zero_notifications(self)`
- `MicrosoftDevTunnel` (`FlaredanticTunnelHelper`)
  - `build_tunnel(self)`
  - `start(self)`
- Top-level functions:
- `default_microsoft_tunnel_id()`
- Notable constants/configuration names: `MICROSOFT_TUNNEL_ID_ENV_KEYS`, `MICROSOFT_TUNNEL_TIMEOUT`.

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Observed side-effect areas: filesystem reads, network calls, settings/state persistence, tunnel state.
- Imported dependency areas include: `flaredantic`, `getpass`, `hashlib`, `helpers`, `helpers.tunnel_common`, `os`, `socket`.

## Key Concepts

- Important called helpers/classes observed in the source: `join`, `strip`, `hashlib.sha256.hexdigest`, `self.notify`, `callable`, `self._notify_progress`, `self._run_cmd`, `MicrosoftConfig`, `AgentZeroMicrosoftTunnel`, `getpass.getuser`, `socket.gethostname`, `files.get_abs_path`, `super.notify`, `parent`, `super.start`, `hashlib.sha256`, `MicrosoftTunnelError`, `default_microsoft_tunnel_id`, `RuntimeError`, `seed.encode`.
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
