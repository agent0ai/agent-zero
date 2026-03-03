# Audit Logging (JSONL)

Agent Zero writes a minimal, append-only audit trail for key actions as newline-delimited JSON (`.jsonl`), one event per line.

## Location

- Default path: `logs/audit.jsonl` (created on demand)
- Override with env var: `A0_AUDIT_LOG_PATH` (absolute or repo-relative)

Note: `logs/` is repo-controlled (directory is tracked) but log files are ignored by git by default.

## Event format

Each line is a single JSON object with these required fields:

- `timestamp` (UTC ISO-8601, e.g. `2026-03-03T12:34:56.789Z`)
- `agent_role` (e.g. `api`, `cli`, `Agent 0`)
- `user_action` (stable action identifier)
- `sources` (list of sources/URLs used; can be empty)
- `output_hash` (`sha256:<hex>` over a stable representation of the action output)
- `file_paths_touched` (list of file paths involved; can be empty)

Optional:

- `extra` (free-form structured metadata)

## Hooked actions (Issue #9)

- **User message intake**: `user_action="api:/message_async:intake"`
- **Chat export**: `user_action="api:/chat_export"`
- **Research tool invocation**: `user_action="tool:search_engine"` (and `tool:knowledge` / `tool:knowledge_tool` when used)
- **LegalFlow intent routing**: `user_action="intent:draft"` and `user_action="intent:review"`
- **Public corpus ingestion CLI**: `user_action="cli:legalflow.ingest_public_corpus"`

## Example entry

```json
{"agent_role":"api","file_paths_touched":[],"output_hash":"sha256:1f9e3d6d2d6f8e06f2a30b8d2d4a2bcb0d3b01a7b6a41d2f6b59d2b9f9c1c2a3","sources":[],"timestamp":"2026-03-03T12:34:56.789Z","user_action":"api:/message_async:intake"}
```
