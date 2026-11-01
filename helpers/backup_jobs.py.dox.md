# Backup Jobs DOX

## Purpose

- Own background backup creation and the lifetime of downloadable archives.

## Runtime Contracts

- `BackupJobs.start(name, create)` returns a random job ID immediately and runs the async archive builder in a dedicated daemon thread with its own event loop. Scanning, chat persistence, and ZIP compression outlive the initiating HTTP request.
- The builder receives a server-owned output path in a private temporary directory. The requested download name is metadata and never selects the job's filesystem path.
- Each process holds one job. A running job or an active download prevents starting another backup. A new job replaces an idle completed or failed job.
- `status(job_id)` returns `running`, `completed`, or `failed`, with a user-facing error for failure. Detailed exceptions go to the server log.
- Completed and failed jobs expire one hour after creation finishes. Failed output is cleaned immediately; completed output is cleaned on expiry or replacement.
- `acquire_download` opens a file lease. The response must call `release_download` on close, including client disconnects. Release is idempotent; expiry defers deletion until all readers close.
- Jobs are process-local and disappear after a server restart. All callers must retain the endpoint's authentication and CSRF checks.

## Verification

- Run `pytest tests/test_backup_jobs.py` for asynchronous creation, real ZIP content, concurrent requests, failures, retention, downloads, and HTTP security.
- Run `node --test tests/test_backup_store.mjs` for polling, cancellation, resuming, and errors.
