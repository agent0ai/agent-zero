# A0Cleaner

Open **A0Cleaner** from the sidebar menu. Opening it scans automatically when the previous scan is older than an hour. Choose areas, review the file list, and select **Clean up**.

A real **A0Cleaner** task appears in Agent Zero's Scheduled Tasks. It runs weekly, Monday at 09:00 in the configured timezone, with no model call. Change its cadence in the cleaner or edit its cron schedule through **Schedule details**. Deleting or disabling the task is respected. Each run saves its results in the cleaner and sends an A0 notification with a **Clean up** button for remaining files.

## Defaults

| Area | Default action | Retention |
| --- | --- | --- |
| Python and Node download caches | Automatic | 30 days |
| Plugin/skill installer staging | Automatic | 7 days |
| Retired browser profiles | Automatic | 30 days, inactive profiles only |
| Old chat screenshots | Automatic | 30 days, inactive chats only |
| Temporary browser/desktop captures | Automatic | 30 days |
| Unused Chromium installations | Automatic | 30 days, required and running versions excluded |
| Embedding cache | Manual selection | 30 days |
| Custom folders | Manual selection | Per-folder age |

The master switch and each area's **Auto** switch persist explicit choices. Automatic cleanup never includes custom folders or the embedding cache. Clearing retired profiles removes their saved sign-ins; clearing chat screenshots removes those previews while retaining chat text and uploaded images. Embedding cleanup may cause remote model usage when the cache is rebuilt.

A custom age of 0 includes all eligible files and still requires manual confirmation. Custom folders must be subfolders of A0's workdir, projects, downloads, uploads or tmp. Project roots, configuration, Git repositories, managed browser directories and Time Travel storage are protected. Time Travel keeps its own retention lifecycle; A0Cleaner does not delete its repositories. Installed models and applications, uploads, chat transcripts and arbitrary temporary folders are not treated as disposable caches.

## Cleanup contract

Scans inspect metadata and do not delete files. Cleanup uses the reviewed scan ID, verifies each file's identity, size and timestamps, and skips changed files. Symbolic links, hard links and nested mounts are excluded. Deletions walk parent directories with `O_NOFOLLOW` and use directory file descriptors. Active process paths, running package managers, shared browser profiles, the required Chromium revision, and active/recent chats are protected. Files owned by another UID whose open files cannot be inspected are skipped.

Scans are capped at 250,000 entries and 90 seconds. Failed inspection leaves the affected area untouched. Per-instance locks serialize scans and cleanup; scheduled cancellation and plugin disablement stop further deletion. A scan expires after 24 hours and cannot be replayed after cleanup. Reports, the latest scheduled result and the last 40 cleanup records live under `usr/plugin_data/_a0_cleaner/`.

Sizes are allocated file-byte estimates. The disk meter reports the filesystem visible to the container; deleting files inherited from an immutable image layer may not free host disk space until that image is replaced.

## Implementation and verification

The scheduler owns timing, state and result persistence. A0Cleaner's `run_scheduled_task` hook owns cleanup, and its job-loop extension only registers the task once. The authenticated plugin API performs blocking filesystem work in worker threads. The UI uses the existing A0 modal, icon, toast and scheduler components.

Run `pytest tests/test_a0_cleaner.py tests/test_scheduler_plugin_tasks.py` and `node --test tests/test_a0_cleaner_store.mjs`. Verify scan, area switches, preview/cancel/clean, custom folders, schedule save/reopen, notifications and narrow/mobile layouts on the live framework runtime.

The 256 × 256 thumbnail uses the supplied Agent Zero logo, generated with the built-in image tool and optimized to JPEG under 20 KB. Its generation brief is in `webui/thumbnail.prompt.txt`.
