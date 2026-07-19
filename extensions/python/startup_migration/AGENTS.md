# Startup Migration Extensions DOX

## Purpose

- Own backend startup migrations.

## Ownership

- Ordered Python files in this folder own idempotent migration steps that run during startup.

## Local Contracts

- Migrations must be safe to run repeatedly.
- Preserve user data and create backups or reversible paths when changing durable state.
- Keep long-running work bounded and observable.
- `_10_self_update_manager.py` may replace `/exe/self_update_manager.py` from the repository copy when the installed runtime updater is stale; it must validate required safety markers and keep a backup before replacement.
- After synchronizing a stale self-update manager, `_10_self_update_manager.py` starts that manager's best-effort Codex CLI refresh in the background so the update that introduces the hook does not need a second restart.

## Work Guidance

- Add migrations only for durable state changes that cannot be handled lazily elsewhere.

## Verification

- Smoke-test startup on a clean checkout and on representative existing user state when practical.

## Child DOX Index

No child DOX files.
