# Plugins And Development Workflow

## Source Anchors

- Plugin contract: `/a0/plugins/AGENTS.md`
- Plugin helper code: `/a0/helpers/plugins.py`
- Sandbox placement and interfaces: [Sandboxed plugin runtimes](../../../docs/developer/plugin-sandboxes.md#choosing-dependency-location), `/a0/helpers/sandbox.py` and `/a0/helpers/sandbox_worker.py`
- Plugin entrypoints: `/a0/skills/a0-create-plugin/SKILL.md` and `/a0/skills/a0-manage-plugin/SKILL.md`
- Root development contract: `/a0/AGENTS.md`

## Plugin-First Rule

Plugins are the primary way to extend Agent Zero. A plugin can bundle:

- `plugin.yaml`
- `default_config.yaml`
- `hooks.py` (required for setup, dependencies, initialization, and cleanup)
- `execute.py` (optional non-lifecycle manual action only)
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
- Prefer existing sandboxes for plugin-owned Python/Node/native packages, heavy inference, browser/document/media workers and external integration clients. Keep lightweight tools, hooks, configuration and authenticated API/UI adapters in the framework and call the guest without importing guest-only libraries or adding them to main requirements/global installs.
- Main-environment dependencies are legitimate only for functionality that must execute there; document the concrete need and keep that set minimal. `hooks.py` still runs in the framework's global Docker Python environment, so worker sandboxing does not isolate hooks.
- Hooks and framework management APIs own install/update/uninstall; guest setup may delegate to existing automatic workers using guest-owned manifests/installers and persistent environments. Provision at first actual use, or at enablement/startup for early-needed features and configured listeners. Preserve idempotent retry, disabled-state behavior and owned cleanup; never require `execute.py` or a manual post-install command. Follow `a0-create-plugin` and the sandbox source anchors above, including the current bundled-only `SandboxWorker` path limit.

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

1. For authoring, changes, review or contribution, load `a0-create-plugin` and its relevant references.
2. For finding useful plugins or managing installed ones, load `a0-manage-plugin`.
3. Honor a stated local/community target; ask only if that choice is missing before creating a new plugin.
4. Read `plugins/AGENTS.md` and any plugin-local `AGENTS.md`.
5. Keep changes inside the plugin boundary unless shared framework behavior truly belongs in root code.
6. Update plugin docs/DOX when behavior, configuration, routes, hooks or cleanup changes.

## Verification

- Check optional guest dependencies stay out of main requirements and feature import/general boot paths do not eagerly install them. Verify first-use setup/retry and early listener readiness where needed; lazy setup reduces the default footprint, not necessarily total disk after use.
- Run plugin-specific tests after changing a bundled plugin.
- Run framework tests for touched tools, API handlers, extension points, settings, or WebUI surfaces.
- Smoke-test external-service, browser, desktop, or connector integrations when practical.
- For discovery banners/cards, verify rendering, dismiss behavior, ordering, and CTA behavior.
