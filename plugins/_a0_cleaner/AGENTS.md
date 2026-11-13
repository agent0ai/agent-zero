# A0Cleaner DOX

## Purpose

- Own default storage housekeeping, user-selected cleanup and the A0Cleaner UI.

## Ownership

- `helpers/cleaner.py` owns the bounded inventory, review manifest, guarded deletion and persistent reports.
- `helpers/runtime.py` owns runtime paths, process/chat activity, settings, the scheduler task and notifications.
- `hooks.py` supplies `run_scheduled_task` and validates saved settings. The job-loop extension registers the task; it does not run cleanup itself.
- `api/cleaner.py` owns authenticated scan, review, cleanup, settings and schedule actions.
- `webui/` owns the modal, state, styling, settings entry and 256×256 thumbnail under 20 KB.

## Local Contracts

- Automatic cleanup defaults on for aged Python/Node download caches, installer leftovers, retired browser profiles, old inactive-chat screenshots, temporary captures and unused Chromium installations. Preserve explicit per-area and master opt-outs. Embedding cache and custom folders require manual selection; never add them to automatic cleanup.
- Keep source, settings, models, installed apps, uploads and chat text outside built-in cleanup areas. Time Travel owns its own retention; never prune its repositories here.
- Skip required/running browser versions, shared/active/recent profiles, recent/running/paused chats, active process paths, symbolic links, hard links and mounts. Unknown process ownership fails closed for the affected UID; unavailable root/current-UID inspection aborts cleanup.
- Scans are read-only, limited to 250,000 entries and 90 seconds. Inspection errors disable the affected area. Age uses both mtime and ctime, so an old timestamp on a newly copied file cannot qualify it.
- Cleanup requires the current, unexpired scan ID and unchanged settings. Manual cleanup requires explicit confirmation. Validate roots again, walk all parent directories with O_NOFOLLOW, compare file identity/size/timestamps and unlink through directory descriptors. Changed files are skipped and never counted as removed. Consume the manifest after every deletion pass.
- Use a cross-process operation lock. Poll cancellation and plugin activation during work. Persist partial completion before reporting interruption; keep the last 40 cleanup records and the latest scheduled result separately from fresh scans.
- The normal scheduler owns cadence/state/results through the `plugin_name` hook contract. Default Monday 09:00 in the configured timezone. Register once, preserve edited/disabled schedules and respect task deletion. Never create a model chat for housekeeping.
- Custom rules accept only proper subfolders of A0 workdir/projects/downloads/uploads/tmp, with no symlink ancestors, overlapping rules, protected metadata or overlapping managed roots.
- Report allocated file-byte estimates, not guaranteed host block recovery from immutable container image layers. No chat contents or process command lines belong in reports or notifications.
- Use native A0 notifications and an action opening the cleaner; toast clicks must never authorize deletion directly.

## Work Guidance

- Add a cleanup area only after tracing its producer, readers and lifecycle on the framework runtime.
- Keep policy in the catalog, not in browser-provided filesystem paths. Do not add arbitrary shell cleanup commands.
- Preserve the supplied Agent Zero logo geometry in thumbnail revisions; keep generation provenance in `webui/thumbnail.prompt.txt`.

## Verification

- Run `tests/test_a0_cleaner.py`, scheduler plugin-task tests and the cleaner store tests.
- Exercise live scan, opt-outs, preview/cancel/clean, custom rules, scheduled execution and notifications with controlled files before running default cleanup.
- Check desktop/mobile layouts and settings/schedule persistence on the live Docker target.

## Child DOX Index

No child DOX files.
