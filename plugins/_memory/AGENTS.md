# Memory Plugin DOX

## Purpose

- Own persistent memory, knowledge import, vector indexing, and memory management UI.

## Ownership

- `helpers/memory.py` owns FAISS store loading, embedding metadata, and knowledge preload.
- `helpers/knowledge_import.py` and `helpers/memory_consolidation.py` own import and consolidation behavior.
- `tools/memory.py` owns the single `memory` tool whose `action` arg selects load, save, delete or forget.
- Legacy `tools/memory_{load,save,delete,forget}.py` files re-export that implementation for saved prompts/calls. Their names fix the action regardless of supplied arguments; only `memory` is advertised to models.
- The memory tool logs messages as its own `memory` type with icon verb headlines; `extensions/webui/get_message_handler/` owns the shared `MEM` badge presentation in the behavior adjustment brain pink accent and `extensions/webui/get_process_step_types/` registers the types.
- `get_tool_message_handler` reuses the memory renderer for saved `type="tool"` logs with legacy memory names.
- `api/` and `webui/` own memory dashboard and knowledge reindex/import flows.
- `extensions/webui/` owns the welcome-screen Memory card and the quick-actions dropdown entries.
- `prompts/`, `default_config.yaml`, and `plugin.yaml` own memory prompts, defaults, and metadata.

## Local Contracts

- Keep memory scoped by configured subdirectory/context.
- Shared tool policy preserves saved per-action memory permissions in both unified and legacy calls; an allowed load must not grant save, delete or forget. Explicit tool-wide blocks cover every alias.
- Preserve embedding metadata needed to rebuild indexes safely.
- Delayed recall results must survive `LoopData` replacement, stay scoped to the originating memory/profile/project, and be consumed once by the next prompt; do not persist live task objects into chat JSON.
- The `load` action accepts numeric `threshold` and `limit` values as native numbers or numeric strings and coerces them before vector search.
- The tool-prompt declaration must start with `args` so native Responses models receive the `memory` tool.
- Auto-recall embeds each prepared query once and reuses that vector for the memory and solution filters; manual `load` keeps the ordinary text-query path.
- Keep auto-recall context capability-neutral; memory-tool routing belongs in
  the policy-filtered memory tool prompt.
- Avoid storing transient action-history noise as durable memory.

## Work Guidance

- Both dashboard selection toolbars use icon-only actions with accessible labels and the shared borderless close control before the selection count.
- Dashboard selection checkboxes reuse the shared native theme from `webui/index.css`; keep header and row controls 16px and centered in their table cells.
- Keep dashboard metadata JSON-safe without changing shared API serialization.
- Coordinate tool, prompt, and consolidation changes so saved memories remain useful and bounded.

## Verification

- Smoke-test save, recall, delete, dashboard search/update, and knowledge import/reindex after changes.
- Run `tests/test_tool_policy.py` and `tests/test_tool_compatibility.py` for action permissions and legacy calls, and `tests/test_webui_tool_compatibility.py` for saved-log rendering.

## Child DOX Index

No child DOX files.
