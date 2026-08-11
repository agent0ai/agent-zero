# migration_preview.py DOX

## Purpose

Preview a user-selected harness export without changing Agent Zero state.

## Contract

- Auth and CSRF use the default `ApiHandler` protections.
- Accepts multipart `source` plus one or more `files[]` values.
- Rejects unsafe archives and uploads larger than 256 MiB.
- Returns counts, chat titles, knowledge files, skills, exclusions, and warnings.
- Never returns source message bodies or credential values.

## Verification

Run `python -m pytest plugins/_migrate_agents/tests -q` from the Agent Zero root.
