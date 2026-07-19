# Chat Compaction Plugin DOX

## Purpose

- Own compacting an entire chat history into a single optimized summary message.
- Keep compaction prompt, helper, API, and modal behavior aligned.

## Ownership

- `plugin.yaml` and `default_config.yaml` own metadata and compaction defaults.
- `api/compact_chat.py` owns the compaction endpoint.
- `helpers/compactor.py` owns summary generation and history rewrite logic.
- `prompts/` owns compaction system and message prompts.
- `webui/` owns the compaction modal and store.

## Local Contracts

- Preserve chat history integrity and persistence after compaction.
- Backup JSON and transcript artifacts must remain UTF-8 writable when chat content contains malformed Unicode such as lone surrogates.
- Keep generated summaries bounded by configured model and token limits.
- Preserve loaded skill names from `skill_instructions` metadata without copying full skill bodies into compacted summaries.
- After replacing local history, clear the active Responses provider continuation while preserving stored response IDs for cleanup.
- Do not discard original context data unless the compaction flow explicitly owns that behavior.

## Work Guidance

- Coordinate prompt changes with helper behavior and UI confirmation text.

## Verification

- Smoke-test compacting a chat and reloading it after persistence.

## Child DOX Index

No child DOX files.
