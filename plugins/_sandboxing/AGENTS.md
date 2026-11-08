# Sandboxing Plugin DOX

## Purpose

- Own direct gVisor/runsc sandbox lifecycle, execution, destination discovery, and management UI.

## Ownership

- `helpers/images.py` owns daemonless Docker/OCI pull, local Docker archive import, unpacking, digest-pinned image cache metadata, image last-use tracking, and safe cache deletion.
- `helpers/builtin_image.py` owns OCI packaging and the lazy gVisor build of `agent-zero-sandbox:1` using `docker/sandbox/install.sh`.
- `helpers/manager.py` owns validation, OCI bundles, runtime state, snapshots, mounts, sandbox/image references, expiry, and safe deletion.
- `helpers/runtime.py` owns resolved plugin configuration and the process-local manager.
- `helpers/shell.py` owns interactive `runsc exec` terminal sessions.
- `tools/`, `api/`, `prompts/`, `extensions/`, and `webui/` expose the manager without duplicating lifecycle logic.

## Local Contracts

- Invoke `runsc` directly with argument arrays and `shell=False`; agent-generated shell text is only passed inside the sandbox.
- Use rootless systrap with directfs for host-backed filesystem operations. Keep guest mounts, instance masks, capability bounds and read-only inputs intact; enabling directfs must not add outer-container capabilities or privileges. Verify non-root lifecycle and mount isolation with the supported runsc release.
- Never use a Docker socket, nested daemon, SSH server, KVM, or an unvalidated sandbox path.
- Pull images through `skopeo` and unpack them through `umoci` with argument arrays, bounded output, timeouts, and no shell. Registry credentials may only be referenced through a configured auth file.
- Local `docker save` archives enter the same cache through `helpers.sandbox import-image`; inspect and unpack a private archive copy, preserve validation/size limits, and never access a Docker socket. A cache-only reference must be reimported if evicted.
- Resolve the built-in default from the image cache, then `/opt/agent-zero/sandbox-image`. If missing or invalid, build it on first use in a private temporary gVisor sandbox from official Python/Node images. Serialize this through the image-cache lock, use a separate temporary source cache, run no host package installers, and publish only validated results. Do not eagerly build on startup or config reads; restoring an existing standalone sandbox may recover its base in the background.
- A rebuilt image must match an explicitly requested digest; never silently replace an existing sandbox's pinned base. Preserve custom default-image settings.
- Pin every sandbox to an immutable image digest. Tag refreshes affect new sandboxes only; image deletion and cleanup must refuse every digest referenced by sandbox metadata.
- Treat image cache entries as private runtime state. Automatic cleanup removes only unreferenced images whose last-use time exceeds the configured lifetime (30 days by default).
- Keep the shared mount explicit at `/shared`; optional binds must have validated absolute sources and sandbox destinations.
- New sandboxes use a private writable disk root copied with reflinks when available; starts do not rebuild or extract snapshots. Temporary controls idle expiry only; permanent never expires. Legacy overlay/snapshot records remain readable.
- Scope instance directories, runsc roots/IDs, and OCI annotations by the persistent Agent Zero instance ID. Never operate on another instance’s metadata.
- Child is the default lifetime: a passed pipe closes on parent exit and terminates guest PID 1. Standalone processes survive parent exit and restore on startup only when desired_running is true; manual stop clears that flag. Docker/host restarts require relaunch, not live process survival.
- Internet and host loopback are available with network=host (default); network=none is offline. No claim of separate outbound-only isolation.
- Share Agent Zero usr/ at /a0/usr by default, with share_usr=False to opt out. Mask manager state and image caches inside user-folder mounts. Mounting host / at /host requires host_root=True. Tunnel services opt out of shared user data.
- Service sandboxes are omitted from agent destinations and rejected by sandbox tools/interactive sessions.
- helpers.sandbox exposes the configured Python manager and CLI. Keep it as an adapter to this manager, not a second implementation.
- Lifecycle mutations must use per-sandbox and image-cache thread/process locks and atomic metadata/snapshot replacement.
- Lifecycle, list, inspect and liveness calls never scan files for storage reporting; sandbox `size_bytes` is null in those responses. `disk_usage(name)` returns a separate measurement on explicit request and holds no lifecycle locks. The authenticated API runs it in a worker thread, and the UI requests it only through Calculate, independently of polling/actions. Python async callers use `asyncio.to_thread`; the CLI provides `disk-usage NAME`.
- Image listings use the size recorded at import/pull; missing or broken size metadata is null, never an implicit scan. Keep import/pull size-limit validation.
- Disk accounting uses lstat metadata without following guest symlinks, whose absolute targets belong to the guest filesystem.

- `helpers/sandbox_worker.py` is the shared lazy worker adapter; `sandbox/` owns the guest file protocol and Python bootstrap. Service sandboxes receive a private tmpfs at `/shared`; they never inherit the common agent exchange. Worker input mounts are read-only and under masked instance state. `set_mounts` requires a stopped guest; `process_command` exposes validated admin pipe execution.
- `sandbox/progress.py` atomically publishes installer stages tagged with the current request boot ID. Worker installation fingerprints include read-only support files so native build recipe updates invalidate cached setup. Old boot progress is ignored; readiness still requires the matching `ready.json` handshake.

## Work Guidance

- Keep framework adapters thin and manager behavior independently testable without a real gVisor installation.
- Treat changes to capabilities, namespaces, mounts, networking, paths, or `runsc` flags as security-contract changes.

## Verification

- Run `pytest tests/test_sandboxing.py tests/test_code_execution_destinations.py` after manager or destination changes.
- Run `pytest tests/test_sandbox_builtin_image.py` for bundle selection, lazy recovery, pinning, and recipe consistency. Verify a real missing-bundle build and offline Docker-bundle creation before claiming both paths work.
- Run the documented Linux lifecycle smoke test in an image with gVisor before claiming runtime compatibility.

## Child DOX Index

No child DOX files.
