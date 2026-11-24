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

`a0_version` optionally declares supported **Agent Zero** versions, separately from the plugin's own `version`. Use quoted values: `"3.0"` (exact), `">=3.0,<4.0"` (AND comparisons), `"3.0 - 3.5"` (inclusive range), `"3.*"` (wildcard), or `["2.15", ">=3.0,<4.0"]` (OR alternatives). Omission or `"*"` leaves versions unrestricted. Declare tested versions, not a guessed compatibility promise. See the [full specification](../../../docs/developer/plugins.md#agent-zero-version-requirements) for comparison semantics and fork handling. The Hub reads the repository's default-branch `plugin.yaml` directly, displays the requirement and current A0 version, and warns before incompatible installs while allowing the user to continue. Do not duplicate it in `index.yaml`.

`settings_sections` controls which Settings tabs show a subsection for this plugin. Valid values: `agent`, `external`, `mcp`, `developer`, `backup`. Use `[]` for no subsection.

Activation defaults to ON when no toggle rule exists. Set `per_project_config` and/or `per_agent_config` to enable advanced per-scope switching. Core system plugins may also use `always_enabled: true` to lock the plugin permanently ON (reserved for framework use).

---

## Backend API & Context

For a messaging integration that should expose Agent Zero slash commands, read [Channel Commands](channel-commands.md). It covers the shared catalog/resolver, effects, context binding, and transport-specific menus; forwarding slash text alone does not provide full command compatibility.

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
  hooks.py              # Required when setup/dependencies/initialization/cleanup are needed
  execute.py            # Optional non-lifecycle manual action only; omit by default
  default_config.yaml   # Optional default settings fallback
  README.md             # Optional locally; strongly recommended for community plugins
  LICENSE               # Optional locally (shown in Plugin List UI when present); required at repo root for Plugin Index submission
  agents/
    <profile>/agent.yaml # Optional plugin-distributed agent profile
  api/                  # API Handlers (ApiHandler base class)
  skills/<skill-name>/SKILL.md # On-demand workflow and optional callable declaration
  tools/                # Standalone agent tools
  helpers/              # Shared Python logic and skill callable handlers
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

## Required Lifecycle Hooks (`hooks.py`)

**All plugin setup, dependency installation, required initialization, and uninstall cleanup MUST remain owned by functions in the plugin-root `hooks.py`; guest provisioning may delegate to automatic worker setup. These operations MUST NOT live in `execute.py`, including when described as manual setup, post-install, repair, or maintenance.** Installation through the Plugins UI/API must leave an automatic path to readiness without an Execute button or an extra setup command.

The framework calls exported functions through `helpers.plugins.call_plugin_hook(...)`:

| Hook | When it runs | Responsibility |
|---|---|---|
| `install()` | After Git/ZIP installation and again after a successful code update | Prepare required installation/update state, migrations, registrations and initialization; guest packages/assets may provision automatically on first use or enablement. Safe to rerun without duplicating resources or overwriting user data. |
| `pre_update()` | Immediately before updating plugin code | Stop plugin-owned processes or prepare state when required. |
| `uninstall()` | Before the framework deletes the custom plugin directory | Stop owned processes, unregister integrations, and remove plugin-owned dependencies and resources. |

Hooks run inside the **global Docker Python environment** and may be sync or async. Their execution location does not determine where dependencies belong. Keep lifecycle entrypoints in `hooks.py`; delegate guest provisioning to existing automatic worker setup and plugin-local helpers. The [Document Query hooks](../../../plugins/_document_query/hooks.py) and [sandbox adapter](../../../plugins/_document_query/helpers/sandbox.py) show lazy guest setup and owned stop/delete behavior; use the [sandbox guide](../../../docs/developer/plugin-sandboxes.md#choosing-dependency-location) for current interfaces and custom-plugin path limits.

Use plugin-owned dependency directories where possible so cleanup is precise. Reuse compatible shared dependencies; never uninstall shared packages or services needed by Agent Zero or another plugin. Remove owned services, symlinks, registrations, and generated resources too; directory deletion alone does not undo external side effects. Preserve unrelated data and document any plugin-owned user data that uninstall deletes.

Check subprocess results and raise on setup failure rather than reporting success. Clean up partial initialization so install/update and guest setup can be retried; record setup success only after it completes. Guest packages and models may provision on first actual use and persist across stops. Features needed early and configured inbound listeners must prepare at enablement/startup before receiving work, while respecting disabled state; do not delay a receiver until a message it cannot receive. Startup extensions may call the same helper or hook without replacing install/uninstall ownership. Disable stops owned workers; uninstall removes their owned resources.

### Manual Actions (`execute.py`)

Omit `execute.py` by default. It is only for a separate, explicitly requested manual action unrelated to the plugin lifecycle, such as exporting a diagnostic report. Never use it to install/uninstall dependencies, perform required setup or initialization, apply required update migrations, or remove the plugin. Renaming lifecycle work as maintenance does not change this rule.

### Environment targeting rules

- Prefer existing sandbox/worker facilities for plugin-owned Python/Node/native packages, inference, browser/document/media workers and external integration clients. Keep lightweight tools, hooks, configuration and authenticated API/UI adapters in the framework; call the guest without importing its libraries there.
- Reuse guest-owned manifests/installers and persistent environments. Execute pip/npm/apt inside the guest through the existing manager/worker; choosing a host subprocess or virtualenv alone does not enter a sandbox.
- Add a main-environment dependency only for functionality that must execute there, with a concrete explanation in the plugin README and the smallest dependency set. `sys.executable -m pip install ...` in a hook targets Agent Zero's Python (`/usr/local/bin/python` in Docker); it is not a guest installer.
- Check that optional guest dependencies stay out of main requirements and no feature import/general boot path eagerly installs them. Intentional readiness for enabled early-needed features/listeners is separate. Lazy provisioning reduces the shipped/default footprint but may not reduce total disk after feature use.

---


## Agent-Facing Capabilities

Start with a plugin skill for an agent workflow. Put it in `skills/<skill-name>/SKILL.md` and use `build-skill` for authoring. The agent can discover the workflow and load its instructions when needed, which keeps detailed procedures out of unrelated chats.

Have the skill use an existing authorized tool, CLI, or API when it already provides the operation. If the workflow needs its own callable for chat-scoped state, framework artifacts, or a permission boundary, declare it in the skill.

1. In `SKILL.md`, set `metadata.tool.name` to the callable name and `metadata.tool.parameters` to its JSON Schema object. Put text-mode call examples in the skill body. Responses uses the declared schema.
2. In an `extensions/python/skill_tools/` extension, set `bindings[callable_name] = SkillTool(plugin_name, skill_name, factory)` from `execute(self, bindings, **kwargs)`. The factory creates the plugin's `Tool` handler from `helpers/`. The callable becomes available after the chat loads the skill, subject to normal scoped skill overrides, visibility, and Tool Access.
3. When migrating, remove `tools/<callable>.py`, any discovery shim, and its old agent tool prompt or duplicate schema. File-based tool lookup takes precedence over the skill binding. Preserve saved Tool Access denials and destination authorization at execution.

Follow the shipped [Browser](../../../plugins/_browser/extensions/python/skill_tools/_10_browser.py) and [Document Query](../../../plugins/_document_query/extensions/python/skill_tools/_10_document_query.py) registrations.

## API And Tool Contracts

An API handler extends `helpers.api.ApiHandler`, keeps authentication/CSRF defaults, validates input, and returns a dict or Flask response. Its route is `/api/plugins/<name>/<handler>`. See `a0-development` references for HTTP examples; do not import live server contexts into a separate shell process to control the WebUI.

An agent tool extends `helpers.tool.Tool` and returns `helpers.tool.Response`:

```python
from helpers.tool import Tool, Response

class MyTool(Tool):
    async def execute(self, text: str = "", **kwargs) -> Response:
        return Response(message=text, break_loop=False)
```

For a standalone tool, provide its callable contract in a policy-filtered `agent.system.tool.*.md` prompt. For an on-demand callable, put the contract in the skill as described above. Keep examples complete and valid JSON.

## Local Verification

Verify the named Docker runtime and source sync first. Use `/usr/local/bin/python` directly for framework imports and hooks; use the local execution destination when modifying Agent Zero. Compile changed Python, run focused tests, then exercise the actual API/tool/UI path. For lifecycle changes, exercise normal install, repeated install/update, and uninstall through management APIs using isolated test data; confirm readiness without Execute and removal of owned dependencies without touching shared ones. Check effective configuration, plugin toggles, and cleanup. A successful import is not a live behavior test.

For local-only plugins, a GitHub repository and Index submission are unnecessary. Do not add dependencies, pages, tools, or hooks that the requested feature does not need.
