# Text Editor Plugin DOX

## Purpose

- Own the native LLM-friendly text editing tool for reading, writing, and patching text files.

## Ownership

- `tools/text_editor.py` owns method dispatch and agent-facing tool behavior.
- `helpers/` owns file operations, patch requests, context patching, stale-read tracking, and patch state.
- `prompts/` owns read/write/patch success and error messages.
- `default_config.yaml`, `plugin.yaml`, `README.md`, `extensions/`, and `webui/` own defaults, metadata, docs, hooks, and config UI.

## Local Contracts

- Preserve stale-read protection before patch operations.
- Validate patch structures before applying edits.
- Read back changed regions after writes or patches where the tool contract requires confirmation.
- Include the active agent context id in write/patch result metadata when available so canvas consumers can open the changed file in the correct chat context.

## Work Guidance

- Coordinate helper changes with prompt responses so the agent receives actionable edit feedback.

## Verification

- Smoke-test read, write, patch, stale-read rejection, and error handling after tool changes.

## Child DOX Index

No child DOX files.
