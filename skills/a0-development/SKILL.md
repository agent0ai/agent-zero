---
name: a0-development
description: Concise development guide for extending Agent Zero with tools, extensions, API endpoints, profiles, prompts, projects, and skills.
version: 1.1.0
author: Agent Zero Team
tags: ["development", "framework", "agent-zero", "tools", "extensions", "api", "agents", "prompts", "skills"]
trigger_patterns:
  - "extend agent zero"
  - "agent zero development"
  - "build agent zero feature"
  - "create agent zero tool"
  - "add extension"
  - "framework development"
  - "agent zero architecture"
  - "create agent zero extension"
  - "add api endpoint"
  - "create agent profile"
  - "agent zero internals"
  - "prompt system"
  - "agent profile"
---

# Agent Zero Development Guide

Use this skill when you need to understand the framework and add a new capability in the right place.

It covers:
- framework structure and extension points
- tools, extensions, API endpoints, and agent profiles
- prompt lookup and override rules
- projects and skills at a practical level

> **Path convention:** `/a0/` means the framework root. In Docker that is `/a0/`; in local development it is your repository root.

> [!IMPORTANT]
> **Plugins are the default extension mechanism.** If the task is "build or modify a plugin", load `a0-plugin-router`. This guide explains the framework primitives that plugins are built from.

Related skills: `a0-plugin-router` | `create-skill` | `a0-create-plugin` | `a0-review-plugin` | `a0-manage-plugin` | `a0-contribute-plugin` | `a0-debug-plugin`

---

## Golden Rules

- Prefer plugins for new features; they can bundle tools, prompts, extensions, API handlers, and UI pieces together.
- Create custom work under `/a0/usr/` so it survives framework updates.
- Every tool needs a matching prompt fragment named `agent.system.tool.<tool_name>.md`.
- Use `helpers.*` imports, not old or duplicated paths.
- Copy patterns from `/a0/agents/_example/` before inventing new ones.
- Follow the framework's async style for tools, API handlers, and most extensions.

---

## Framework Map

Most development work touches only these areas:

```text
/a0/
|- agent.py                    # Agent, AgentContext, AgentConfig
|- tools/                      # Core tools
|- extensions/
|  |- python/<hook_point>/     # Python lifecycle hooks
|  `- webui/<hook_point>/      # Browser-side hooks
|- api/                        # Flask API handlers
|- helpers/                    # Base classes and utility helpers
|- prompts/                    # Base prompt fragments
|- agents/                     # Built-in agent profiles
|- plugins/                    # Built-in plugins
`- usr/
   |- plugins/                 # User plugins
   |- agents/                  # User profiles
   |- skills/                  # User skills
   |- extensions/              # Standalone user extensions
   `- projects/                # User projects
```

### Core patterns

- **Plugin-first:** most real features belong in `/a0/usr/plugins/<name>/`.
- **Shared context:** `self.agent.context.data` stores conversation-scoped state shared across agents.
- **Composable prompts:** the system prompt is assembled from named fragments with includes and variables.
- **Ordered extensions:** `_10_*.py`, `_20_*.py`, `_30_*.py` run in filename order.
- **Profile inheritance:** profiles inherit from `default/` and override only the prompt fragments they need.

### Agent loop

At a high level, Agent Zero does this:

1. receive a user message
2. assemble the system prompt from fragments
3. call the model
4. parse tool calls from the response
5. execute tools and append results to history
6. repeat until the model emits `response` or a loop limit is reached

Extensions can observe or change behavior throughout that loop.

---

## Choose The Right Extension Point

| If you want to... | Use |
|---|---|
| Add a new agent capability | **Tool** |
| Hook into the lifecycle | **Extension** |
| Add server functionality for the Web UI | **API endpoint** |
| Add client-side UI behavior | **WebUI extension** |
| Create a specialized subordinate | **Agent profile** |
| Package instructions only | **Skill** |
| Bundle multiple pieces into one deliverable | **Plugin** |

---

## Recipes

Each recipe follows the same pattern: import, location, smallest working example, and the main gotcha.

### Tool

**Import**

```python
from helpers.tool import Tool, Response
```

**Usually lives in**

- `/a0/usr/plugins/<plugin>/tools/`
- occasionally `/a0/agents/<profile>/tools/` for profile-specific behavior

**Minimal example**

```python
from helpers.tool import Tool, Response

class MyTool(Tool):
    async def execute(self, **kwargs):
        value = kwargs.get("input", "")
        return Response(
            message=f"Processed: {value}",
            break_loop=False,
        )
```

**What matters**

- Read tool args from `kwargs`.
- Use `self.method` if the tool supports sub-methods like `my_tool:action`.
- Use `self.agent.context` for shared state.
- Return errors as a `Response` instead of crashing.
- Use `self.set_progress()` or `self.add_progress()` for long operations.

**Main gotcha**

Every tool also needs a prompt fragment so the model knows when and how to use it:

```text
agent.system.tool.<tool_name>.md
```

### Extension

**Import**

```python
from helpers.extension import Extension
```

**Usually lives in**

- `/a0/usr/plugins/<plugin>/extensions/python/<hook_point>/`
- `/a0/usr/extensions/python/<hook_point>/` for standalone experiments

**Naming rule**

```text
_NN_name.py
```

Where `_NN_` is a numeric prefix controlling execution order (e.g., `_10_`, `_20_`, `_50_`).
Use gaps like `_10_`, `_20_`, `_30_` so you can insert more later.

**Minimal example**

```python
from helpers.extension import Extension

class MyExtension(Extension):
    async def execute(self, **kwargs):
        if self.agent:
            self.agent.agent_name = "CustomAgent" + str(self.agent.number)
```

**Common hook points**

| Hook point | Typical use |
|---|---|
| `agent_init` | set defaults, load config |
| `system_prompt` | inject prompt content |
| `before_main_llm_call` | add or adjust prompt data |
| `tool_execute_before` | validate or guard tool calls |
| `tool_execute_after` | post-process results |
| `message_loop_end` | cleanup after a loop |
| `startup_migration` | startup migration logic |
| `webui_ws_event` | handle custom WebSocket events |

Inspect existing extension directories if you need a less common hook.

**Implicit extension points**

Functions decorated with `@extensible` also expose start/end hooks under:

```text
_functions/<module_path>/<qualname_path>/start
_functions/<module_path>/<qualname_path>/end
```

Example:

```text
_functions/agent/Agent/handle_exception/start
```

Those hooks receive a mutable `data` dict with `args`, `kwargs`, `result`, and `exception`.

**Main gotcha**

`self.agent` can be `None` for early startup hooks like `startup_migration` and `banners`, so guard against that.

### API Endpoint

**Import**

```python
from helpers.api import ApiHandler
from flask import Request, Response
```

**Usually lives in**

- `/a0/usr/plugins/<plugin>/api/`

**Minimal example**

```python
from helpers.api import ApiHandler
from flask import Request

class MyEndpoint(ApiHandler):
    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET", "POST"]

    async def process(self, input: dict, request: Request) -> dict:
        context = self.use_context(input.get("context", ""))
        return {"context": context.id, "result": input.get("param", "default")}
```

**What matters**

- The filename becomes the route: `my_endpoint.py` -> `/api/my_endpoint`.
- Override class methods like `requires_auth()`, `requires_api_key()`, or `requires_loopback()` when needed.
- Use `use_context()` when the endpoint should join an existing conversation context.

**Main gotcha**

If you add UI-facing behavior, you often need both an API endpoint and a matching WebUI extension.

### Agent Profile

**Usually lives in**

- `/a0/usr/agents/<profile-name>/`

**Minimum structure**

```text
agents/<profile-name>/
|- agent.yaml
`- prompts/
   `- agent.system.main.role.md
```

**`agent.yaml`**

```yaml
title: Data Analyst
description: Agent specialized in data analysis and visualization.
context: Use this agent for data analysis, plotting, and statistical work.
```

**Role override**

```markdown
## Your role
You are a specialized data analysis agent.

## Process
1. Understand the data and question.
2. Choose the right tools.
3. Run the analysis.
4. Summarize the findings clearly.
```

**What matters**

- Profiles inherit from `default/`.
- Override prompt files by reusing the same filename as the base prompt.
- The most common override is `agent.system.main.role.md`.

**Main gotcha**

`agent.yaml` is intentionally small. Profile-specific model and other runtime overrides belong in `settings.json` next to the profile, not in `agent.yaml`.

### Prompt System

Prompts are named fragments that the framework assembles into a final system prompt.

**Common names**

```text
agent.system.main.md
agent.system.main.role.md
agent.system.main.communication.md
agent.system.tool.<name>.md
agent.system.tools.md
agent.system.skills.md
fw.*.md
```

**Lookup order**

| Location | Purpose |
|---|---|
| `/a0/agents/<profile>/prompts/` | built-in profile overrides |
| `/a0/usr/agents/<profile>/prompts/` | user profile overrides |
| `/a0/plugins/<plugin>/prompts/` | built-in plugin prompts |
| `/a0/usr/plugins/<plugin>/prompts/` | user plugin prompts |
| `/a0/prompts/` | base prompts |

The first matching file wins.

**Useful directives**

| Directive | Meaning |
|---|---|
| `{{include "agent.system.main.role.md"}}` | include another fragment |
| `{{include original}}` | include the next lower-priority version |
| `{{variable_name}}` | substitute a variable at render time |

**Read prompts in code**

```python
content = self.read_prompt("fw.some_message.md", variable1="value1")
```

```python
from helpers.files import read_prompt_file

content = read_prompt_file("template.md", _directories=[...], var="value")
```

**Main gotcha**

Use `{{include original}}` when you want to extend a base prompt rather than fully replace it.

### Skill

Skills are instruction bundles loaded by `skills_tool`. A skill is just a directory with a `SKILL.md`.

**Usually lives in**

- `/a0/skills/`
- `/a0/usr/skills/`

**Tool calls**

```json
{"tool_name": "skills_tool:list", "tool_args": {}}
{"tool_name": "skills_tool:load", "tool_args": {"skill_name": "my-skill"}}
```

**Main gotcha**

If you need the full skill-authoring workflow, stop here and load `create-skill`.

### Project

Projects provide isolated working directories and project-specific instructions.

**Usually lives in**

- `/a0/usr/projects/<project-name>/`

**Important files**

```text
.a0proj/project.json
.a0proj/agents.json
.a0proj/variables.env
.a0proj/secrets.env
.a0proj/memory/
```

**What matters in `project.json`**

- `title`, `description`: display metadata
- `instructions`: markdown injected into the active system prompt
- `git_url`: optional repository URL
- `memory`: shared vs project-specific memory mode
- `file_structure`: controls the working-directory tree shown to the agent

**Main gotcha**

Projects are typically created and managed through the Web UI; the `.a0proj/` directory is usually generated for you.

---

## Minimal Reference

### Common helper patterns

**Shared context**

```python
context = self.agent.context
context.data["my_key"] = my_value
value = context.data.get("my_key", default)
```

**File helpers**

```python
from helpers import files

content = files.read_file("path/to/file")
files.write_file("path/to/file", content)
exists = files.exists("path/to/file")
```

**Console output**

```python
from helpers.print_style import PrintStyle

PrintStyle.hint("Informational message")
PrintStyle.warning("Warning message")
PrintStyle.error("Error message")
```

**Error handling in tools**

```python
from helpers.tool import Response
from helpers.print_style import PrintStyle

try:
    result = await risky_operation()
except Exception as e:
    PrintStyle.error(f"Operation failed: {e}")
    return Response(message=f"Error: {e}", break_loop=False)
```

### Most useful files

| File | Why it matters |
|---|---|
| `/a0/agent.py` | core agent and context objects |
| `/a0/helpers/tool.py` | `Tool` and `Response` base classes |
| `/a0/helpers/extension.py` | `Extension` base class and `@extensible` |
| `/a0/helpers/api.py` | `ApiHandler` base class |
| `/a0/helpers/files.py` | prompt and file helpers |
| `/a0/agents/_example/` | best reference implementation to copy from |

### Practical workflow

1. Choose the right extension point.
2. Build it under `/a0/usr/`, usually inside a plugin.
3. Copy patterns from `/a0/agents/_example/` or an existing plugin.
4. Test with minimal input first.
5. Run `python run_ui.py` locally or restart the container if using Docker.

For plugin contribution details, see `/a0/docs/contribution.md`.
