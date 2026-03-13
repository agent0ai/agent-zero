# Agent Zero - Plugins Guide

This guide covers the Python Backend and Frontend WebUI plugin architecture. Use this as the definitive reference for building and extending Agent Zero.

---

## 1. Architecture Overview

Agent Zero uses a convention-over-configuration plugin model where runtime capabilities are discovered from the directory structure.

### Internal Components

1. Backend discovery (python/helpers/plugins.py): Resolves roots (usr/plugins/ first, then plugins/) and builds the effective set of plugins.
2. Path resolution (python/helpers/subagents.py): Injects plugin paths into the agent's search space for prompts, tools, and configurations.
3. Python extensions (python/helpers/extension.py): Executes lifecycle hooks from extensions/python/<point>/.
4. WebUI extensions (webui/js/extensions.js): Injects HTML/JS contributions into core UI breakpoints (x-extension).

---

## 2. File Structure

Each plugin lives in usr/plugins/<plugin_name>/.

```text
usr/plugins/<plugin_name>/
├── plugin.yaml                   # Required: Title, version, settings + activation metadata
├── initialize.py                 # Optional: one-time setup script (dependencies, models, etc.)
├── hooks.py                      # Optional: runtime hook functions callable by the framework
├── default_config.yaml           # Optional: fallback settings defaults
├── README.md                     # Optional: shown in Plugin List UI
├── LICENSE                       # Optional: shown in Plugin List UI
├── conf/
│   └── model_providers.yaml      # Optional: add or override model providers
├── api/                          # API handlers (ApiHandler subclasses)
├── tools/                        # Agent tools (Tool subclasses)
├── helpers/                      # Shared Python logic
├── prompts/                      # Prompt templates
├── agents/                       # Agent profiles (agents/<profile>/agent.yaml)
├── extensions/
│   ├── python/<point>/           # Backend lifecycle hooks
│   └── webui/<point>/            # UI HTML/JS contributions
└── webui/
    ├── config.html               # Optional: Plugin settings UI
    └── ...                       # Full plugin pages/components
```

### plugin.yaml (runtime manifest)

This is the manifest file that lives inside your plugin directory and drives runtime behavior. It is distinct from the index manifest used when publishing to the Plugin Index (see Section 7).

```yaml
title: My Plugin
description: What this plugin does.
version: 1.0.0
settings_sections:
  - agent
per_project_config: false
per_agent_config: false
# Optional: lock plugin permanently ON in UI/back-end
always_enabled: false
```

Field reference:
- `title`: UI display name
- `description`: Short plugin summary
- `version`: Plugin version string
- `settings_sections`: Which Settings tabs show a subsection for this plugin. Valid values: `agent`, `external`, `mcp`, `developer`, `backup`. Use `[]` for no subsection.
- `per_project_config`: Enables project-scoped settings and toggle rules
- `per_agent_config`: Enables agent-profile-scoped settings and toggle rules
- `always_enabled`: Forces ON and disables toggle controls in the UI (reserved for framework use)

### hooks.py (framework runtime hooks)

Plugins can include an optional `hooks.py` file at the plugin root. Agent Zero loads this module on demand and calls exported functions by name through `helpers.plugins.call_plugin_hook(...)`.

- `hooks.py` runs inside the **Agent Zero framework runtime and Python environment**, not the separate agent execution environment.
- Use it for framework-internal operations such as install-time setup, plugin registration work, filesystem preparation, cache updates, or other tasks that need access to Agent Zero internals.
- Hook functions may be synchronous or async. Async hooks are awaited by the framework.
- Hook modules are cached until plugin caches are cleared, so changes may require a plugin refresh/reload cycle.

Current example: the plugin installer calls `install()` from `hooks.py` after a plugin is copied into place.

### Runtime and dependency implications

- If `hooks.py` installs Python packages with `sys.executable -m pip`, those packages are installed into the **same Python environment that runs Agent Zero itself**.
- This is the correct place for Python dependencies that your plugin's backend code needs while running inside the framework runtime.
- It is **not** the right place for dependencies meant only for the separate agent execution runtime or for arbitrary system-level tooling.

If your plugin needs to install packages or binaries for the agent execution environment instead of the framework runtime, launch a subprocess that explicitly activates or targets that other environment first. In practice this means invoking the correct interpreter or shell for that environment rather than relying on the current process environment. For example:

- target a specific Python interpreter path for that runtime
- activate the desired virtualenv inside a subprocess shell command before running `pip`
- invoke the appropriate package manager from a subprocess prepared for that environment

In Docker deployments, this distinction is especially important:

- Framework runtime: `/opt/venv-a0`
- Agent execution runtime: `/opt/venv`

So a `hooks.py` install step affects `/opt/venv-a0` unless you intentionally switch to `/opt/venv` (or another target) inside your subprocess.

---

## 3. Frontend Extensions

### HTML Breakpoints
Core UI defines insertion points like <x-extension id="sidebar-quick-actions-main-start"></x-extension>.
To contribute:
1. Place HTML files in extensions/webui/<extension_point>/.
2. Include a root x-data scope.
3. Include an x-move-* directive (e.g., x-move-to-start, x-move-after="#id").

### JS Hooks
Place *.js files in extensions/webui/<extension_point>/ and export a default async function. They are called via callJsExtensions("<point>", context).

Core JS hooks can also expose runtime UI surfaces when static HTML breakpoints are not a fit. For example, `confirm_dialog_after_render` runs after the shared confirm dialog is built and receives the rendered dialog/body/footer nodes plus any caller-provided `extensionContext`.

### User Feedback: Notifications, Not Inline Errors
Plugin UI must use the **A0 notification system** for errors, success, and warnings. Do not render dedicated error/success boxes (e.g. a red block bound to `store.error`). Use the notification store so toasts and notification history stay consistent across the app.

- **Frontend (Alpine/store)**: Import `toastFrontendError`, `toastFrontendSuccess`, `toastFrontendWarning`, `toastFrontendInfo` from `/components/notifications/notification-store.js`, or call `$store.notificationStore.frontendError(message, title)` etc.
- **Backend (Python)**: Use `AgentNotification.error(...)`, `AgentNotification.success(...)` from `helpers.notification`.

See [Notifications](../developer/notifications.md) for the full API.

---

## 4. Plugin Settings

1. Add webui/config.html to your plugin.
2. The plugin settings wrapper instantiates a local modal context from $store.pluginSettingsPrototype.
3. Bind plugin fields to config.* and use context.* for modal-level state and actions.
4. Settings are scoped per-project and per-agent automatically.

### Resolution Priority (Highest First)
1. project/.a0proj/agents/<profile>/plugins/<name>/config.json
2. project/.a0proj/plugins/<name>/config.json
3. usr/agents/<profile>/plugins/<name>/config.json
4. usr/plugins/<name>/config.json
5. plugins/<name>/default_config.yaml (fallback defaults)

## 5. Model Providers

Plugins can add or override model providers by placing a `conf/model_providers.yaml` inside their plugin directory. The file follows the same format as the main `conf/model_providers.yaml`.

At startup (and whenever a plugin is enabled/disabled), the system:
1. Loads the base `conf/model_providers.yaml`.
2. Discovers `conf/model_providers.yaml` from all enabled plugins.
3. Merges them in order — matching provider IDs are overwritten, new IDs are appended.

Example plugin provider file (`usr/plugins/my_plugin/conf/model_providers.yaml`):
```yaml
chat:
  my_custom_provider:
    name: My Custom LLM
    litellm_provider: openai
    kwargs:
      api_base: https://my-llm.example.com/v1

embedding:
  my_custom_embed:
    name: My Embeddings
    litellm_provider: openai
    kwargs:
      api_base: https://my-embed.example.com/v1
```

---

## 6. Plugin Activation Model

- Global and scoped activation are independent, with no inheritance between scopes.
- Activation flags are files: `.toggle-1` (ON) and `.toggle-0` (OFF).
- UI states are `ON`, `OFF`, and `Advanced` (shown when any project/profile-specific override exists).
- `always_enabled: true` in `plugin.yaml` forces ON and disables toggle controls in the UI.
- The "Switch" modal is the canonical per-scope activation surface, and "Configure Plugin" keeps scope synchronized with the settings modal.

---

## 7. Routes

| Route | Purpose |
|---|---|
| GET /plugins/<name>/<path> | Serve static assets |
| POST /api/plugins/<name>/<handler> | Call plugin API |
| POST /api/plugins | Management (actions: get_config, save_config, list_configs, delete_config, toggle_plugin, get_doc) |

---

## 8. Plugin Index & Community Sharing

The **Plugin Index** is a community-maintained repository at https://github.com/agent0ai/a0-plugins that lists plugins available to the Agent Zero community. Plugins listed there can be discovered and installed by other users.

### Two Distinct plugin.yaml Files

There are two completely different `plugin.yaml` schemas used at different stages. They must not be confused:

**Runtime manifest** (inside your plugin repo/directory, drives Agent Zero behavior):
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

**Index manifest** (submitted to the `a0-plugins` repo under `plugins/<your-plugin-name>/`, drives discoverability only):
```yaml
title: My Plugin
description: What this plugin does.
github: https://github.com/yourname/your-plugin-repo
tags:
  - tools
  - example
```

The index manifest contains only four fields (`title`, `description`, `github`, `tags`) and must not include runtime fields. The `github` field must point to the root of a GitHub repository that itself contains a runtime `plugin.yaml` at the repository root.

### Repository Structure for Community Plugins

When creating a plugin intended for the community, the plugin should be a standalone GitHub repository where the plugin directory contents live at the repo root:

```text
your-plugin-repo/          ← GitHub repository root
├── plugin.yaml            ← runtime manifest (title, description, version, ...)
├── default_config.yaml
├── README.md
├── LICENSE
├── api/
├── tools/
├── extensions/
└── webui/
```

Users install it locally by cloning (or downloading) the repo contents into `/a0/usr/plugins/<plugin_name>/`.

### Submitting to the Plugin Index

1. Create a GitHub repository for your plugin with the runtime `plugin.yaml` at the repo root.
2. Fork `https://github.com/agent0ai/a0-plugins`.
3. Create a folder `plugins/<your-plugin-name>/` containing only an index `plugin.yaml` (and optionally a square thumbnail image ≤ 20 KB).
4. Open a Pull Request with exactly one new plugin folder.
5. CI validates the submission automatically. A maintainer reviews and merges.

Index submission rules:
- One plugin per PR
- Folder name must be unique, stable, lowercase, kebab-case
- Folders starting with `_` are reserved for internal use
- `github` must point to a public repo that contains `plugin.yaml` at its root
- `title` max 50 characters, `description` max 500 characters
- `tags`: optional, up to 5, use recommended tags from https://github.com/agent0ai/a0-plugins/blob/main/TAGS.md

### Plugin Marketplace (Coming Soon)

A built-in **Plugin Marketplace** plugin (always active) will allow users to browse the Plugin Index and install or update community plugins directly from the Agent Zero UI. This section will be updated once the marketplace plugin is released.

---

*Refer to AGENTS.md for the main framework guide.*
