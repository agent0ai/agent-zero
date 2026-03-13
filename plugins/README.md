# Agent Zero - Core Plugins

This directory contains the system-level plugins bundled with Agent Zero.

## Directory Structure

- `plugins/`: Core system plugins. Reserved for framework updates — do not place custom plugins here.
- `usr/plugins/`: The correct location for all user-developed and custom plugins. This directory is gitignored.

## Documentation

For detailed guides on how to create, extend, or configure plugins, refer to:

- [`docs/agents/AGENTS.plugins.md`](../docs/agents/AGENTS.plugins.md): Full-stack plugin architecture, manifest format, extension points, and Plugin Index submission.
- [`docs/developer/plugins.md`](../docs/developer/plugins.md): Human-facing developer guide covering the full plugin lifecycle.
- [`AGENTS.md`](../AGENTS.md): Main framework guide and backend context.
- [`skills/a0-create-plugin/SKILL.md`](../skills/a0-create-plugin/SKILL.md): Agent-facing authoring workflow (local and community plugins).

## What a Plugin Can Provide

Plugins are automatically discovered based on the presence of a `plugin.yaml` file. Each plugin can contribute:

- **Backend**: API handlers, tools, helpers, and lifecycle extensions
- **Frontend**: HTML/JS UI contributions via core extension breakpoints
- **Settings**: Isolated configuration scoped per-project and per-agent profile
- **Activation**: Global and scoped ON/OFF rules via `.toggle-1` and `.toggle-0` files, including advanced per-scope switching in the WebUI
- **Agent profiles**: Plugin-distributed subagent definitions under `agents/<profile>/agent.yaml`

## Plugin Manifest

Every plugin requires a `plugin.yaml` at its root:

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

## Plugin Initialization (`initialize.py`)

Plugins can include an optional `initialize.py` at the plugin root for one-time setup such as installing dependencies or downloading models. Users trigger it via the **Init** button in the Plugin List UI. The script should return `0` on success and print progress messages for user feedback.

## Runtime Hooks (`hooks.py`)

Plugins can also include an optional `hooks.py` at the plugin root. The framework loads it on demand and can call exported hook functions by name through `helpers.plugins.call_plugin_hook(...)`.

- `hooks.py` runs inside the **Agent Zero framework runtime and Python environment**.
- Use it for framework-internal work such as install hooks, cache preparation, registration, or filesystem setup.
- If it runs `sys.executable -m pip install ...`, packages are installed into the same Python environment that runs Agent Zero.
- If you need to install into the separate agent runtime or into the system environment, explicitly target that environment from a subprocess by selecting the correct interpreter, virtualenv, or package manager.

In Docker, `hooks.py` normally affects `/opt/venv-a0`; the agent execution runtime is `/opt/venv`.

## Plugin Index & Community Sharing

The **Plugin Index** at https://github.com/agent0ai/a0-plugins is the community-maintained registry of plugins available to all Agent Zero users.

To share a plugin with the community:

1. Create a standalone GitHub repository with the plugin contents at the repo root and the runtime `plugin.yaml` there.
2. Fork `https://github.com/agent0ai/a0-plugins` and add a folder `plugins/<your-plugin-name>/` containing a separate index `plugin.yaml`:

```yaml
title: My Plugin
description: What this plugin does.
github: https://github.com/yourname/your-plugin-repo
tags:
  - tools
```

3. Open a Pull Request. CI validates the submission; a maintainer reviews and merges.

Note: The index `plugin.yaml` is a **different schema** from the runtime manifest — it contains only `title`, `description`, `github`, and optional `tags`. Do not mix them up.

## Plugin Marketplace (Coming Soon)

A built-in **Plugin Marketplace** (always-active plugin) is planned and will allow users to browse the Plugin Index and install community plugins directly from the Agent Zero UI.
