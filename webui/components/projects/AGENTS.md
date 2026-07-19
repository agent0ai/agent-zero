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
- Do not expose project secrets in logs, URLs, or long-lived frontend state unnecessarily.
- Preserve scoped settings interactions with plugins, models, skills, and MCP servers.
- Project model settings select a global `_model_config` preset; they do not own copied model dictionaries or project-local preset definitions.

## Work Guidance

- Verify project edit flows when changing shared project store state.

## Verification

- Smoke-test create, select, edit, secrets, LLM, skills, MCP servers, and file-structure flows after changes.

## Child DOX Index

No child DOX files.
