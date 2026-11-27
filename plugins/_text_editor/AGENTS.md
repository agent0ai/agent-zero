# Text Editor Plugin DOX

## Purpose

- Own the native LLM-friendly text editing tool for reading, writing, and patching text files.

## Ownership

- `tools/text_editor.py` owns method dispatch and agent-facing tool behavior.
- `helpers/` owns file operations, patch requests, context patching, stale-read tracking, and patch state. `helpers/log.py` owns the shared local/remote editor log factory.
- `prompts/` owns read/write/patch success and error messages.
- `default_config.yaml`, `plugin.yaml`, `README.md`, `extensions/`, and `webui/` own defaults, metadata, docs, hooks, and config UI.

## Local Contracts

- Text read/write/patch operations support local, sandbox, and connected-host paths. Local operations preserve extension hooks and canvas metadata. Sandbox line edits track destination-specific content revisions and reject writes over a changed file. Host editing uses the connector transport and its file permissions. The local tool resolves development `/a0` aliases before reads, writes, patches and freshness tracking; shared file helpers used by the remote editor retain remote path semantics.

- `extensions/webui/get_process_step_types/text-editor-types.js` registers `text_editor` as a process-step type so raw-log grouping matches the plugin's message renderer.

- `patch` supports line-number `edits`, context `patch_text`, and exact `old_text`/`new_text` replacement. Line edits remain supported and require fresh read state; they are not deprecated.
- Text Editor `write`/`patch` read the canonical UI-intent arg `open_in_canvas`; legacy aliases `open_canvas` and `open_document` still work. Document only the canonical arg in model-facing prompts.
- Fallback editor log rows without an action or path render `icon://construction Using tool 'text_editor'` without an agent-name prefix.
- `tools/text_editor.py` logs `type="text_editor"` through a `get_log_object()` override so the WebUI `get_message_handler` hook routes messages to `_text_editor/extensions/webui/get_message_handler/_10_text_editor_handler.js` instead of the default `drawMessageTool` handler.
- Plugin activation controls editor discovery for every destination.
- Repository search runs in the terminal. Keep the editor's follow-up range reads on the same destination.
- Preserve stale-read protection before patch operations.
- Validate patch structures before applying edits.
- Line-edit inserts past the last line start on a new line, even when the file has no trailing newline.
- All three local patch methods preserve the existing file's mode and, when running as root, its UID/GID before atomic replacement. Metadata failures leave the original file intact. New-file ownership follows the executing process; patching does not repair already-root-owned workspaces.
- Read back changed regions after writes or patches where the tool contract requires confirmation.
- Include the active agent context id in write/patch result metadata when available so canvas consumers can open the changed file in the correct chat context.

## Work Guidance

- Coordinate helper changes with prompt responses so the agent receives actionable edit feedback.

## Verification

- Smoke-test read, write, patch, stale-read rejection, and error handling after tool changes.

## Child DOX Index

No child DOX files.
