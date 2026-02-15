# Agent Zero Plugins

This directory contains default plugins shipped with Agent Zero.

## Architecture

Agent Zero uses a convention-over-configuration plugin model:

- `plugin.json` is not used by runtime discovery.
- Runtime capabilities are discovered from directory structure.
- Backend owns discovery and routing; frontend consumes resolved URLs.

## Directory Conventions

Each plugin lives in `plugins/<plugin_id>/` (or `usr/plugins/<plugin_id>/` for overrides).

Capability discovery is based on these paths:

- `api/*.py` - API handlers (`ApiHandler` subclasses), exposed as `/plugins/{plugin_id}/{handler_name}`
- `tools/*.py` - Agent tools (`Tool` subclasses)
- `helpers/*.py` - Shared Python helpers
- `extensions/backend/{extension_point}/*.py` - Backend lifecycle extensions
- `extensions/frontend/**/*.html` - Frontend UI components (auto-injected via `<meta name="plugin-target">`)
- `prompts/**/*.md` - Prompt templates
- `agents/` - Agent profiles
- `extensions/frontend/` - Frontend UI assets and auto-injected components

## Frontend Auto-Injection (PoC)

Plugins can inject HTML components into the core UI. Place components under `extensions/frontend/` and declare the injection target with a `<meta>` tag:

```html
<meta name="plugin-target" content=".quick-actions-dropdown">
```

Components without the meta tag (e.g. modals, dashboards) are standalone and not auto-injected.

Resolution flow:

1. The backend parses `<meta name="plugin-target">` from each component HTML at scan time.
2. `/plugins_resolve` returns component URLs with their target selectors.
3. `plugins.js` (loaded globally) creates `<x-component>` elements at the declared target selectors.
4. The standard `components.js` MutationObserver handles loading automatically.
5. A MutationObserver in `plugins.js` retries for targets that appear after initial page render.

## Routes

- Plugin static assets: `GET /plugins/<plugin_id>/<path>`
- Plugin APIs: `/plugins/<plugin_id>/<handler>`

## Notes

- User plugins in `usr/plugins/` override repo plugins by plugin ID.
- Runtime behavior is fully convention-driven from directory structure.
