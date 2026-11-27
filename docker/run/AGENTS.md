# Docker Runtime DOX

## Purpose

- Own container startup, runtime files, Compose and self-update hooks.

## Ownership

- `docker-compose.yml` is the local Compose example. `fs/` is copied to the container root.
- `fs/opt/agent-zero/init/` owns the Agent Zero, SSH and cron services started by Tuxee. `fs/exe/` owns the entrypoint, self-update bootstrap and Node evaluator.
- `update/` owns release-supplied self-update hooks.

## Local Contracts

- Tuxee's Tini and init hooks own container shutdown. A0 supplies an image-owned hook directory so a reused anonymous `/init` volume cannot mask updated launchers. Agent Zero relaunches through `/exe/run_A0.sh` after a crash or a clean exit, with a one-second delay. Shutdown terminates the active process group and waits without starting another attempt.
- Tuxee listens on HTTP loopback at `127.0.0.1:17883`. Keep it behind Agent Zero's authenticated Desktop gateway and share the initialized root password through the root-only startup handoff. The Compose example publishes only Agent Zero HTTP.
- Persist `/a0/usr`. An empty full `/a0` mount fails with migration guidance. A populated development mount remains supported. Source updates survive restarts, while container replacement uses the new image code.
- Startup creates uploads before the framework starts, raises the open-file soft limit toward `A0_NOFILE_LIMIT` (default `65535`) within the hard limit, and starts a single background APT index refresh per container.
- Compose uses default seccomp and no-new-privileges. PRoot needs no added capabilities, mount devices or nested user namespaces.
- Remote Control, SearXNG and Browser dependencies install in plugin sandboxes on demand. Startup migrations may clean up old services on existing images.
- Self-update user-data backups skip Time Travel shadow history under `usr/.time_travel/` and transient Desktop agent state.
- Self-update backups use ZIP deflate level 1 and clamp archive timestamps to ZIP's supported range without changing source file dates.
- Self-update rollback stashes use immutable Git object IDs for creation checks and restoration; resolve the matching reflog selector only when dropping that stash, preserving unrelated entries. Failed restoration retains the stash.
- Self-update waits up to 600 seconds for each updated or restored WebUI health check by default; `A0_SELF_UPDATE_HEALTH_TIMEOUT_SECONDS` may override it. Backup and checkout time precede this health window.
- Successful or already-current self-updates refresh an installed Codex CLI with npm on a best-effort basis; missing CLIs and registry failures must not block Agent Zero startup.
- Self-update hooks come from the resolved target commit. Run `update/before/` after backup and target validation, before checkout; run `update/after/` after checkout validation, before UI startup and its health timer. Failures abort/restore the checkout; arbitrary system changes are not automatically reversible.
- Critical updater replacement is explicitly staged by a before hook, validated before atomic replacement, and backed up next to the runtime updater. Hand off the prepared attempt to the replacement without repeating backup/before hooks; restore the previous updater on handled update failures. Ordinary updates do not replace the updater just because source bytes differ.

## Work Guidance

- Keep application and self-update entrypoints on `/usr/local/bin/python`.

## Verification

- Build from the root and check HTTP readiness, crash recovery, clean restart, shutdown and loopback-only Tuxee.

## Child DOX Index

| Child | Scope |
| --- | --- |
| [update/AGENTS.md](update/AGENTS.md) | Release update hooks, execution context and critical updater handoff. |
