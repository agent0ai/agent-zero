# Project Components DOX

## Purpose

- Own WebUI project creation, selection, editing, secrets, model, skill, MCP server, and file-structure components.

## Ownership

- `projects-store.js` owns project state and actions.
- `project-create.html`, `project-list.html`, and `project-selector.html` own project creation and navigation UI.
- `project-edit*.html` files own project editing subsections.
- `project-file-structure-test.html` owns file-structure test UI.
- `project-files.html` and `project-files-store.js` own the scoped workspace, instructions, and knowledge file view for managed team projects.

## Local Contracts

- A native project selection can start a team draft without creating a chat. Selecting another project from a shared chat preserves the original project's ownership.

- The native picker keeps a member's project selection pending on Welcome. Switching to another project from an existing chat creates a chat in that project and preserves existing chat ownership.
- Shared settings and file edits submit the revisions loaded with the drafts. Keep the draft on conflict and offer the latest version for review before allowing a retry against it.

- Keep project API payloads synchronized with backend project handlers.
- `loadProjectsList()` retains the current list when response values are unchanged, avoiding sidebar regrouping on window focus. Changed project values and ordering still replace the list.
- Member snapshots prune revoked projects immediately and refresh project details when assignments change. Ignore overlapping list requests that completed after a newer request began.
- Welcome Files uses the existing Projects list as a chooser when no project is active. Selecting a project opens the native File Browser at its project root.
- Do not expose project secrets in logs, URLs, or long-lived frontend state unnecessarily.
- Preserve scoped settings interactions with plugins, models, skills, and MCP servers.
- Project model settings select a global `_model_config` preset; they do not own copied model dictionaries or project-local preset definitions.
- Agent Editor owns profile-scoped availability mutations. Project edit payloads
  do not include that state, so unrelated project saves cannot restore stale
  toggle values.

## Work Guidance

- Verify project edit flows when changing shared project store state.

## Verification

- Smoke-test create, select, edit, secrets, LLM, skills, MCP servers, and file-structure flows after changes.

## Child DOX Index

No child DOX files.
