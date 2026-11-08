# Remote Control Plugin DOX

## Purpose

Own remote-control settings, provider installation and execution in a gVisor service sandbox.

## Ownership

- `helpers/runtime.py` owns the host adapter, status cache, bounded readiness wait, and start/stop calls.
- `api/tunnel.py` owns authenticated, CSRF-protected control. Legacy core endpoint paths delegate here.
- `sandbox/boot.sh`, `install.sh`, and `start.sh` own first-use installation and provider execution. `install_cloudflare.py` verifies the official release asset digest before installation.
- `sandbox/providers/` and `worker.py` retain Microsoft, Serveo and Tailscale behavior without framework imports or an HTTP server.
- `webui/` owns settings, operational controls and the existing Remote Control surface.

## Local Contracts

- Keep sandbox dependency constraints at least as strict as the shared root security floors; constraints must not install unused core dependencies.
- No sandbox, provider dependency installation, or resident controller before Start.
- Run Cloudflare as the native daemon. Other providers may use the plugin-local file-status worker; install flaredantic only inside their sandbox.
- Use the system image unless plugin image is explicitly set. Installer scripts run inside that sandbox. Keep its filesystem across stop/start; changing the base image requires deleting/recreating the service sandbox.
- Use a permanent standalone service sandbox. Restore desired-running services after an outer restart. Quick-tunnel URLs can change when the daemon restarts.
- Forward to the runtime HTTP port unless the plugin has an explicit override. Never bypass the normal HTTP/WebSocket authentication or CSRF checks.
- Bind only plugin source read-only; do not expose the entire usr/ or host root to the tunnel.
- Read bounded provider output using the manager's no-symlink file reader. Do not expose arbitrary logs or framework secrets through API responses.
- Disabling stops the sandbox. Uninstall deletes its plugin-owned sandbox, including provider credentials. Stop preserves it.

## Work Guidance

Keep provider dependencies out of root requirements and core imports. `hooks.install` intentionally defers guest setup until Start, per the on-demand lifecycle. Preserve origin discovery through `helpers.tunnel_origins` and legacy route compatibility.

## Verification

Run the focused sandbox, plugin, provider, CSRF and WebSocket tests. For runtime changes, exercise Cloudflare HTTPS/login/CSRF/WebSockets, parent exit, outer-container restart, cold install, warm restart, and stop through the real plugin API.

## Child DOX Index

No child DOX files.
