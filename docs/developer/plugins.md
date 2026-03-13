# Plugins

This page documents the current Agent Zero plugin system, including manifest format, discovery rules, scoped configuration, activation behavior, and how to share a plugin with the community.

## Overview

Plugins extend Agent Zero through convention-based folders. A plugin can provide:

- Backend: API handlers, tools, helpers, Python lifecycle extensions
- Frontend: WebUI components and extension-point injections
- Agent profiles: plugin-scoped subagent definitions
- Settings: scoped plugin configuration loaded through the plugin settings store
- Activation control: global and per-scope ON/OFF rules

Primary roots (priority order):

1. `usr/plugins/` (user/custom plugins)
2. `plugins/` (core/built-in plugins)

On name collisions, user plugins take precedence.

## Manifest (`plugin.yaml`)

Every plugin must contain `plugin.yaml`. This is the **runtime manifest** — it drives Agent Zero behavior. It is distinct from the index manifest used when publishing to the Plugin Index (see [Publishing to the Plugin Index](#publishing-to-the-plugin-index) below).

```yaml
title: My Plugin
description: What this plugin does.
version: 1.0.0
settings_sections:
  - agent
per_project_config: false
per_agent_config: false
always_enabled: false
```

Field reference:

- `title`: UI display name
- `description`: short plugin summary
- `version`: plugin version string
- `settings_sections`: where plugin settings appear (`agent`, `external`, `mcp`, `developer`, `backup`)
- `per_project_config`: enables project-scoped settings/toggles
- `per_agent_config`: enables agent-profile-scoped settings/toggles
- `always_enabled`: forces ON state and disables toggle controls

## Recommended Structure

```text
usr/plugins/<plugin_name>/
├── plugin.yaml
├── initialize.py                    # optional one-time setup script
├── hooks.py                         # optional runtime hook functions callable by the framework
├── default_config.yaml              # optional defaults
├── README.md                        # optional, shown in Plugin List UI
├── LICENSE                          # optional, shown in Plugin List UI
├── api/                             # ApiHandler implementations
├── tools/                           # Tool implementations
├── helpers/                         # shared Python logic
├── prompts/
├── agents/
│   └── <profile>/agent.yaml         # optional plugin-distributed agent profile
├── extensions/
│   ├── python/<extension_point>/
│   └── webui/<extension_point>/
└── webui/
    ├── config.html                  # optional settings UI
    └── ...
```

## Plugin Initialization (`initialize.py`)

Plugins can include an optional `initialize.py` at the plugin root for one-time setup such as installing dependencies, downloading models, or preparing databases.

- Triggered manually via the **Init** button in the Plugin List UI — never runs automatically
- Execution is tracked in `usr/plugins/<plugin_name>/init_exec.json` (timestamp + exit code)
- The modal streams output in real time and shows success/failure on completion

```python
import subprocess
import sys

def main():
    print("Installing dependencies...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "requests==2.31.0"],
        text=True,
    )
    if result.returncode != 0:
        print("ERROR: Installation failed")
        return result.returncode
    print("Done.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

Return `0` on success, non-zero on failure. Print progress for user feedback. Use `sys.executable` for pip commands.

## Runtime Hooks (`hooks.py`)

Plugins can also include an optional `hooks.py` at the plugin root. Agent Zero loads this module on demand and calls exported functions by name through `helpers.plugins.call_plugin_hook(...)`.

- `hooks.py` executes inside the **Agent Zero framework runtime and Python environment**.
- Use it for framework-internal operations such as install hooks, registration, cache preparation, file setup, or other work that needs direct access to framework internals.
- Hook functions may be synchronous or async.
- Hook modules are cached, so edits may require a plugin refresh or cache clear before changes are picked up.

Current built-in usage: the plugin installer calls `install()` from `hooks.py` after copying a plugin into place.

### Dependency and environment behavior

- If `hooks.py` runs `sys.executable -m pip install ...`, it installs into the **same Python environment that is currently running Agent Zero**.
- That is the correct target for dependencies needed by your plugin's backend code inside the framework runtime.
- It is not automatically the right target for packages intended only for the separate agent execution runtime or for system-level binaries.

If you need to install into a different environment, do it explicitly from a subprocess. In practice, that means targeting the correct interpreter or activating the correct environment inside the subprocess before running `pip` or another package manager.

Examples of the right approach:

- call a specific Python executable for the target runtime
- activate the target virtualenv in a subprocess shell command before invoking `pip`
- run OS-level package installation from a subprocess prepared for the intended environment

In Docker deployments, `hooks.py` normally affects the framework runtime at `/opt/venv-a0`, while the agent execution runtime is `/opt/venv`.

## Settings Resolution

Plugin settings are resolved by scope. Higher priority overrides lower priority:

1. `project/.a0proj/agents/<profile>/plugins/<name>/config.json`
2. `project/.a0proj/plugins/<name>/config.json`
3. `usr/agents/<profile>/plugins/<name>/config.json`
4. `usr/plugins/<name>/config.json`
5. `plugins/<name>/default_config.yaml` (fallback defaults)

Notes:

- Runtime reads support JSON and YAML fallback files.
- Save path is scope-specific and persisted through plugin settings APIs.

## Activation Model

Activation is independent per scope and file-based:

- `.toggle-1` means ON
- `.toggle-0` means OFF
- no explicit rule means ON by default

WebUI activation states:

- `ON`: explicit ON or implicit default
- `OFF`: explicit OFF rule at selected scope
- `Advanced`: at least one project/agent-profile override exists

`always_enabled: true` bypasses OFF state and keeps the plugin ON in both backend and UI.

## UI Flow

Current plugin UX surfaces activation in two places:

- Plugin list: simple ON/OFF selector, with `Advanced` option when scoped overrides are enabled
- Plugin switch modal: scope-aware ON/OFF controls per project/profile, with direct handoff to settings

Scope synchronization behavior:

- Opening "Configure Plugin" from the switch modal propagates current scope into settings store
- Switching scope in settings also mirrors into toggle store so activation status stays aligned

## API Surface

Core plugin management endpoint: `POST /api/plugins`

Supported actions:

- `get_config`
- `save_config`
- `list_configs`
- `delete_config`
- `toggle_plugin`
- `get_doc` (fetches README.md or LICENSE for display in the UI)

## Publishing to the Plugin Index

The **Plugin Index** is a community-maintained repository at https://github.com/agent0ai/a0-plugins. Plugins listed there are discoverable by all Agent Zero users.

### Two Distinct plugin.yaml Files

There are two completely different `plugin.yaml` schemas — they must not be confused:

**Runtime manifest** (inside your plugin's own repo, drives Agent Zero behavior):
```yaml
title: My Plugin
description: What this plugin does.
version: 1.0.0
settings_sections:
  - agent
per_project_config: false
per_agent_config: false
always_enabled: false
```

**Index manifest** (submitted to `a0-plugins` under `plugins/<your-plugin-name>/`, drives discoverability only):
```yaml
title: My Plugin
description: What this plugin does.
github: https://github.com/yourname/your-plugin-repo
tags:
  - tools
  - example
```

The index manifest has only four fields (`title`, `description`, `github`, `tags`). The `github` URL must point to a public GitHub repository that contains a runtime `plugin.yaml` at the **repository root**.

### Repository Structure for Community Plugins

Plugin repos should expose the plugin contents at the repo root, so they can be cloned directly into `usr/plugins/<name>/`:

```text
your-plugin-repo/          ← GitHub repository root
├── plugin.yaml            ← runtime manifest
├── default_config.yaml
├── README.md
├── LICENSE
├── api/
├── tools/
├── extensions/
└── webui/
```

### Submission Process

1. Create a GitHub repository with the runtime `plugin.yaml` at the repo root.
2. Fork `https://github.com/agent0ai/a0-plugins`.
3. Add `plugins/<your-plugin-name>/plugin.yaml` (index manifest) to your fork, and optionally a square thumbnail image (≤ 20 KB, named `thumbnail.png|jpg|webp`).
4. Open a Pull Request. One PR must add exactly one new plugin folder.
5. CI validates automatically. A maintainer reviews and merges.

Submission rules:
- Folder name: unique, stable, lowercase, kebab-case
- Folders starting with `_` are reserved for internal use
- `title`: max 50 characters
- `description`: max 500 characters
- `tags`: optional, up to 5, see https://github.com/agent0ai/a0-plugins/blob/main/TAGS.md

### Plugin Marketplace (Coming Soon)

A built-in **Plugin Marketplace** (always-active plugin) will allow users to browse the Plugin Index and install or update community plugins directly from the Agent Zero UI without leaving the application. This section will be updated once the marketplace plugin is released.

## User Feedback in Plugin UI (Notifications)

Plugin UIs must use the **A0 notification system** for user feedback. Do not show errors or success via inline elements (e.g. a red box bound to `store.error`).

- **Frontend**: Use `toastFrontendError(message, title)`, `toastFrontendSuccess(message, title)`, etc. from `/components/notifications/notification-store.js`, or `$store.notificationStore.frontendError(...)` in templates.
- **Backend**: Use `AgentNotification.error(...)`, `AgentNotification.success(...)` from `helpers.notification`.

This keeps toasts and notification history consistent. See [Notifications](notifications.md) for the full API.

## See Also

- `docs/agents/AGENTS.plugins.md` for full architecture details
- `skills/a0-create-plugin/SKILL.md` for plugin authoring workflow (agent-facing)
- `plugins/README.md` for core plugin directory overview

## Frontend Extension Notes

- HTML breakpoints are preferred when the core template already exposes an `x-extension` anchor.
- JS hooks are the right fit for runtime-built UI surfaces. For example, `confirm_dialog_after_render` can extend the shared confirm dialog using the supplied DOM nodes and caller `extensionContext`.
