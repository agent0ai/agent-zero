# tailscale_tunnel.py DOX

## Purpose

- Own the `tailscale_tunnel.py` helper module.
- This module implements Tailscale tunnel install and provider lifecycle behavior.
- Keep this file-level DOX profile synchronized with `tailscale_tunnel.py` because this directory is intentionally flat.

## Ownership

- `tailscale_tunnel.py` owns the runtime implementation.
- `tailscale_tunnel.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `TailscaleTunnel` (`CliTunnelHelper`)
  - `stop(self)`
- Top-level functions:
- `tailscale_arch()`
- `tailscale_archive_url()`
- `install_tailscale(notify=...)`
- `resolve_tailscaled_binary(binary_path)`
- `notify_info(notify, message, data=...)`
- `tailscale_socket_args(socket_path=...)`
- `tailscale_command(binary_path, args, socket_path=...)`
- `tailscale_status(binary_path, socket_path=...)`
- `tailscale_funnel_help(binary_path, socket_path=...)`
- `compact_output(lines)`
- `tailscale_daemon_hint(output)`
- `tailscale_daemon_ready(binary_path, socket_path)`
- `read_recent_tailscaled_log()`
- `start_tailscaled(binary_path, notify=...)`
- `stop_managed_tailscaled()`
- `tailscale_up_failure_message(output, timed_out=...)`
- `run_tailscale_up(binary_path, notify=..., timeout=..., socket_path=...)`
- `ensure_tailscale_funnel_command(binary_path, socket_path=...)`
- `ensure_tailscale_ready(binary_path, notify=...)`
- Notable constants/configuration names: `TAILSCALE_URL_RE`, `TAILSCALE_LOGIN_URL_RE`, `TAILSCALE_STABLE_PACKAGES_URL`, `TAILSCALE_UP_TIMEOUT`, `TAILSCALE_FUNNEL_TIMEOUT`, `TAILSCALE_FUNNEL_HTTPS_PORT`, `TAILSCALE_DAEMON_START_TIMEOUT`, `TAILSCALE_RUNTIME_DIR`, `TAILSCALE_STATE_DIR`, `TAILSCALE_SOCKET_PATH`, `TAILSCALE_DAEMON_LOG_PATH`, `TAILSCALE_DAEMON_PID_PATH`.

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Observed side-effect areas: filesystem reads, filesystem writes, filesystem deletion, network calls, subprocess/runtime control, WebSocket state, settings/state persistence, tunnel state.
- Imported dependency areas include: `collections`, `flaredantic`, `helpers`, `helpers.cli_tunnel`, `json`, `os`, `pathlib`, `queue`, `re`, `shutil`, `subprocess`, `threading`, `time`, `urllib.parse`, `urllib.request`.

## Key Concepts

- Important called helpers/classes observed in the source: `re.compile`, `Path`, `files.get_abs_path`, `cli_tunnel.platform_parts`, `tailscale_arch`, `pattern.search`, `urllib.parse.urljoin`, `shutil.which`, `tailscale_archive_url`, `cli_tunnel.download_file`, `Path.with_name`, `sibling.exists`, `callable`, `subprocess.run`, `join`, `output.lower`, `tailscale_status`, `compact_output`, `resolve_tailscaled_binary`, `tailscale_daemon_ready`.
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
