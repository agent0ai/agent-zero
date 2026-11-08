# Docker Runtime Image DOX

## Purpose

- Own the runnable Agent Zero image context and local compose example.
- Install Agent Zero from a selected branch onto the base image and prepare runtime entrypoints.

## Ownership

- `Dockerfile` owns branch-based image assembly, exposed ports, and container startup command.
- `docker-compose.yml` owns the local compose service example.
- `build.txt` owns maintainer build and push command notes.
- `fs/exe/` owns runtime entrypoint, supervisor, self-update, Node eval, and service scripts.
- `fs/ins/` owns preinstall, installation, Playwright, SSH, and postinstall scripts.
- Files under `fs/` are copied to container root during the runtime build.

## Local Contracts

- `BRANCH` is required for branch-based Docker builds.
- Preserve exposed ports for SSH, HTTP, and tunneled services unless docs and workflows are updated together.
- Run framework services and local agent/user Python execution in the official image's global Python environment; do not create or activate a virtual environment.
- Run Supervisor's event listener with Debian's `/usr/bin/python3`, matching the apt-owned Supervisor package; application services still use the official global Python.
- Build embedded Tuxee with `plugins/_desktop/build/` in a disposable stage, copying only its runtime and minimal VNC/window manager. Install that recipe's native runtime libraries in the outer image; no LibreOffice/UNO, Xfce, Xpra or Collabora belongs there. Browser mounts the shared `/usr/local/lib/tuxee-gui` bundle read-only in its sandbox and uses noVNC.
- Do not bake secrets, local `.env` values, or user data into the image.
- The consolidated root requirements include SoundFile for WAV test fixtures; supported wheels bundle its audio library. Speech runtimes remain in their guests; do not add outer APT audio packages for test tooling.
- Runtime startup must ensure `/a0/usr/uploads` exists before supervised services start.
- Runtime startup seeds APT package lists in the background only when no package index is cached (fresh images clear these at build time). Normal restarts skip the refresh; installation scripts and plugin hooks refresh metadata when installing packages.
- Runtime startup raises the soft open-file limit toward `A0_NOFILE_LIMIT` (default `65535`) before supervisord starts, bounded by the container hard limit.
- Do not launch a separate tunnel API service. The Remote Control plugin starts its provider inside a standalone sandbox on demand; startup migration removes legacy Supervisor entries on source updates.
- Do not launch or configure SearXNG in the outer runtime container; the placeholder integration is owned by `plugins/_searxng/` and any future service must run through sandboxing.
- The compose example keeps the outer container unprivileged with `no-new-privileges`, uses an init reaper for detached sandboxes, and allows the nested gVisor systrap syscall surface through `seccomp:unconfined`.
- Self-update user-data backups skip Time Travel shadow history under `usr/.time_travel/` and transient Desktop agent state.
- Self-update backups use ZIP deflate level 1 and clamp archive timestamps to ZIP's supported range without changing source file dates.
- Self-update rollback stashes use immutable Git object IDs for creation checks and restoration; resolve the matching reflog selector only when dropping that stash, preserving unrelated entries. Failed restoration retains the stash.
- Self-update waits up to 600 seconds for each updated or restored WebUI health check by default; `A0_SELF_UPDATE_HEALTH_TIMEOUT_SECONDS` may override it. Backup and checkout time precede this health window.
- Successful or already-current self-updates refresh an installed Codex CLI with npm on a best-effort basis; missing CLIs and registry failures must not block Agent Zero startup.
- Install application requirements with `uv pip install --no-cache --python /usr/local/bin/python` in both installation passes; launch services directly with `/usr/local/bin/python`. Later overlay cache deletion cannot reclaim base layers.
- Keep `PYTHONDONTWRITEBYTECODE=1` for services and their subprocesses: import-time bytecode events can expose a lock inversion between watchdog registration and event dispatch during startup.
- The cache-busted final install reuses installed packages, prepares checksum-pinned default ONNX/tokenizer assets with a failing-on-error inference check, then runs embedding preload. Do not ship unused Torch weights or an outer training stack. Chromium, document parsing and speech assets install only in their plugin sandboxes on first use.
- Patchright Python, its driver, Chromium and display runtime belong entirely to the Browser sandbox. Telegram aiogram, IMAP/Exchange packages and WhatsApp npm dependencies likewise install in their guests on demand. `install_playwright.sh` is a no-op compatibility entry point.
- Images built with the retired shared dependency store require rebuilt base and runtime images; source-only self-update cannot supply missing global packages or replace image-owned launchers.
- Both this Dockerfile and `DockerfileLocal` build the shared `docker/sandbox/install.sh` recipe and package its rootfs as an OCI layout at `/opt/agent-zero/sandbox-image`. Keep it outside `/a0` and `usr/` so mounts and source updates cannot hide it. Packaging uses a read-only build-stage mount, avoiding a second full rootfs layer. Do not add eager sandbox image setup to WebUI startup.
- The bundled OCI layout is public image content: make its metadata and blobs readable by normal Linux users so rootless callers can reuse it without rebuilding.

## Work Guidance

- Keep startup scripts explicit about using the global Python runtime.
- Coordinate tag, branch, and publishing changes with GitHub workflow automation.

## Verification

- Build `docker/run` when changing Dockerfile or install scripts.
- Smoke-test container startup after entrypoint, supervisor, port, or compose changes.

## Child DOX Index

No child DOX files.
