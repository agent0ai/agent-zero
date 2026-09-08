# Files extraction

Authenticated/CSRF-protected handler validates the request, delegates extraction to `helpers.file_archives`, emits the existing mutation hook and refreshes the listing. Keep archive inspection, size/count policy, controlled writes and cleanup in helpers. The operation is distinct from Backup & Restore.

Verify `tests/test_file_browser_archives.py` and `tests/test_file_transfer_safety.py`.

Validation and expansion-limit failures use the existing error dictionary response; no HTTP exception is propagated into the shared API handler.
