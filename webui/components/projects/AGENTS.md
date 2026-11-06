# Project Components DOX

## Purpose

- Own WebUI project creation, selection, editing, secrets, model, skill, MCP server, and file-structure components.

## Ownership

- `projects-store.js` owns project state and actions.
- `project-create.html`, `project-list.html`, and `project-selector.html` own project creation and navigation UI.
- `project-edit*.html` files own project editing subsections.
- `project-file-structure-test.html` owns file-structure test UI.

## Local Contracts

- Keep project API payloads synchronized with backend project handlers.
- `loadProjectsList()` retains the current list when response values are unchanged, avoiding sidebar regrouping on window focus. Changed project values and ordering still replace the list.
- Do not expose project secrets in logs, URLs, or long-lived frontend state unnecessarily.
- Preserve scoped settings interactions with plugins, models, skills, and MCP servers.
- Project model settings select a global `_model_config` preset; they do not own copied model dictionaries or project-local preset definitions.
- Agent Editor owns profile-scoped availability mutations. Project edit payloads
  do not include that state, so unrelated project saves cannot restore stale
  toggle values.
- `project-selector.html` caps its dropdown with `--project-dropdown-available-height`, recomputed from the trigger's viewport position on open and on window resize, so the menu never extends past the window bottom and its rows stay scrollable in short windows. The cap floors at zero like the model switcher, so a trigger near the bottom edge yields a collapsed menu instead of a menu outside the viewport; the shared `.dropdown-menu` `overflow-y: auto` provides the scrolling.
- `#time-date-container` stacks above the composer `#input-section`, so the open project dropdown paints over the chat input; the mobile sidebar overlay stays one layer above the container. Do not lower the container below the composer again.

## Work Guidance

- Verify project edit flows when changing shared project store state.
- Resize the window short and tall with the project dropdown open to confirm the menu still fits and scrolls.

## Verification

- Smoke-test create, select, edit, secrets, LLM, skills, MCP servers, and file-structure flows after changes.

## Child DOX Index

No child DOX files.
