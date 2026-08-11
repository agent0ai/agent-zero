# migration_import.py DOX

## Purpose

Commit a previously reviewed harness export into native Agent Zero storage.

## Contract

- Auth and CSRF use the default `ApiHandler` protections.
- Accepts the same multipart export as the preview endpoint plus category toggles.
- Creates new chat IDs; it never overwrites an existing chat.
- Writes imported knowledge below `usr/knowledge/_migrate_agents/` and skills below `usr/skills/_migrate_agents/` using unique directories and atomic files.
- Does not import credentials, provider keys, authentication state, schedules, channel bindings, or executable runtime services.

## Verification

Run `python -m pytest plugins/_migrate_agents/tests -q`, then exercise preview and import against the live framework runtime.
