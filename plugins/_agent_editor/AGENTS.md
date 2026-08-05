# Agent Editor Plugin DOX

## Purpose

- Own the deterministic Easy and Advanced Agent Editor API and WebUI workflow.

## Ownership

- `helpers/editor.py` composes existing profile, prompt, model, tool, and skill
  owners into editor state and sparse change plans.
- `api/` owns authenticated/CSRF-protected state, save, and avatar routes.
- `webui/` owns the Alpine store, modal surface, styling, and client-side draft.
- `extensions/webui/` owns lifecycle registration on the shared modal stack and
  the global entry points used by existing WebUI surfaces.

## Local Contracts

- The editor performs zero model calls.
- Writes are limited to `usr/agents/<profile-id>` and only to paths or config
  keys listed in the validated change plan.
- Never call `helpers.subagents.save_agent_data`.
- Authored profile definitions remain YAML; editor-written plugin configs remain
  JSON.
- Profile config paths use `helpers.plugins.determine_plugin_asset_path` while
  remaining rooted in the editor's validated user-profile boundary.
- Active project tool policy is resolved through the standard plugin asset
  provenance and shown as higher priority; the editor still writes only the
  user-profile scope.
- Bundled `agents/` files are read-only.

## Verification

- Run Agent Editor, profile merge, tool policy, skill policy, API security, and
  WebUI tests, then verify the explicitly named bind-mounted runtime.

## Child DOX Index

No child DOX files.
