# Sandboxing Plugin DOX

## Purpose

- Own PRoot/UID/CoW sandbox lifecycle, execution, destination discovery, and management UI.

## Ownership

- `webui/thumbnail.jpg` owns the 256×256 plugin catalog artwork, kept below 20 KB.

- `helpers/images.py` owns daemonless Docker/OCI pull, local Docker archive import, unpacking, digest-pinned image cache metadata, image last-use tracking, and safe cache deletion.
- `helpers/builtin_image.py` owns OCI packaging and the lazy PRoot build of `agent-zero-sandbox:1` using `docker/sandbox/install.sh`.
- `helpers/manager.py` owns validation, launcher configuration, runtime state, bindings, sandbox/image references, expiry, and safe deletion.
- `helpers/runtime.py` owns resolved plugin configuration and the process-local manager.
- `helpers/shell.py` owns interactive PRoot terminal sessions.
- `tools/`, `api/`, `prompts/`, `extensions/`, and `webui/` expose the manager without duplicating lifecycle logic.

## Local Contracts

- The Sandboxes panel opens persistent non-service roots in Files via the managed read-only Sandbox provider. Browse and download without starting a guest or following guest symlinks, including when names are concurrently replaced. Bind mounts and transient runtime trees are outside this view. Pin connection IDs to the instance and sandbox creation time. Keep host-side edits away from hardlinked image files.

- Agent file transfers run the bounded standard Python file helper inside the selected guest. Exclude plugin service sandboxes and preserve guest mount permissions. Custom images need `python3` for this feature.

- Invoke PRoot via the stdlib process supervisor with argument arrays and shell=False. Guest shell text is never evaluated by the host.
- Never use a Docker socket, nested daemon, SSH server, KVM, or an unvalidated sandbox path.
- Pull images through `skopeo` and unpack them through `umoci` with argument arrays, bounded output, timeouts, and no shell. Registry credentials may only be referenced through a configured auth file.
- Local `docker save` archives enter the same cache through `helpers.sandbox import-image`; inspect and unpack a private archive copy, preserve validation/size limits, and never access a Docker socket. A cache-only reference must be reimported if evicted.
- Resolve the built-in default from the image cache, then `/opt/agent-zero/sandbox-image`. If missing or invalid, build it on first use in a private temporary PRoot sandbox from official Python/Node images. Serialize this through the image-cache lock, use a separate temporary source cache, run no host package installers, and publish only validated results. Do not eagerly build on startup or config reads; restoring an existing standalone sandbox may recover its base in the background.
- A rebuilt image must match an explicitly requested digest; never silently replace an existing sandbox's pinned base. Preserve custom default-image settings.
- Pin every sandbox to an immutable image digest. Tag refreshes affect new sandboxes only; image deletion and cleanup must refuse every digest referenced by sandbox metadata.
- Treat image cache entries as private runtime state. Automatic cleanup removes only unreferenced images whose last-use time exceeds the configured lifetime (30 days by default).
- Keep the shared mount explicit at `/shared`; optional binds must have validated absolute sources and sandbox destinations.
- New sandboxes hardlink root-owned immutable image files into private UID-owned directory trees. The tracked PRoot extension copies files before mutation. Access checks report writable shared files when copy-up can succeed, without copying on a probe; preserve read-only bindings, existing fake-root handling of private files, enforced parent permissions and read/execute checks. Cache/state must share a filesystem. Existing disk roots migrate in place; legacy overlay snapshots are preserved and refused with an export instruction. Temporary controls idle expiry only.
- Scope instance directories and process metadata by the persistent Agent Zero instance ID. Never operate on another instance’s metadata.
- Child is the default lifetime: a passed pipe closes on parent exit and terminates all guest UID processes. Standalone processes survive parent exit and restore on startup only when desired_running is true; manual stop clears that flag. Docker/host restarts require relaunch, not live process survival.
- Internet and host loopback are available with network=host (default); network=none is offline. No claim of separate outbound-only isolation.
- Share Agent Zero usr/ at /a0/usr by default, with share_usr=False to opt out. Mask manager state and image caches inside user-folder mounts. Host-root bindings are refused; explicit directories remain supported. Tunnel services opt out of shared user data.
- Service sandboxes are omitted from agent destinations and rejected by sandbox tools/interactive sessions.
- helpers.sandbox exposes the configured Python manager and CLI. Keep it as an adapter to this manager, not a second implementation.
- Lifecycle mutations must use per-sandbox and image-cache thread/process locks and atomic metadata/snapshot replacement.
- Lifecycle, list, inspect and liveness calls never scan files for storage reporting; sandbox `size_bytes` is null in those responses. `disk_usage(name)` returns a separate measurement on explicit request and holds no lifecycle locks. The authenticated API runs it in a worker thread, and the UI requests it only through Calculate, independently of polling/actions. Python async callers use `asyncio.to_thread`; the CLI provides `disk-usage NAME`.
- Image listings use the size recorded at import/pull; missing or broken size metadata is null, never an implicit scan. Keep import/pull size-limit validation.
- Disk accounting uses lstat metadata without following guest symlinks, whose absolute targets belong to the guest filesystem.

- `helpers/sandbox_worker.py` is the shared lazy worker adapter; `sandbox/` owns the guest file protocol and Python bootstrap. Service sandboxes receive a private disk directory at `/shared`; they never inherit the common agent exchange. Worker input mounts are read-only and under masked instance state. `set_mounts` requires a stopped guest; `process_command` exposes validated admin pipe execution.
- `sandbox/python.sh` defaults new environments to Python 3.12 for parser/model compatibility. Validated workers may set `WORKER_PYTHON` to their image interpreter; existing environments retain their interpreter and packages. Installer fingerprints automatically apply source updates without deleting worker state.
- `sandbox/progress.py` atomically publishes installer stages tagged with the current request boot ID. Worker installation fingerprints include read-only support files so native build recipe updates invalidate cached setup. Old boot progress is ignored; readiness still requires the matching `ready.json` handshake.

- `helpers/storage.py` owns immutable image preparation, private hardlink trees, symlink-safe binding ACLs and permanent UID leases. Preserve effective existing ACL permissions; atomic worker requests use mode 0640 so inherited read ACLs remain effective.
- `helpers/process.py` drops supplementary groups and real UID/GID, applies no-new-privileges and seccomp, then runs PRoot fake-root. Supervisors use PID start-time tokens, child pipes and UID cleanup; exec wrappers reap their own detached descendants on cancellation.
- `helpers/bootstrap.py` and `docker/base/fs/ins/proot/` own the pinned build and source-update installer. Runtime capability marker `A0-COW-2` includes overlay-aware access checks; older binaries rebuild through this installer on source update. Never install build dependencies during normal ready-image startup.
- PRoot is dependency/filesystem separation, not a hostile-code security boundary. Do not claim PID/kernel isolation. Offline mode denies new non-Unix sockets; bindings can still expose Unix services.

- Transient `/tmp`, `/run` and PRoot scratch data live below short, private `/run/a0-proot/<uid>` directories to keep Unix socket paths within Linux limits. They are cleared on stop; persistent guest files remain in the CoW root.

## Work Guidance

- Keep framework adapters thin and manager behavior independently testable without a real PRoot installation.
- Treat changes to capabilities, namespaces, mounts, networking, paths, or PRoot flags as security-contract changes.

## Verification

- Run `pytest tests/test_sandboxing.py tests/test_code_execution_destinations.py` after manager or destination changes.
- Run `pytest tests/test_sandbox_builtin_image.py` for bundle selection, lazy recovery, pinning, and recipe consistency. Verify a real missing-bundle build and offline Docker-bundle creation before claiming both paths work.
- Run the documented Linux lifecycle smoke test in an image with PRoot before claiming runtime compatibility.

## Child DOX Index

No child DOX files.
