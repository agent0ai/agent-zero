# Migrate Agents DOX

## Purpose

- Own the bundled workflow for previewing and importing retained work from OpenClaw, Hermes Agent, OpenCode, Claude Code, and Codex.

## Ownership

- `helpers/migration.py` owns source parsing, redaction, limits, preview data, and native chat conversion.
- `api/migration_preview.py` owns read-only upload inspection; `api/migration_import.py` owns confirmed writes.
- `webui/` and the sidebar extension own source selection, upload, review, consent, and progress UI.
- `tests/` owns parser, privacy, archive-safety, native-chat, project, and import-helper regression coverage.

## Local Contracts

- The bundled folder, manifest name, Python imports, and HTTP routes use `_migrate_agents`.
- Preview must not write Agent Zero state. Import starts only after explicit category selection and review consent.
- Credentials, authentication state, hidden reasoning, schedules, live services, and replayable tool execution stay excluded.
- Imported knowledge and skills remain namespaced below `usr/knowledge/_migrate_agents/` and `usr/skills/_migrate_agents/`.
- Preserve source provenance and do not claim transcript metadata can reconstruct unavailable project files.

## Work Guidance

- Extend the shared parser and redaction path instead of adding source-specific import side channels.
- Keep source commands, supported artifacts, exclusions, and mapping limits accurate in both WebUI copy and README.
- Keep bundled harness assets local and update `webui/assets/ATTRIBUTION.md` when their provenance changes.

## Verification

- Run `conda run -n a0 python -m pytest plugins/_migrate_agents/tests -q`.
- For WebUI changes, verify the mounted modal and upload flow against the named live Agent Zero runtime.

## Child DOX Index

No child DOX files.
