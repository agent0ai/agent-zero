# Plugin Implementation

Sources: `/a0/plugins/AGENTS.md`, `/a0/helpers/plugins.py`, `/a0/helpers/api.py`, `/a0/helpers/tool.py`, and `/a0/agent.py`. Read the current contracts before implementation. UI patterns are in `webui.md`; publication is in `contribute.md`.

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

## Backend API & Context

### Import Paths
- Correct: `from agent import AgentContext, AgentContextType`
- Correct: `from initialize import initialize_agent`
- Correct for plugin-local Python modules under `usr/plugins/<name>/`: `from usr.plugins.<name>.helpers.module import ...`
- Avoid `sys.path` hacks for plugin-local imports
- Avoid symlink-dependent imports like `from plugins.<name>...` for user/community plugins in `usr/plugins/`

### Sending An Authorized Message In The Framework Process
```python
from agent import AgentContext
from agent import UserMessage

context = AgentContext.use(context_id)
if context is None:
    raise ValueError("Context not found")
task = context.communicate(UserMessage("Message text"))
response = await task.result()
```

### Reading Plugin Settings (backend)
```python
from helpers.plugins import get_plugin_config, save_plugin_config

# Runtime (with running agent - resolves project/profile from context)
settings = get_plugin_config("my_plugin", agent=agent) or {}

# Explicit write target (project/profile scope)
save_plugin_config(
    "my_plugin",
    project_name="my-project",
    agent_profile="default",
    settings=settings,
)
```

### Configuration Hook Caller Context

Use caller context only when the same settings need different behavior for a
known origin. An unlabeled call remains compatible and uses `"api"`; a
plugin-controlled runtime path can opt in explicitly:

```python
settings = get_plugin_config("my_plugin", agent=agent, caller="agent") or {}
```

Its `hooks.py` receives `hook_context={"caller": ...}`. For example, a plugin
can redact a stored credential for a UI-specific path while preserving its
normal runtime configuration:

```python
def get_plugin_config(default=None, hook_context=None, **kwargs):
    caller = (hook_context or {}).get("caller", "api")
    return redact_for_display(default) if caller == "ui" else default
```

The available values are `"ui"`, `"agent"`, and `"api"`. Existing hooks do
not need to change: the framework safely ignores this new argument for hooks
that do not accept it. This is behavior metadata, never authorization; do not
use it to grant or deny access to secrets or other protected data. A
`config.html` alone does not set the caller; its backend load/save path must
pass it explicitly.

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
        [sys.executable, "-m", "pip", "install", "<required-package>==<tested-version>"],
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
  - the plugin uninstaller calls `uninstall()` in `hooks.py` before deleting the plugin directory — use this to clean up any dependencies or state created by `install()`
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


## API And Tool Contracts

An API handler extends `helpers.api.ApiHandler`, keeps authentication/CSRF defaults, validates input, and returns a dict or Flask response. Its route is `/api/plugins/<name>/<handler>`. See `a0-development` references for HTTP examples; do not import live server contexts into a separate shell process to control the WebUI.

An agent tool extends `helpers.tool.Tool` and returns `helpers.tool.Response`:

```python
from helpers.tool import Tool, Response

class MyTool(Tool):
    async def execute(self, text: str = "", **kwargs) -> Response:
        return Response(message=text, break_loop=False)
```

Provide its callable contract in a policy-filtered `agent.system.tool.*.md` prompt. Do not advertise configurable tools in unconditional system fragments. Keep examples complete and valid JSON.

## Local Verification

Verify the named Docker runtime and source sync first. Use `/opt/venv-a0/bin/python` for framework imports and hooks, and `/opt/venv/bin/python` only for task-runtime code. Compile changed Python, run focused tests, then exercise the actual API/tool/UI path. Check effective configuration, plugin toggles, and cleanup. A successful import is not a live behavior test.

For local-only plugins, a GitHub repository and Index submission are unnecessary. Do not add dependencies, pages, tools, or hooks that the requested feature does not need.
