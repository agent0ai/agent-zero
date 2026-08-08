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
- Writes are limited to the selected profile layer — global
  `usr/agents/<profile-id>` or project
  `usr/projects/<project>/.a0proj/agents/<profile-id>` — and only to paths or
  config keys listed in the validated change plan.
- Never call `helpers.subagents.save_agent_data`.
- Authored profile definitions remain YAML; editor-written plugin configs remain
  JSON.
- Profile config paths use `helpers.plugins.determine_plugin_asset_path` for the
  selected Global or project scope and remain rooted in that exact validated
  profile boundary.
- Project profiles inherit the existing global, plugin, and bundled layers.
  Removing or deleting in project scope never mutates those inherited layers;
  only agents created in the selected scope are deletable.
- Bundled `agents/` files are read-only.
- Advanced prompt text is directly editable; per-file close/check actions
  discard or accept the current edit checkpoint, while the editor's global save
  remains the only persistence boundary.
- The configurable tool catalog is visible in both modes; Easy provides direct
  allow/block checkboxes and points to Advanced for skill access. Skills remain
  Advanced-only. Advanced keeps both complete selectors visible but disabled
  for inherited access and interactive for custom access. Framework-required
  tools remain absent from the tool catalog.
- Model selection reuses `_model_config`'s compact preset dropdown and preset
  editor; Agent Editor persists only the scoped preset reference.
- Manage agents reuses the plugin-settings project vocabulary: Global or one
  existing project. Save & test activates that same scope in the fresh chat.
- The WebUI uses the shared modal stack, labeled prompt scroll regions, and
  24px-or-larger policy and text-action targets.

## Verification

- Run Agent Editor, profile merge, tool policy, skill policy, API security, and
  WebUI tests, then verify the explicitly named bind-mounted runtime.

## Child DOX Index

No child DOX files.
