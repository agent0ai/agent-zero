# Memory Plugin DOX

## Purpose

- Own persistent memory, knowledge import, vector indexing, and memory management UI.

## Ownership

- `helpers/memory.py` owns FAISS store loading, embedding metadata, and knowledge preload.
- `helpers/knowledge_import.py` and `helpers/memory_consolidation.py` own import and consolidation behavior.
- `tools/` owns memory save/load/delete/forget and behavior adjustment tools.
- `api/` and `webui/` own memory dashboard and knowledge reindex/import flows.
- `prompts/`, `default_config.yaml`, and `plugin.yaml` own memory prompts, defaults, and metadata.

## Local Contracts

- Keep memory scoped by configured subdirectory/context.
- Preserve embedding metadata needed to rebuild indexes safely.
- `memory_load` accepts numeric `threshold` and `limit` values as native numbers or numeric strings and coerces them before vector search.
- Avoid storing transient action-history noise as durable memory.

## Work Guidance

- Coordinate tool, prompt, and consolidation changes so saved memories remain useful and bounded.

## Verification

- Smoke-test save, recall, delete, dashboard search/update, and knowledge import/reindex after changes.

## Child DOX Index

No child DOX files.
