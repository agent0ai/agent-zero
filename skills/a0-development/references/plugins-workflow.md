# Plugins And Development Workflow

## Source Anchors

- Plugin contract: `/a0/plugins/AGENTS.md`
- Plugin helper code: `/a0/helpers/plugins.py`
- Plugin specialist skills: `/a0/skills/a0-plugin-router/SKILL.md`, `/a0/skills/a0-create-plugin/SKILL.md`, `/a0/skills/a0-debug-plugin/SKILL.md`, `/a0/skills/a0-review-plugin/SKILL.md`
- Root development contract: `/a0/AGENTS.md`

## Plugin-First Rule

Plugins are the primary way to extend Agent Zero. A plugin can bundle:

- `plugin.yaml`
- `default_config.yaml`
- `hooks.py`
- `execute.py`
- `tools/`
- `api/`
- `helpers/`
- `prompts/`
- `skills/`
- `extensions/python/`
- `extensions/webui/`
- `webui/`
- plugin-local docs and assets

Use root framework directories only when changing bundled framework behavior itself. For custom or experimental work, use `usr/plugins/<plugin>/` unless the task is explicitly to change a bundled plugin.

## Imports And Runtime

- Bundled plugins under `plugins/` may use `plugins.<plugin_name>...` imports.
- User plugins under `usr/plugins/` should use `usr.plugins.<plugin_name>...` imports.
- Avoid `sys.path` hacks and symlink-dependent imports.
- `hooks.py` runs inside the framework runtime (`/opt/venv-a0` in Docker).
- If a plugin must prepare the agent execution runtime or system packages, it must explicitly target that environment in a subprocess.

## Manifest And Configuration

Every plugin needs `plugin.yaml`. Runtime fields include:

- `name`
- `title`
- `description`
- `version`
- `settings_sections`
- `per_project_config`
- `per_agent_config`
- `always_enabled`

Defaults belong in `default_config.yaml`. Runtime user settings belong under `usr/`.

Settings resolution order is project/profile, project, user/profile, user plugin config, then bundled `default_config.yaml`.

## Activation And Cleanup

- Global and scoped activation are independent.
- Activation files use `.toggle-1` for ON and `.toggle-0` for OFF.
- `always_enabled: true` forces ON and disables UI toggles.
- Plugin deletion or disablement should not leave unmanaged services, symlinks, or files outside plugin-owned paths unless explicitly documented with cleanup.

## Routes And UI

Plugin routes:

| Route | Purpose |
|---|---|
| `GET /plugins/<name>/<path>` | Static/plugin web assets. |
| `POST /api/plugins/<name>/<handler>` | Plugin API handler. |
| `POST /api/plugins` | Plugin management actions. |

Plugin settings UIs should bind saved values to `config.*` and modal-only state/actions to `context.*` through `$store.pluginSettingsPrototype`.

Plugin UI errors, warnings, success, and info should use the A0 notification system.

## Workflow

1. Decide whether the request is plugin-specific. If yes, load `a0-plugin-router`.
2. If creating a plugin, load `a0-create-plugin`.
3. If debugging a plugin, load `a0-debug-plugin`.
4. If reviewing or publishing a plugin, load `a0-review-plugin` or `a0-contribute-plugin`.
5. Read `plugins/AGENTS.md` and any plugin-local `AGENTS.md`.
6. Keep changes inside the plugin boundary unless shared framework behavior truly belongs in `helpers/` or root code.
7. Update plugin docs/DOX when user-visible behavior, configuration, routes, hooks, or cleanup changes.

## Verification

- Run plugin-specific tests after changing a bundled plugin.
- Run framework tests for touched tools, API handlers, extension points, settings, or WebUI surfaces.
- Smoke-test external-service, browser, desktop, or connector integrations when practical.
- For discovery banners/cards, verify rendering, dismiss behavior, ordering, and CTA behavior.
