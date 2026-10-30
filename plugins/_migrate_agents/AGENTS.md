# Migrate Agents DOX

## Purpose

- Own the bundled workflow for previewing and importing retained work from Pi, OpenClaw, Hermes Agent, OpenCode, Claude Code, and Codex.

## Ownership

- `helpers/migration.py` owns source parsing, redaction, limits, preview data, and native chat conversion.
- `api/migration_preview.py` owns read-only upload inspection; `api/migration_import.py` owns confirmed writes.
- `webui/` owns source selection, upload, review, consent, and progress UI.
- `tests/` owns parser, privacy, archive-safety, native-chat, project, and import-helper regression coverage.

## Local Contracts

- The bundled folder, manifest name, Python imports, and HTTP routes use `_migrate_agents`.
- Preview must not write Agent Zero state. Import starts only after explicit category selection and review consent.
- Credentials, authentication state, hidden reasoning, schedules, live services, and replayable tool execution stay excluded.
- Imported knowledge and skills remain namespaced below `usr/knowledge/_migrate_agents/` and `usr/skills/_migrate_agents/`.
- Preserve source provenance and do not claim transcript metadata can reconstruct unavailable project files.
- Store native chat provenance in `data.migrate_agents`; underscore-prefixed context data is transient and stripped by chat persistence.
- Pi JSONL versions 1–3 preserve retained public history as separate branch chats, with shared ancestors repeated. Validate parent links and bound branch expansion before normalization. Do not replay system messages, reasoning, compaction/branch summaries, context edits, extension records, or context-excluded shell commands; report omitted context records. Image bytes become omission markers. Tool arguments, results, errors, and public shell records use the shared redaction and inert-history path.

## Work Guidance

- Extend the shared parser and redaction path instead of adding source-specific import side channels.
- Keep source commands, supported artifacts, exclusions, and mapping limits accurate in both WebUI copy and README.
- Keep bundled harness assets local and update `webui/assets/ATTRIBUTION.md` when their provenance changes.

## Verification

- Run `conda run -n a0 python -m pytest plugins/_migrate_agents/tests -q`.
- For WebUI changes, verify the mounted modal and upload flow against the named live Agent Zero runtime.

## Child DOX Index

No child DOX files.
