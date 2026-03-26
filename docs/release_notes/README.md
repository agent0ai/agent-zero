# Release Notes

Create one file per release tag in this folder using the exact name `vX.Y.md`, for example `v2.33.md`.

Rules:
- The automated Docker publish workflow reads `docs/release_notes/<tag>.md` when the current latest `main` release tag is built successfully.
- Keep the notes concise and release-ready. Summarize the meaningful changes since the previous release notes tag in this folder.
- Prefer user-facing features, major fixes, notable infrastructure or packaging changes, and breaking or migration notes. Skip low-signal internal churn.
- Use normal Markdown. A short heading plus a flat bullet list is enough.
- If you intentionally want a release with no notes, leave the file empty and the workflow will publish `No release notes.`
