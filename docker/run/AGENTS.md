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
- Retain the Python 3.13-compatible ATK, LibreOffice/UNO, and Xpra pins in `fs/ins/install_additional.sh`. Resolve them from the signed Debian `forky` archive dated `20260624T000000Z` and Xpra `trixie`, using build-scoped APT options that preserve normal Kali sources. Refresh Xpra through `plugins/_desktop/helpers/refresh_xpra_index.sh` from the cloned repository; its signed compressed index avoids upstream's empty ARM64 `Packages` metadata without clearing the Debian indexes.
- Do not bake secrets, local `.env` values, or user data into the image.
- Runtime startup must ensure `/a0/usr/uploads` exists before supervised services start.
- Runtime startup seeds APT package lists in the background only when no package index is cached (fresh images clear these at build time). Normal restarts skip the refresh; installation scripts and plugin hooks refresh metadata when installing packages.
- Runtime startup raises the soft open-file limit toward `A0_NOFILE_LIMIT` (default `65535`) before supervisord starts, bounded by the container hard limit.
- Do not launch or configure SearXNG in the outer runtime container; the placeholder integration is owned by `plugins/_searxng/` and any future service must run through sandboxing.
- The compose example keeps the outer container unprivileged with `no-new-privileges`, uses an init reaper for detached sandboxes, and allows the nested gVisor systrap syscall surface through `seccomp:unconfined`.
- Self-update user-data backups skip Time Travel shadow history under `usr/.time_travel/` and transient Desktop agent state.
- Self-update backups use ZIP deflate level 1 and clamp archive timestamps to ZIP's supported range without changing source file dates.
- Self-update rollback stashes use immutable Git object IDs for creation checks and restoration; resolve the matching reflog selector only when dropping that stash, preserving unrelated entries. Failed restoration retains the stash.
- Self-update waits up to 600 seconds for each updated or restored WebUI health check by default; `A0_SELF_UPDATE_HEALTH_TIMEOUT_SECONDS` may override it. Backup and checkout time precede this health window.
- Successful or already-current self-updates refresh an installed Codex CLI with npm on a best-effort basis; missing CLIs and registry failures must not block Agent Zero startup.
- Application requirements are materialized into Depfix's shared installed store; launchers use `depfix run` so store fallback is active without moving those packages into global `site-packages`.
- The cache-busted final install reuses the first exact Depfix materialization and is the only pass that installs Chromium and runs preload.
- Playwright's pinned Python distribution comes only from `requirements.txt`; `install_playwright.sh` owns Chromium, its OS libraries, and `/a0/tmp/playwright` through the Depfix-managed module invocation.
- Keep Depfix's installed store. Depfix owns its ephemeral uv resolver cache, so runtime-image and self-update scripts must not purge pip or uv caches.

## Work Guidance

- Keep startup scripts explicit about using the global Python runtime.
- Coordinate tag, branch, and publishing changes with GitHub workflow automation.

## Verification

- Build `docker/run` when changing Dockerfile or install scripts.
- Smoke-test container startup after entrypoint, supervisor, port, or compose changes.

## Child DOX Index

No child DOX files.
