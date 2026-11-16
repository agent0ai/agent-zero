# Release Update Hooks DOX

## Purpose

- Own system checks and migrations required when updating an installed release.

## Ownership

- `before/` and `after/` contain optional standalone Python/Bash scripts, ordered by filename.
- `README.md` documents the environment, failure behavior and critical updater replacement.
- `../fs/exe/self_update_manager.py` owns discovery, execution, backup/rollback and handoff.

## Local Contracts

- Only direct regular `.py` and `.sh` files from the fetched target commit execute. Never run local, user or plugin-discovered update scripts here.
- Before hooks run with the old checkout; after hooks run with the validated new checkout, before UI startup. Both run as the updater user, normally root, using the installed runtime.
- Scripts must be idempotent and check installed state, including skipped-version upgrades and downgrades. Missing hook directories are valid. Already-installed explicit-tag requests skip hooks.
- Keep scripts standalone: target application dependencies may not yet be installed. Scripts are staged outside the checkout; use `A0_UPDATE_REPO_DIR` for live files and `git show` with `A0_UPDATE_TARGET_COMMIT` for target files.
- Failure or the 1800-second per-script timeout stops the attempt. Output goes to the update log; timeout kills the hook process group. Do not detach background work or print secrets.
- Preserve working assets until checks/builds succeed and publish completion markers last, as in the Tuxee installer. Git rollback cannot undo package, sandbox or user-data changes; script authors own those recovery paths.
- Updater replacement is exceptional. Only a before hook may stage `A0_UPDATE_UPDATER_CANDIDATE`. Preserve `execute_pending_update(request_data, *, logger, prepared=None)` and its prepared-state contract when changing the updater; the new implementation resumes the same attempt after before hooks.

## Work Guidance

- Add scripts only when a release needs system changes; reuse owning installers and state checks. Keep lazy plugin installation in its owning plugin.
- Keep hooks needed for supported direct upgrades in subsequent releases; the updater runs the target release's scripts, not intermediate releases.
- Do not write the running updater directly. Follow the staging protocol in `README.md`.

## Verification

- Run `pytest tests/test_self_update_hooks.py tests/test_self_update_runtime_sync.py tests/test_self_update_tag_filter.py`.
- Test migrations against both current and outdated disposable runtime state, including failure/retry and retained user data.

## Child DOX Index

No child DOX files.
