# Project files API

- Authenticated, CSRF-protected native Projects endpoint for workspace, instruction, and knowledge files in a managed project.
- Body specifies `project`, `area`, relative `path` and `action`. Upload uses multipart with a `file`; text writes and deletion accept a revision. Download streams an attachment.
- Authorization resolves the current membership and native project binding before opening any file. Scope errors and version conflicts return 403 and 409 respectively.
- Verify authorized same-project reads, rejected other-project reads and stale writes from two sessions.
- The native Files and Editor surfaces reuse project-scoped list, limits, upload, read, save, rename, move, delete, and download actions. Rename and move reject overwrites. Native Editor retains the original content revision through save.
