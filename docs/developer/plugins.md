# Plugins

This page documents the current Agent Zero plugin system, including manifest format, discovery rules, scoped configuration, activation behavior, and how to share a plugin with the community.

## Overview

Plugins extend Agent Zero through convention-based folders. A plugin can provide:

- Backend: API handlers, tools, helpers, Python lifecycle extensions, and implicit `@extensible` hooks
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
name: my_plugin              # required for community plugins (^[a-z0-9_]+$, must match dir name)
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

- `name`: plugin identifier; required by CI for index submission; must be `^[a-z0-9_]+$` and match the index folder name exactly
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
├── execute.py                       # optional user-triggered plugin script
├── hooks.py                         # optional runtime hook functions callable by the framework
├── default_config.yaml              # optional defaults
├── README.md                        # optional locally; strongly recommended for community plugins
├── LICENSE                          # optional locally (shown in Plugin List UI when present); required at repo root for Plugin Index submission
├── api/                             # ApiHandler implementations
├── tools/                           # Tool implementations
├── helpers/                         # shared Python logic
├── prompts/
├── agents/
│   └── <profile>/agent.yaml         # optional plugin-distributed agent profile
├── extensions/
│   ├── python/<extension_point>/
│   ├── python/_functions/<module>/<qualname>/<start|end>/
│   └── webui/<extension_point>/
└── webui/
    ├── config.html                  # optional settings UI
    └── ...
```

## Python Extension Layouts

Use one of these backend layouts:

- `extensions/python/<extension_point>/` for named lifecycle hooks such as `agent_init`, `system_prompt`, or `tool_execute_before`
- `extensions/python/_functions/<module>/<qualname>/<start|end>/` for implicit `@extensible` hook targets

The `_functions` layout keeps the full module path and nested `__qualname__` path, which avoids collisions between similarly named functions. Do not create the retired flattened form `extensions/python/<module>_<qualname>_<start|end>/`; it is stale and will not be resolved by the current extensible system.

## Python Imports for User Plugins

For plugin-local Python imports inside `usr/plugins/<plugin_name>/`, use the
fully qualified `usr.plugins.<plugin_name>...` path.

Good:

```python
from usr.plugins.my_plugin.helpers.runtime import do_work
import usr.plugins.my_plugin.helpers.state as state
```

Avoid:

```python
sys.path.insert(0, ...)
from helpers.runtime import do_work

from plugins.my_plugin.helpers.runtime import do_work
```

This is the preferred pattern because it keeps plugin imports explicit,
requires no directory renaming like `name_helpers`, requires no symlink into
`plugins/`, and leaves no global import hack behind when the plugin is deleted.

## Plugin Script (`execute.py`)

Plugins can include an optional `execute.py` at the plugin root for user-triggered operations such as setup, post-install actions, maintenance, repair steps, or other manual tasks that should run only when explicitly requested.

- Triggered manually from the Plugin List UI — never runs automatically
- Suitable for rerunnable operations such as refreshing caches, rebuilding generated files, running migrations, or syncing plugin-managed resources
- Execution state is recorded per plugin with timestamp and exit code metadata
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
    print("Refreshing plugin resources...")
    print("Done.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

Return `0` on success, non-zero on failure. Print progress for user feedback. Use `sys.executable` for pip commands. Prefer making the script safe to run more than once; if reruns are not safe, detect the current state and print a clear explanation.

First rule of plugin side effects: do not modify the system permanently unless
the user explicitly asked for it and the plugin also provides a cleanup path.
Deleting a plugin should not leave behind symlinks, orphaned services,
framework patches, or unmanaged files outside plugin-owned locations.

## Runtime Hooks (`hooks.py`)

Plugins can also include an optional `hooks.py` at the plugin root. Agent Zero loads this module on demand and calls exported functions by name through `helpers.plugins.call_plugin_hook(...)`.

- `hooks.py` executes inside the **Agent Zero framework runtime and Python environment**.
- Use it for framework-internal operations such as install hooks, pre-update hooks, registration, cache preparation, file setup, or other work that needs direct access to framework internals.
- Hook functions may be synchronous or async.
- Hook modules are cached, so edits may require a plugin refresh or cache clear before changes are picked up.
- Hooks should be reversible and cleanup-safe. Prefer plugin-owned paths and framework-managed state over permanent system modifications.

Use `execute.py` when the user should explicitly decide when the operation runs. Use `hooks.py` or lifecycle extensions when the work belongs to framework-managed behavior.

Current built-in usage:
- the plugin installer calls `install()` from `hooks.py` after copying a plugin into place
- the plugin updater calls `pre_update()` from `hooks.py` immediately before pulling new plugin code into place

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

### Two Distinct Manifest Files

There are two completely different manifest files — they must not be confused:

**Runtime manifest** (`plugin.yaml`, inside your plugin's own repo — drives Agent Zero behavior):
```yaml
name: my_plugin              # REQUIRED for index submission; must match index folder name
title: My Plugin
description: What this plugin does.
version: 1.0.0
settings_sections:
  - agent
per_project_config: false
per_agent_config: false
always_enabled: false
```

**Index manifest** (`index.yaml`, submitted to `a0-plugins` under `plugins/<your_plugin_name>/` — drives discoverability only):
```yaml
title: My Plugin
description: What this plugin does.
github: https://github.com/yourname/your-plugin-repo
tags:
  - tools
  - example
screenshots:                    # optional, up to 5 full image URLs
  - https://raw.githubusercontent.com/yourname/your-plugin-repo/main/docs/screen.png
```

The index manifest file is named `index.yaml` (not `plugin.yaml`). Required fields: `title`, `description`, `github`. Optional: `tags` (up to 5), `screenshots` (up to 5 URLs). The `github` URL must point to a public GitHub repository that contains a runtime `plugin.yaml` at the **repository root**, and that `plugin.yaml` must include a `name` field matching the index folder name exactly. That repository must also include a `LICENSE` file at its root (Plugin Index / community contribution requirement).

### Repository Structure for Community Plugins

Plugin repos should expose the plugin contents at the repo root, so they can be cloned directly into `usr/plugins/<name>/`:

```text
your-plugin-repo/          ← GitHub repository root
├── plugin.yaml            ← runtime manifest (must include name field)
├── default_config.yaml
├── README.md
├── LICENSE                ← required for Plugin Index listings
├── api/
├── tools/
├── extensions/
└── webui/
```

### Submission Process

1. Create a GitHub repository with the runtime `plugin.yaml` (including the `name` field) at the repo root.
2. Fork `https://github.com/agent0ai/a0-plugins`.
3. Create folder `plugins/<your_plugin_name>/` and add `index.yaml` (the index manifest, not `plugin.yaml`). Optionally add a square thumbnail image (≤ 20 KB, named `thumbnail.png|jpg|webp`).
4. Open a Pull Request. One PR must add exactly one new plugin folder.
5. CI validates automatically. A maintainer reviews and merges.

Submission rules:
- Folder name: unique, stable, `^[a-z0-9_]+$` (lowercase, numbers, underscores — no hyphens)
- Folder name must exactly match the `name` field in your remote `plugin.yaml`
- The GitHub repo must include `LICENSE` at its root (community contribution requirement)
- Folders starting with `_` are reserved for internal use
- `title`: max 50 characters
- `description`: max 500 characters
- `index.yaml` total: max 2000 characters
- `tags`: optional, up to 5, see https://github.com/agent0ai/a0-plugins/blob/main/TAGS.md
- `screenshots`: optional, up to 5 full image URLs (png/jpg/webp, each ≤ 2 MB)

### Plugin Hub

Agent Zero now exposes the community **Plugin Hub** through the always-enabled **Plugin Installer** plugin. Users can browse Plugin Index entries directly from the Plugins UI without leaving the application.

Users can open the Plugin Hub from the **Plugins** dialog in two ways:

- click the **Browse** tab after **Custom** and **Builtin**
- click **Install** in the plugin list toolbar to open the installer modal, which starts on its own **Browse** tab

The Plugin Hub supports search, filtering, sorting, and a plugin detail view with README content and the install action.

## User Feedback in Plugin UI (Notifications)

Plugin UIs must use the **A0 notification system** for user feedback. Do not show errors or success via inline elements (e.g. a red box bound to `store.error`).

- **Frontend**: Use `toastFrontendError(message, title)`, `toastFrontendSuccess(message, title)`, etc. from `/components/notifications/notification-store.js`, or `$store.notificationStore.frontendError(...)` in templates.
- **Backend**: Use `AgentNotification.error(...)`, `AgentNotification.success(...)` from `helpers.notification`.

This keeps toasts and notification history consistent. See [Notifications](notifications.md) for the full API.

## See Also

- `docs/agents/AGENTS.plugins.md` for full architecture details
- `skills/a0-plugin-router/SKILL.md` for the primary agent-facing entry point across plugin create/review/manage/contribute/debug tasks
- `skills/a0-create-plugin/SKILL.md` for direct plugin authoring workflow when the task is specifically to build or extend a plugin
- `plugins/README.md` for core plugin directory overview

## Frontend Extension Notes

- HTML breakpoints are preferred when the core template already exposes an `x-extension` anchor.
- JS hooks are the right fit for runtime-built UI surfaces. For example, `confirm_dialog_after_render` can extend the shared confirm dialog using the supplied DOM nodes and caller `extensionContext`.
