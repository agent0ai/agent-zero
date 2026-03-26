---
name: a0-create-plugin
description: Create, extend, or modify Agent Zero plugins. Follows strict full-stack conventions (usr/plugins, plugin.yaml, Store Gating, AgentContext, plugin settings). Use for UI hooks, API handlers, lifecycle extensions, or plugin settings UI.
version: 1.0.0
tags: ["plugins", "create", "build", "develop", "extend"]
trigger_patterns:
  - "create plugin"
  - "build plugin"
  - "new plugin"
  - "develop plugin"
  - "write plugin"
  - "plugin template"
---

# Agent Zero Plugin Development

> [!IMPORTANT]
> Always create new plugins in `/a0/usr/plugins/<plugin_name>/`. The `/a0/plugins/` directory is reserved for core system plugins.

Related skills: `/a0/skills/a0-review-plugin/SKILL.md` | `/a0/skills/a0-contribute-plugin/SKILL.md` | `/a0/skills/a0-manage-plugin/SKILL.md`

Primary references:
- /a0/AGENTS.md (Full-stack architecture & AgentContext)
- /a0/docs/agents/AGENTS.components.md (Component system deep dive)
- /a0/docs/agents/AGENTS.modals.md (Modal system & CSS conventions)
- /a0/docs/agents/AGENTS.plugins.md (Extension points, plugin.yaml, settings system, Plugin Index)
- /a0/docs/developer/plugins.md (Developer lifecycle and publishing)

---

## Step 0: Ask First — Local or Community Plugin?

Before starting, ask the user one question:

> "Should this plugin be **local only** (stays in your Agent Zero installation) or a **community plugin** (published to the Plugin Index so others can install it)?"

- **Local plugin**: Create it in `/a0/usr/plugins/<plugin_name>/`. No repository needed. Skip to the manifest section below.
- **Community plugin**: The plugin must live in its own GitHub repository (runtime manifest at the repo root), and then a separate index submission PR is made to https://github.com/agent0ai/a0-plugins. Guide the user through both steps.

---

## Plugin Manifest (plugin.yaml)

Every plugin must have a `plugin.yaml` or it will not be discovered.

```yaml
name: my_plugin              # required for community plugins; must match dir name (^[a-z0-9_]+$)
title: My Plugin
description: What this plugin does.
version: 1.0.0
settings_sections:
  - agent
per_project_config: false
per_agent_config: false
```

`name`: lowercase, numbers, underscores only (`^[a-z0-9_]+$`). Required by CI when submitting to the Plugin Index - must exactly match the index folder name.

`settings_sections` controls which Settings tabs show a subsection for this plugin. Valid values: `agent`, `external`, `mcp`, `developer`, `backup`. Use `[]` for no subsection.

Activation defaults to ON when no toggle rule exists. Set `per_project_config` and/or `per_agent_config` to enable advanced per-scope switching. Core system plugins may also use `always_enabled: true` to lock the plugin permanently ON (reserved for framework use).

---

## Mandatory Frontend Patterns

### 1. The "Store Gate" Template
To avoid race conditions and undefined errors, every component must use this wrapper:
```html
<div x-data>
  <template x-if="$store.myPluginStore">
    <div x-init="$store.myPluginStore.onOpen()" x-destroy="$store.myPluginStore.cleanup()">
       <!-- Content goes here -->
    </div>
  </template>
</div>
```

### 2. Separate Store Module
Place store logic in a separate .js file. Do NOT use alpine:init listeners inside HTML.
```javascript
// webui/my-store.js
import { createStore } from "/js/AlpineStore.js";
export const store = createStore("myPluginStore", {
    status: 'idle',
    init() { ... },
    onOpen() { ... },
    cleanup() { ... }
});
```
Import it in the HTML <head>:
```html
<head>
  <script type="module" src="/plugins/<plugin_name>/webui/my-store.js"></script>
</head>
```

### 3. User Feedback: A0 Notifications Only
Do **not** show errors or success via inline boxes (e.g. a red `<div>` bound to `store.error`). Use the project notification system so toasts and history stay consistent.

- **Errors**: `toastFrontendError(message, "My Plugin")` (or `$store.notificationStore.frontendError(...)`)
- **Success**: `toastFrontendSuccess(message, "My Plugin")`
- **Warnings/Info**: `toastFrontendWarning`, `toastFrontendInfo` from `/components/notifications/notification-store.js`

Import and call from your store; do not render a dedicated error/success block in the template. See [Notifications](/a0/docs/developer/notifications.md) for the full API.

---

## Plugin Settings

If your plugin needs user-configurable settings, add `webui/config.html`. The system detects it automatically and shows a Settings button in the relevant tabs (per `settings_sections` in `plugin.yaml`).

### Settings modal contract

The modal provides Project + Agent profile context selectors. The plugin settings wrapper instantiates a local modal context from `$store.pluginSettingsPrototype`. Inside `config.html`, bind plugin fields to `config.*` and use `context.*` for modal-level state and actions:

```html
<html>
<head>
  <title>My Plugin Settings</title>
  <script type="module">
    import { store } from "/components/plugins/plugin-settings-store.js";
  </script>
</head>
<body>
  <div x-data>
    <input x-model="config.my_key" />
    <input type="checkbox" x-model="config.feature_enabled" />
  </div>
</body>
</html>
```

The modal's Save button persists `config` to `config.json` in the correct scope (project/agent/global).

### Sidebar Button (sidebar entry point)
- Extension point: `sidebar-quick-actions-main-start`
- Class: `class="config-button"`
- Placement: `x-move-after=".config-button#dashboard"`
- Action: `@click="openModal('/plugins/<plugin_name>/webui/my-modal.html')"`

---

## Backend API & Context

### Import Paths
- Correct: `from agent import AgentContext, AgentContextType`
- Correct: `from initialize import initialize_agent`
- Correct for plugin-local Python modules under `usr/plugins/<name>/`: `from usr.plugins.<name>.helpers.module import ...`
- Avoid `sys.path` hacks for plugin-local imports
- Avoid symlink-dependent imports like `from plugins.<name>...` for user/community plugins in `usr/plugins/`

### Sending Messages Proactively
```python
from agent import AgentContext
from helpers.messages import UserMessage

context = AgentContext.use(context_id)
task = context.communicate(UserMessage("Message text"))
response = await task.result()
```

### Reading Plugin Settings (backend)
```python
from helpers.plugins import get_plugin_config, save_plugin_config

# Runtime (with running agent - resolves project/profile from context)
settings = get_plugin_config("my-plugin", agent=agent) or {}

# Explicit write target (project/profile scope)
save_plugin_config(
    "my-plugin",
    project_name="my-project",
    agent_profile="default",
    settings=settings,
)
```

---

## Directory Layout
```
/a0/usr/plugins/<name>/
  plugin.yaml           # Required manifest
  execute.py            # Optional user-triggered setup, post-install, or maintenance script
  hooks.py              # Optional framework runtime hook functions
  default_config.yaml   # Optional default settings fallback
  README.md             # Optional locally; strongly recommended for community plugins
  LICENSE               # Optional locally (shown in Plugin List UI when present); required at repo root for Plugin Index submission
  agents/
    <profile>/agent.yaml # Optional plugin-distributed agent profile
  api/                  # API Handlers (ApiHandler base class)
  tools/                # Tool subclasses
  helpers/              # Shared Python logic
  prompts/              # Prompt templates
  conf/
    model_providers.yaml # Optional: add or override model providers
  extensions/
    python/<extension_point>/  # Named Python lifecycle extensions
    python/_functions/<module>/<qualname>/<start|end>/  # Implicit @extensible hooks
    webui/<point>/      # HTML/JS hook extensions
  webui/
    config.html         # Optional: plugin settings UI
    my-modal.html       # Full plugin pages
    my-store.js         # Alpine stores
```

Do not create the retired flattened extensible path form `extensions/python/<module>_<qualname>_<start|end>/`. The current runtime only resolves the deep `_functions/<module>/<qualname>/<start|end>` layout for implicit `@extensible` hooks.

### Import rule for plugin-local Python code

Use the fully qualified `usr.plugins.<plugin_name>...` path for plugin-local
imports. This lets plugins keep a normal `helpers/` directory without renaming
it to `<name>_helpers`, and it avoids both `sys.path` mutation and symlink
installation steps.

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

## Plugin Execution Script (`execute.py`)
If your plugin needs a user-triggered script for setup, post-install work, maintenance, or other manual operations, add an `execute.py` at the plugin root.

Good uses for `execute.py` include:
- installing dependencies or downloading models/assets
- running post-install steps after the plugin is copied into place
- rebuilding caches, indexes, or generated files
- applying migrations, repair steps, or sync jobs that the user may need to run again later
- performing periodic maintenance tasks that should happen only when explicitly requested by the user

Use `execute.py` for **user-initiated** work. If the behavior is framework-internal or should happen automatically as part of plugin lifecycle handling, use `hooks.py` or lifecycle extensions instead.

First rule of plugin side effects: do not modify the system permanently in ways
that outlive the plugin. When a plugin is deleted, there should be no leftover
symlinks, unmanaged services, or stray files outside plugin-owned paths unless
the user explicitly requested that behavior and the plugin documents how to
clean it up.

```python
import subprocess
import sys

def main():
    print("Installing plugin dependencies...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "requests==2.31.0"],
        text=True,
    )
    if result.returncode != 0:
        print("ERROR: Installation failed")
        return result.returncode

    print("Refreshing plugin resources...")
    # Add post-install, repair, migration, or maintenance logic here.

    print("Done.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

Users trigger it from the Plugins UI. Treat it as a manual, rerunnable operation: return `0` on success, non-zero on failure, and print progress so the user can understand what happened. When possible, make it safe to run more than once; if reruns are not safe, detect the state and print a clear message.

## Runtime Hooks (`hooks.py`)
If your plugin needs framework-internal hook points, add a `hooks.py` file at the plugin root. The framework can call exported functions by name via `helpers.plugins.call_plugin_hook(...)`.

- `hooks.py` runs inside the **Agent Zero framework runtime**, not the separate agent execution environment.
- Use it for things like install hooks, pre-update hooks, plugin registration work, cache setup, file preparation, or other internal framework operations.
- Current built-in usage:
  - the plugin installer calls `install()` in `hooks.py` after placing a plugin in `usr/plugins/`
  - the plugin updater calls `pre_update()` in `hooks.py` immediately before pulling new plugin code into place
- Hook functions may be sync or async.
- Hooks should be reversible and cleanup-safe. Prefer framework-managed state and plugin-owned paths over permanent system modifications.

### Environment targeting rules
- If `hooks.py` runs `sys.executable -m pip install ...`, it installs into the same Python environment that is running Agent Zero.
- That is correct for dependencies needed by the plugin inside the framework runtime.
- If the dependency is meant for the separate agent runtime or for OS-level tools, do **not** assume the current environment is correct.

Instead, explicitly switch targets in a subprocess:
- invoke the exact Python interpreter for the target runtime
- activate the target virtualenv in the subprocess before running `pip`
- run the relevant OS package manager from a subprocess configured for the intended environment

In Docker, this usually means `hooks.py` affects `/opt/venv-a0` unless you intentionally target `/opt/venv` or another environment.

---

## Community Plugin: GitHub Repo + Plugin Index Submission

If the user chose a **community plugin**, follow these additional steps after building and testing the plugin locally.

### 1. Repository Structure

The plugin must live in its own GitHub repository with the plugin contents at the **repository root** (not inside a subfolder):

```text
your-plugin-repo/          ← GitHub repository root
├── plugin.yaml            ← runtime manifest (must include name field!)
├── default_config.yaml
├── README.md
├── LICENSE                ← required at repo root before Plugin Index submission
├── api/
├── tools/
├── extensions/
└── webui/
```

The runtime `plugin.yaml` at the repo root **must include a `name` field** matching the index folder name:

```yaml
name: my_plugin            # REQUIRED - must match index folder name exactly
title: My Plugin
description: What this plugin does.
version: 1.0.0
```

Help the user create this repository and push the plugin files to it.

### 2. Index manifest (different from runtime manifest)

The Plugin Index (`https://github.com/agent0ai/a0-plugins`) uses a **separate `index.yaml`** file that only describes discoverability — it is NOT the same as the runtime `plugin.yaml` and has a different schema:

```yaml
title: My Plugin
description: What this plugin does.
github: https://github.com/yourname/your-plugin-repo
tags:
  - tools
  - example
screenshots:                # optional, up to 5 full image URLs
  - https://raw.githubusercontent.com/yourname/your-plugin-repo/main/docs/screen1.png
```

Required fields: `title`, `description`, `github`. Optional: `tags` (up to 5), `screenshots` (up to 5 URLs).
See the recommended tag list at https://github.com/agent0ai/a0-plugins/blob/main/TAGS.md.

> Important: CI also checks that your remote `plugin.yaml` contains a `name` field matching the index folder name exactly.

### 3. Submission steps

1. Fork `https://github.com/agent0ai/a0-plugins`.
2. Create the folder `plugins/<your_plugin_name>/` in the fork.
   - Folder name: lowercase letters, numbers, underscores only (`^[a-z0-9_]+$`) - no hyphens
   - Must exactly match the `name` field in your remote `plugin.yaml`
3. Add `index.yaml` inside it (and optionally a square thumbnail ≤ 20 KB named `thumbnail.png`, `thumbnail.jpg`, or `thumbnail.webp`).
4. Open a Pull Request. The PR must add exactly one new plugin folder.
5. CI validates automatically. A maintainer reviews and merges.

Submission constraints:
- Folder name: unique, stable, `^[a-z0-9_]+$`
- Folders starting with `_` are reserved for internal use
- `title` max 50 characters, `description` max 500 characters
- `index.yaml` max 2000 characters total

For a fully guided contribution flow (including git operations), read `/a0/skills/a0-contribute-plugin/SKILL.md`.

---

## Plugin Index & Plugin Hub

The **Plugin Index** is the community hub at https://github.com/agent0ai/a0-plugins.

Agent Zero now exposes indexed plugins through the built-in **Plugin Hub**. Users can open it from the **Plugins** dialog either through the **Browse** tab or through the **Install** button, then inspect plugin details and install directly from the UI.
