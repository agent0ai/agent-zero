# Plugin Review Checklists

Reference material for `a0-review-plugin`. Read specific sections as needed during the review.

---

## Store Gating Pattern (required)

Every Alpine component that accesses a store MUST wrap content in a `x-if` gate:

```html
<!-- CORRECT -->
<div x-data>
  <template x-if="$store.myPluginStore">
    <div x-init="$store.myPluginStore.onOpen()" x-destroy="$store.myPluginStore.cleanup()">
      <!-- content -->
    </div>
  </template>
</div>

<!-- WRONG - will throw if store not yet initialized -->
<div x-data x-init="$store.myPluginStore.onOpen()">
  <!-- content -->
</div>
```

**Why**: Alpine stores are registered asynchronously. Without the gate, components referencing a store that hasn't loaded yet will throw undefined errors.

---

## Store Definition Pattern (required)

```javascript
// webui/my-store.js
import { createStore } from "/js/AlpineStore.js";

export const store = createStore("myPluginStore", {
    myData: null,
    init() {
        // called once globally on registration
    },
    onOpen() {
        // called when the component mounts
    },
    cleanup() {
        // called on x-destroy
    }
});
```

**Import in HTML `<head>`**:
```html
<script type="module" src="/plugins/my_plugin/webui/my-store.js"></script>
```

**Anti-patterns**:
- `document.addEventListener('alpine:init', ...)` in HTML - FORBIDDEN
- Defining store inline in HTML with `<script>` + `Alpine.store(...)` - FORBIDDEN

---

## Notification System (required)

Do NOT render inline error/success blocks. Use the A0 notification system:

```javascript
// Frontend (Alpine store or component)
import {
    toastFrontendError,
    toastFrontendSuccess,
    toastFrontendWarning,
    toastFrontendInfo
} from "/components/notifications/notification-store.js";

// Usage
toastFrontendError("Connection failed", "My Plugin");
toastFrontendSuccess("Saved successfully", "My Plugin");
```

```python
# Backend (Python)
from helpers.notification import AgentNotification

AgentNotification.error("Something went wrong", context_id=context.id)
AgentNotification.success("Operation complete", context_id=context.id)
```

**FAIL pattern** (do not allow):
```html
<!-- WRONG: inline error box -->
<div x-show="store.error" class="error-box" x-text="store.error"></div>
```

---

## API Handler Pattern

```python
# api/my_handler.py
from helpers.api import ApiHandler, Request, Response

class MyHandler(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        # input is the parsed request body
        # return a dict (auto-serialized to JSON) or a Response object
        return {"ok": True, "data": "result"}
```

Route is auto-registered as `POST /api/plugins/my_plugin/my_handler`.

---

## Tool Pattern

```python
# tools/my_tool.py
from helpers.tool import Tool, ToolResult

class MyTool(Tool):
    async def execute(self, arg1: str, arg2: str = "default"):
        # Tool logic
        return ToolResult("Result text")
```

---

## Python Extension Layout

Use one of these backend extension layouts:

```text
extensions/python/<extension_point>/
```

For named lifecycle hooks such as `agent_init`, `system_prompt`, `monologue_start`, or `tool_execute_before`.

```text
extensions/python/_functions/<module>/<qualname>/<start|end>/
```

For implicit `@extensible` hook targets. The path must keep the full module path and every nested `__qualname__` segment.

**FAIL pattern**:

```text
extensions/python/<module>_<qualname>_<start|end>/
```

That flattened form is stale and no longer matches the current extensible runtime lookup.

---

## AgentContext Access

```python
# Correct imports
from agent import AgentContext, AgentContextType

# Get context by ID
context = AgentContext.use(context_id)

# Send a message proactively
from helpers.messages import UserMessage
task = context.communicate(UserMessage("Message text"))
response = await task.result()
```

**Wrong** (do not use):
```python
from helpers.context import AgentContext  # WRONG - does not exist
```

---

## Plugin Settings (backend)

```python
from helpers.plugins import get_plugin_config, save_plugin_config

# Read settings (resolves project/profile scope from running agent)
settings = get_plugin_config("my_plugin", agent=agent) or {}

# Write settings to specific scope
save_plugin_config(
    "my_plugin",
    project_name="my-project",
    agent_profile="default",
    settings={"key": "value"},
)
```

---

## Plugin Settings UI (`webui/config.html`)

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
    <template x-if="$store.pluginSettingsPrototype">
      <div x-init="context = $store.pluginSettingsPrototype.init()">
        <input x-model="config.api_key" type="password" placeholder="API Key" />
        <input type="checkbox" x-model="config.feature_enabled" />
      </div>
    </template>
  </div>
</body>
</html>
```

---

## Sidebar Button (extension point)

```html
<!-- extensions/webui/sidebar-quick-actions-main-start/my-button.html -->
<div x-data x-move-after=".config-button#dashboard">
  <button class="config-button" @click="openModal('/plugins/my_plugin/webui/my-modal.html')">
    My Plugin
  </button>
</div>
```

---

## hooks.py Environment Targeting

```python
# hooks.py - install/pre_update hook example
import subprocess
import sys

def install():
    """Called by framework after plugin is placed in usr/plugins/."""
    # This installs into the Agent Zero FRAMEWORK runtime (/opt/venv-a0)
    subprocess.run([sys.executable, "-m", "pip", "install", "some-package==1.0.0"], check=True)

def pre_update():
    """Called by framework immediately before plugin update pulls new code into place."""
    # This installs into the Agent Zero FRAMEWORK runtime (/opt/venv-a0)
    subprocess.run([sys.executable, "-m", "pip", "install", "some-package==1.0.0"], check=True)

async def async_hook():
    """Async hooks are also supported."""
    pass
```

**To install into the AGENT execution runtime** (separate from framework):
```python
import subprocess

def install():
    # Explicitly target the agent runtime interpreter
    agent_python = "/opt/venv/bin/python"
    subprocess.run([agent_python, "-m", "pip", "install", "some-package"], check=True)
```

Never use `sys.executable` when you need the agent runtime - it targets the framework runtime.

---

## execute.py Pattern

```python
# execute.py - user-triggered script
import subprocess
import sys

def main():
    print("Running setup...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "requests==2.31.0"],
        text=True,
    )
    if result.returncode != 0:
        print("ERROR: Installation failed")
        return 1
    print("Done.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

Must: return `0` on success, non-zero on failure. Print progress. Be safe to rerun.

---

## plugin.yaml Schema Reference

```yaml
name: my_plugin              # required for community index (^[a-z0-9_]+$, must match dir name)
title: My Plugin             # required, UI display name
description: What it does.   # required
version: 1.0.0               # required
settings_sections:           # optional, valid: agent | external | mcp | developer | backup
  - agent
per_project_config: false    # optional, enables project-scoped settings
per_agent_config: false      # optional, enables agent-profile-scoped settings
always_enabled: false        # optional, framework use only
```

---

## Community Index: What CI Checks

When submitting to https://github.com/agent0ai/a0-plugins, CI validates:

**`index.yaml`** (in the index repo, NOT `plugin.yaml`):
- Fields: `title` (max 50), `description` (max 500), `github` (required), `tags` (optional, max 5), `screenshots` (optional, max 5 URLs)
- Max total file length: 2000 characters
- No unknown fields allowed

**Remote `plugin.yaml`** (your plugin's own repo):
- Must exist at repo root
- Must contain `name` field matching the index folder name exactly

**`LICENSE`** (your plugin's own repo):
- Must exist at repo root for Plugin Index / community listings (policy; same terms users expect from any open repo)

**Folder name**:
- Pattern: `^[a-z0-9_]+$` (underscores, no hyphens)
- Must not start with `_`
- Must be unique in the index
