# Docker Runtime Image DOX

## Purpose

- Own the runnable Agent Zero image context and local compose example.
- Install Agent Zero from a selected branch onto the base image and prepare runtime entrypoints.

## Ownership

- `Dockerfile` owns branch-based image assembly, exposed ports, and container startup command.
- `docker-compose.yml` owns the local compose service example.
- `build.txt` owns maintainer build and push command notes.
- `fs/exe/` owns runtime entrypoint, supervisor, self-update, Node eval, and service scripts.
- `fs/ins/` owns application dependencies, native runtime packages, embedding assets, and the legacy Playwright compatibility entry point.
- `update/` owns release-supplied before/after self-update scripts and their authoring contract.
- Files under `fs/` are copied to container root during the runtime build.

## Local Contracts

- `BRANCH` is required for branch-based Docker builds. `BASE_IMAGE` defaults to `agent-zero-base:local`, matching `DockerfileLocal`.
- Clone the selected branch once in a disposable source stage with `--filter=blob:none --single-branch`, preserving full ancestry for self-update. Install directly into `/a0`; never retain a seed checkout or copy application files on startup.
- Cache the dependency layer using only root requirements and the desktop native package manifest; copy the final source and prepare embedding assets afterward. Local builds exclude both `.git` files and directories.
- Persist `/a0/usr` in normal installs. An empty full `/a0` mount must fail with migration guidance; populated development mounts remain supported. Source updates survive restarts, while container replacement uses the new image code.
- Preserve exposed ports for SSH, HTTP, and tunneled services unless docs and workflows are updated together.
- Run framework services and local agent/user Python execution in the official image's global Python environment; do not create or activate a virtual environment.
- Run Supervisor's event listener with Debian's `/usr/bin/python3`, matching the apt-owned Supervisor package; application services still use the official global Python.
- Assemble embedded Tuxee with `plugins/_desktop/build/` in a disposable Debian 12 stage: checksum-verified official binary plus minimal VNC/window manager and stripped audio bundle. Create its standard absolute command symlink in the final image. Install that recipe's native runtime libraries in the outer image; no LibreOffice/UNO, Xfce, Xpra or Collabora belongs there. Browser mounts the shared `/usr/local/lib/tuxee-gui` and `/usr/local/lib/tuxee-audio` runtimes read-only in its Debian 12 sandbox and uses noVNC plus an authenticated PCM audio stream.
- Do not bake secrets, local `.env` values, or user data into the image.
- The consolidated root requirements include SoundFile for WAV test fixtures; supported wheels bundle its audio library. Speech runtimes remain in their guests; do not add outer APT audio packages for test tooling.
- Runtime startup must ensure `/a0/usr/uploads` exists before supervised services start.
- On the first container start, launch a silent background APT index update without waiting. `/var/lib/apt/a0-initial-update-started` prevents repeats on restart, including after a failed update; a replacement container starts fresh. Installation scripts and plugin hooks still refresh metadata when installing packages.
- Runtime startup raises the soft open-file limit toward `A0_NOFILE_LIMIT` (default `65535`) before supervisord starts, bounded by the container hard limit.
- Do not launch a separate tunnel API service. The Remote Control plugin starts its provider inside a standalone sandbox on demand; startup migration removes legacy Supervisor entries on source updates.
- Do not launch or configure SearXNG in the outer runtime container; the on-demand sandbox CLI is owned by `plugins/_searxng/`.
- The compose example uses Docker default seccomp, no-new-privileges and an init reaper. PRoot needs no added capabilities, mount devices or nested user namespaces; the A0 manager runs as container root and drops each guest to its leased UID.
- Self-update user-data backups skip Time Travel shadow history under `usr/.time_travel/` and transient Desktop agent state.
- Self-update backups use ZIP deflate level 1 and clamp archive timestamps to ZIP's supported range without changing source file dates.
- Self-update rollback stashes use immutable Git object IDs for creation checks and restoration; resolve the matching reflog selector only when dropping that stash, preserving unrelated entries. Failed restoration retains the stash.
- Self-update waits up to 600 seconds for each updated or restored WebUI health check by default; `A0_SELF_UPDATE_HEALTH_TIMEOUT_SECONDS` may override it. Backup and checkout time precede this health window.
- Successful or already-current self-updates refresh an installed Codex CLI with npm on a best-effort basis; missing CLIs and registry failures must not block Agent Zero startup.
- Self-update hooks come from the resolved target commit. Run `update/before/` after backup and target validation, before checkout; run `update/after/` after checkout validation, before UI startup and its health timer. Failures abort/restore the checkout; arbitrary system changes are not automatically reversible.
- Critical updater replacement is explicitly staged by a before hook, validated before atomic replacement, and backed up next to the runtime updater. Hand off the prepared attempt to the replacement without repeating backup/before hooks; restore the previous updater on handled update failures. Ordinary updates do not replace the updater just because source bytes differ.
- Install application requirements with `uv pip install --no-cache --python /usr/local/bin/python` in the single dependency installation pass; launch services directly with `/usr/local/bin/python`. Later overlay cache deletion cannot reclaim base layers.
- Keep `PYTHONDONTWRITEBYTECODE=1` for services and their subprocesses: import-time bytecode events can expose a lock inversion between watchdog registration and event dispatch during startup.
- The final asset preparation uses installed packages, prepares checksum-pinned default ONNX/tokenizer assets with a failing-on-error inference check, then runs embedding preload. Do not ship unused Torch weights or an outer training stack. Chromium, document parsing and speech assets install only in their plugin sandboxes on first use.
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

| Child | Scope |
| --- | --- |
| [update/AGENTS.md](update/AGENTS.md) | Release update hooks, execution context and critical updater handoff. |
