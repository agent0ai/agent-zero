---
name: a0-development
description: Development guide for extending and building features for the Agent Zero AI framework. Covers architecture, tools, extensions, API endpoints, agent profiles, projects, prompts, and skills — with correct paths, imports, and patterns matching the current codebase.
version: 1.0.0
author: Agent Zero Team
tags: ["development", "framework", "agent-zero", "extending", "tools", "extensions", "skills", "api", "agents", "prompts"]
trigger_patterns:
  - "extend agent zero"
  - "agent zero development"
  - "build agent zero feature"
  - "create agent zero tool"
  - "add extension"
  - "framework development"
  - "agent zero architecture"
  - "how does agent zero work"
  - "create agent zero extension"
  - "add api endpoint"
  - "create agent profile"
  - "agent zero internals"
  - "how does the agent loop work"
  - "extension hook points"
  - "prompt system"
  - "agent profile"
---

# Agent Zero Development Guide

This skill provides comprehensive, accurate guidance for extending and building features for Agent Zero. Use it when you need to:

- Understand the **architecture** and project layout
- Create new **Tools** for agent capabilities
- Add **Extensions** to hook into the framework lifecycle
- Build **API Endpoints** for the Web UI
- Create **Agent Profiles** (subordinates) with custom prompts
- Understand and extend the **Prompt System**
- Create **Skills** (see the dedicated `create-skill` skill for the full wizard)
- Work with **Projects** and workspace configuration

> **Path convention:** Throughout this guide, `/a0/` refers to the framework root — this is `/a0/` inside Docker, or your local repository root in development. All paths are relative to this root.

> [!IMPORTANT]
> **Plugins are the primary way to extend Agent Zero.** Most new tools, extensions, and prompts should be packaged as plugins. For all plugin tasks (create, review, manage, debug, contribute), load the `a0-plugin-router` skill which routes to the appropriate specialist. This guide covers the underlying framework patterns that plugins build upon.

Related skills: `a0-plugin-router` (plugin tasks) | `create-skill` (skill creation wizard) | `a0-create-plugin` | `a0-review-plugin` | `a0-manage-plugin` | `a0-contribute-plugin` | `a0-debug-plugin`

---

## Architecture Overview

### Project Layout

```
/a0/                              # Framework root
├── agent.py                      # Core Agent + AgentContext + AgentConfig classes
├── initialize.py                 # Agent initialization logic
├── models.py                     # Model definitions
├── run_ui.py                     # Web UI entry point
│
├── tools/                        # Core tools (search, response, browser, etc.)
├── extensions/
│   ├── python/                   # Python lifecycle extensions
│   │   ├── <hook_point>/         # e.g., agent_init/, system_prompt/, etc.
│   │   │   └── _NN_name.py       # Numbered extension files
│   │   └── _functions/           # Implicit @extensible decorator extensions
│   └── webui/                    # JavaScript WebUI extensions
│       └── <hook_point>/         # e.g., json_api_call_before/
│           └── name.js
├── api/                          # Flask API endpoint handlers
├── helpers/                      # Framework utilities and base classes
│   ├── tool.py                   # Tool + Response base classes
│   ├── extension.py              # Extension base class + @extensible decorator
│   ├── api.py                    # ApiHandler base class
│   ├── files.py                  # File operations + prompt reading
│   ├── plugins.py                # Plugin system manager
│   ├── print_style.py            # Console output formatting
│   └── ...                       # Many more utility modules
│
├── prompts/                      # Core prompt fragments (system, tools, framework)
├── agents/                       # Agent profiles (subordinate specializations)
│   ├── default/                  # Base profile (inherited by others)
│   ├── agent0/                   # Main user-facing agent
│   ├── developer/                # Developer subordinate
│   ├── hacker/                   # Security subordinate
│   ├── researcher/               # Research subordinate
│   └── _example/                 # Example profile with tool + extension samples
│
├── plugins/                      # Core plugins (tools, extensions, prompts)
│   ├── _code_execution/          # Terminal/Python/Node.js execution
│   ├── _memory/                  # Persistent memory system
│   ├── _text_editor/             # File read/write/patch
│   ├── _model_config/            # LLM model selection
│   ├── _infection_check/         # Prompt injection safety
│   └── ...                       # More core plugins
│
├── skills/                       # Core skills (SKILL.md bundles)
├── knowledge/                    # Knowledge base files
├── webui/                        # Web UI frontend
├── docs/                         # Documentation
│
└── usr/                          # User-space (survives updates)
    ├── agents/                   # User-created agent profiles
    ├── plugins/                  # User-installed plugins
    ├── skills/                   # User-created skills
    ├── knowledge/                # User knowledge base files
    ├── extensions/               # Standalone user extensions (created on demand; prefer plugins instead)
    ├── projects/                 # Project workspaces (created on demand when user adds projects via UI)
    └── workdir/                  # Default working directory
```

### Key Architecture Patterns

1. **Plugin-first design** — Most capabilities (tools, extensions, prompts) are delivered via plugins in `/a0/plugins/` (core) or `/a0/usr/plugins/` (user).
2. **Extensions execute in numeric order** — Files named `_10_*.py`, `_20_*.py`, etc. run sequentially within each hook point.
3. **Tools inherit from `Tool`** — All tools implement the `execute()` method returning a `Response`.
4. **Shared `AgentContext`** — Enables state persistence across agents in a conversation.
5. **Async/await throughout** — All tool execution, extensions, and API handlers are async.
6. **Prompt fragments compose** — System prompts are assembled from named fragments with includes and variable substitution.
7. **Profile inheritance** — Agent profiles inherit from `default/` and override specific prompt fragments.
8. **User-space separation** — Everything under `/a0/usr/` survives framework updates.

### Agent Loop

The core execution cycle works as follows:

1. **User message** arrives (via UI or API)
2. **System prompt assembly** — prompt fragments are composed with includes and variable substitution
3. **LLM call** — the assembled prompt + conversation history is sent to the model
4. **Response parsing** — the framework parses the LLM response looking for JSON tool calls
5. **Tool execution** — if tool calls are found, each tool's `execute()` method is called and the result is appended to history
6. **Loop continues** — steps 3-5 repeat until the agent produces a `response` tool call (which ends the loop) or a loop limit is reached

Extensions fire at each stage (e.g., `monologue_start`, `before_main_llm_call`, `tool_execute_before`, etc.), allowing plugins to observe and modify behavior at every point.

---

## Creating Tools

Tools are how agents interact with the world. Each tool inherits from the `Tool` base class.

### Import Path

```python
from helpers.tool import Tool, Response
```

### Tool Base Class

```python
# /a0/helpers/tool.py

@dataclass
class Response:
    message: str              # Text response shown to agent
    break_loop: bool          # True = stop agent message loop
    additional: dict[str, Any] | None = None  # Extra metadata for history

class Tool:
    def __init__(self, agent: Agent, name: str, method: str | None,
                 args: dict[str,str], message: str,
                 loop_data: LoopData | None, **kwargs) -> None:
        self.agent = agent
        self.name = name
        self.method = method   # For tools with sub-methods (e.g., "skills_tool:load")
        self.args = args
        self.loop_data = loop_data
        self.message = message

    async def execute(self, **kwargs) -> Response:
        pass  # Override this

    # Lifecycle hooks (called automatically):
    async def before_execution(self, **kwargs): ...
    async def after_execution(self, response: Response, **kwargs): ...
```

### Where Tools Live

| Location | Purpose |
|---|---|
| `/a0/tools/` | Core framework tools (search, response, call_subordinate, etc.) |
| `/a0/plugins/<plugin>/tools/` | Plugin-provided tools (code_execution, memory, text_editor) |
| `/a0/agents/<profile>/tools/` | Profile-specific tool overrides |
| `/a0/usr/plugins/<plugin>/tools/` | User plugin tools |

### Example: Creating a Tool

Based on the actual `_example` profile in `/a0/agents/_example/tools/example_tool.py`:

```python
# my_tool.py
from helpers.tool import Tool, Response

class MyTool(Tool):
    async def execute(self, **kwargs):
        # Get arguments — kwargs contains the tool_args from the agent's JSON
        input_data = kwargs.get("input", "")

        # Do something
        result = f"Processed: {input_data}"

        # Return response
        return Response(
            message=result,        # Shown to the agent
            break_loop=False,      # Don't stop the agent loop
        )
```

> [!IMPORTANT]
> Every tool needs a corresponding **prompt fragment** so the agent knows how to use it. Create a file named `agent.system.tool.<tool_name>.md` in the appropriate `prompts/` directory. See the [Prompt System](#prompt-system) section.

### Tool Best Practices

- Always handle errors gracefully — return error messages in `Response`, don't crash
- Access agent context via `self.agent.context`
- Use `self.method` to support sub-methods (e.g., `my_tool:action1`, `my_tool:action2`)
- Use `kwargs.get()` to read arguments with defaults
- For long operations, use `self.set_progress()` or `self.add_progress()` to show status
- Access `self.loop_data` for loop state (iteration count, timing, etc.) — this is the `LoopData` instance passed during tool dispatch

---

## Creating Extensions

Extensions hook into specific lifecycle points in the agent framework.

### Import Path

```python
from helpers.extension import Extension
```

### Extension Base Class

```python
class Extension:
    def __init__(self, agent: "Agent | None", **kwargs):
        self.agent: "Agent | None" = agent
        self.kwargs = kwargs

    def execute(self, **kwargs) -> None | Awaitable[None]:
        pass  # Override this — kwargs are hook-point-specific
```

> Extensions can be sync or async. If `execute()` returns an `Awaitable`, the framework will `await` it automatically. The `agent` parameter is nullable because some hook points (like `startup_migration` or `banners`) fire before an agent exists.

### Extension File Location

Extensions live in directories named by their hook point. The path structure is:

```
extensions/python/<hook_point>/_NN_name.py
```

Where `_NN_` is a numeric prefix controlling execution order (e.g., `_10_`, `_20_`, `_50_`).

| Source | Path |
|---|---|
| Core extensions | `/a0/extensions/python/<hook_point>/` |
| Plugin extensions | `/a0/plugins/<plugin>/extensions/python/<hook_point>/` |
| User extensions | `/a0/usr/extensions/python/<hook_point>/` |
| Agent profile extensions | `/a0/agents/<profile>/extensions/<hook_point>/` |
| User plugin extensions | `/a0/usr/plugins/<plugin>/extensions/python/<hook_point>/` |

### Python Extension Hook Points

Complete list of available hook points:

| Hook Point | When It Fires | Common Use |
|---|---|---|
| `agent_init` | Agent is initialized | Load configs, set defaults |
| `system_prompt` | System prompt is being assembled | Inject prompt content |
| `monologue_start` | Agent monologue begins | Pre-processing, state setup |
| `message_loop_start` | Before message processing loop | Pre-loop setup |
| `message_loop_prompts_before` | Before prompt assembly in loop | Modify prompt inputs |
| `message_loop_prompts_after` | After prompt assembly in loop | Add context (memory recall lives here) |
| `before_main_llm_call` | Before the LLM API call | Modify prompts, add context |
| `util_model_call_before` | Before utility model calls | Modify utility prompts |
| `response_stream` | When response streaming begins | Initialize stream handlers |
| `response_stream_chunk` | Per response chunk received | Transform output, collect data |
| `response_stream_end` | Response streaming complete | Finalize, analyze full response |
| `reasoning_stream` | Reasoning/thinking stream begins | Monitor reasoning |
| `reasoning_stream_chunk` | Per reasoning chunk | Collect reasoning data |
| `reasoning_stream_end` | Reasoning stream complete | Analyze reasoning |
| `tool_execute_before` | Before a tool runs | Validation, logging, safety checks |
| `tool_execute_after` | After a tool runs | Post-process results |
| `hist_add_before` | Before adding to history | Modify history entries |
| `hist_add_tool_result` | After tool result added to history | Log tool results |
| `message_loop_end` | After message processing loop | Post-loop cleanup |
| `monologue_end` | Agent monologue complete | Memorization, cleanup |
| `process_chain_end` | Entire processing chain done | Final cleanup |
| `job_loop` | Background job loop tick | Periodic background tasks |
| `error_format` | Error is being formatted | Custom error messages |
| `startup_migration` | Framework startup | Data migrations |
| `banners` | Startup banners displayed | Add custom banners |
| `embedding_model_changed` | Embedding model changed | Reload vector stores (fired programmatically, not a directory-based hook) |
| `user_message_ui` | User message from UI | Pre-process user input |
| `webui_ws_connect` | WebSocket client connects | Session setup |
| `webui_ws_disconnect` | WebSocket client disconnects | Session cleanup |
| `webui_ws_event` | WebSocket event received | Handle custom WS events |

### The `@extensible` Decorator (Implicit Extension Points)

Any framework function decorated with `@extensible` automatically gets two extension points:

```
_functions/<module_path>/<qualname_path>/start
_functions/<module_path>/<qualname_path>/end
```

The path mapping converts Python module paths and qualified names using `/` separators:
- Module `agent.py` → `agent`
- Class method `Agent.handle_exception` → `Agent/handle_exception`
- Full path: `_functions/agent/Agent/handle_exception/start`

For nested modules like `helpers.history`, a method `History.add` would map to `_functions/helpers/history/History/add/start`.

For example, a function `Agent.handle_exception` in module `agent` creates:
- `_functions/agent/Agent/handle_exception/start`
- `_functions/agent/Agent/handle_exception/end`

Extensions in these directories receive a `data` dict with:
- `data["args"]` — positional args (mutable)
- `data["kwargs"]` — keyword args (mutable)
- `data["result"]` — set this to short-circuit the function
- `data["exception"]` — set to a `BaseException` to force-raise

This is used by plugins like `_error_retry` to wrap core agent methods.

### WebUI Extensions (JavaScript)

Client-side extensions live under `extensions/webui/<hook_point>/`:

| Hook Point | When It Fires |
|---|---|
| `json_api_call_before` | Before a JSON API request |
| `json_api_call_after` | After a JSON API response |
| `fetch_api_call_before` | Before a fetch API request |
| `fetch_api_call_after` | After a fetch API response |
| `get_message_handler` | Register custom message renderers |
| `set_messages_before_loop` | Before messages are rendered |
| `set_messages_after_loop` | After messages are rendered |
| `webui_ws_push` | WebSocket push to client |

### Example: Creating an Extension

Based on the actual `_example` profile in `/a0/agents/_example/extensions/agent_init/_10_example_extension.py`:

```python
# extensions/python/agent_init/_15_my_extension.py
from helpers.extension import Extension

class MyExtension(Extension):
    async def execute(self, **kwargs):
        # Access the agent
        agent = self.agent
        context = agent.context

        # Extension logic — kwargs content depends on the hook point
        agent.agent_name = "CustomAgent" + str(agent.number)
```

### Extension Execution Order

Extensions execute in numeric order based on filename prefix:

```
_10_first.py      # Runs first
_20_second.py     # Runs second
_50_third.py      # Runs third
```

Use 10-number increments to leave room for future extensions.

---

## Creating API Endpoints

API endpoints serve the Web UI and external clients using Flask.

### Import Path

```python
from helpers.api import ApiHandler
from flask import Request, Response
```

### ApiHandler Base Class

```python
class ApiHandler:
    def __init__(self, app: Flask, thread_lock: ThreadLockType):
        self.app = app
        self.thread_lock = thread_lock

    # Override these class methods to configure behavior:
    @classmethod
    def requires_loopback(cls) -> bool: return False   # Restrict to localhost
    @classmethod
    def requires_api_key(cls) -> bool: return False     # Require API key
    @classmethod
    def requires_auth(cls) -> bool: return True         # Require auth session
    @classmethod
    def get_methods(cls) -> list[str]: return ["POST"]   # HTTP methods
    @classmethod
    def requires_csrf(cls) -> bool: return cls.requires_auth()  # CSRF protection

    # Implement this:
    async def process(self, input: dict, request: Request) -> dict | Response:
        pass

    # Utility: get or create an agent context
    def use_context(self, ctxid: str, create_if_not_exists: bool = True) -> AgentContext:
        ...
```

### Where API Endpoints Live

| Location | Purpose |
|---|---|
| `/a0/api/` | Core API endpoints |
| `/a0/plugins/<plugin>/api/` | Plugin API endpoints |
| `/a0/usr/plugins/<plugin>/api/` | User plugin API endpoints |

Endpoints are auto-discovered by filename. The route is derived from the filename (e.g., `my_endpoint.py` -> `/api/my_endpoint`).

### Example: API Endpoint

```python
# api/my_endpoint.py
from helpers.api import ApiHandler
from flask import Request, Response
from agent import AgentContext

class MyEndpoint(ApiHandler):
    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET", "POST"]

    async def process(self, input: dict, request: Request) -> dict:
        param = input.get("param", "default")

        # Get or create agent context
        ctxid = input.get("context", "")
        context = self.use_context(ctxid)

        return {
            "result": f"processed {param}",
            "context": context.id,
        }
```

---

## Creating Agent Profiles

Agent profiles define specialized subordinates with custom prompts and behaviors.

### Profile Directory Structure

```
agents/<profile-name>/
+-- agent.yaml                    # Required: profile metadata
+-- prompts/                      # Optional: prompt overrides
|   +-- agent.system.main.role.md         # Role definition (most common override)
|   +-- agent.system.main.communication.md # Communication style
|   +-- agent.system.tool.<name>.md       # Tool-specific prompts
+-- tools/                        # Optional: profile-specific tools
|   +-- my_tool.py
+-- extensions/                   # Optional: profile-specific extensions
    +-- <hook_point>/
        +-- _NN_extension.py
```

### agent.yaml Format

The actual format is simple YAML with only three fields:

```yaml
title: Developer
description: Agent specialized in complex software development.
context: Use this agent for software development tasks, including writing code,
  debugging, refactoring, and architectural design.
```

| Field | Purpose |
|---|---|
| `title` | Display name shown in UI and agent selection |
| `description` | Brief description of the agent's specialization |
| `context` | Instructions for when to delegate to this profile |

> [!NOTE]
> There is **no** per-profile model configuration, temperature, or allowed_tools in the profile YAML. Model configuration is managed by the `_model_config` plugin. Tool availability is controlled by plugin activation.

### Where Profiles Live

| Location | Purpose |
|---|---|
| `/a0/agents/` | Core profiles (default, agent0, developer, hacker, researcher) |
| `/a0/usr/agents/` | User-created profiles (survives updates) |

### Prompt Override Mechanism

Profiles inherit all prompts from the `default/` profile. To customize behavior, place prompt files with the **same name** in your profile's `prompts/` directory. The framework searches profile-specific prompts first, then falls back to the default.

The most common override is `agent.system.main.role.md` which defines the agent's role and specialization.

### Example: Creating a Profile

```yaml
# /a0/usr/agents/data-analyst/agent.yaml
title: Data Analyst
description: Agent specialized in data analysis, visualization, and statistical modeling.
context: Use this agent for data analysis tasks, creating visualizations, statistical
  analysis, and working with datasets in Python.
```

```markdown
<!-- /a0/usr/agents/data-analyst/prompts/agent.system.main.role.md -->

## Your role
You are a specialized data analysis agent.
Your expertise includes:
- Python data analysis (pandas, numpy, scipy)
- Data visualization (matplotlib, seaborn, plotly)
- Statistical modeling and hypothesis testing
- SQL queries and database analysis
- Data cleaning and preprocessing

## Process
1. Understand the data and the question
2. Choose appropriate tools and methods
3. Execute analysis with code_execution_tool
4. Visualize results when applicable
5. Provide clear interpretation of findings
```

### Reference: The `_example` Profile

The framework includes a complete example profile at `/a0/agents/_example/` that demonstrates:
- Custom tool: `/a0/agents/_example/tools/example_tool.py`
- Custom extension: `/a0/agents/_example/extensions/agent_init/_10_example_extension.py`
- Tool prompt: `/a0/agents/_example/prompts/agent.system.tool.example_tool.md`
- Role prompt: `/a0/agents/_example/prompts/agent.system.main.role.md`

---

## Prompt System

Agent Zero assembles system prompts from **named fragments** using includes and variable substitution.

### Prompt File Naming Convention

Prompt files follow a dot-separated naming scheme:

```
agent.system.main.md            # Main system prompt (entry point)
agent.system.main.role.md       # Role definition
agent.system.main.communication.md  # Communication style
agent.system.tool.<name>.md     # Tool usage instructions
agent.system.tools.md           # Tools overview
agent.system.projects.main.md   # Project system
agent.system.secrets.md         # Secret handling
agent.system.skills.md          # Skills listing
agent.system.datetime.md        # Current date/time
agent.context.extras.md         # Context extras
fw.*.md                         # Framework messages (errors, hints, etc.)
```

### Where Prompts Live

| Location | Priority | Purpose |
|---|---|---|
| `/a0/agents/<profile>/prompts/` | Highest | Profile-specific overrides |
| `/a0/usr/agents/<profile>/prompts/` | High | User profile overrides |
| `/a0/plugins/<plugin>/prompts/` | Normal | Plugin-provided prompts |
| `/a0/usr/plugins/<plugin>/prompts/` | Normal | User plugin prompts |
| `/a0/prompts/` | Base | Core framework prompts |

The framework searches directories in priority order and uses the **first match** found.

### Include Mechanism

Prompts can include other fragments using double-brace `include` directives.

The syntax uses opening double-brace, the keyword, and closing double-brace:

| Directive | Purpose |
|---|---|
| `{{include "agent.system.main.role.md"}}` | Include a named prompt fragment |
| `{{include "agent.system.main.communication.md"}}` | Include another fragment |
| `{{include original}}` | Include the same file from the next lower-priority directory |

The `include original` directive is particularly useful for **extending** rather than fully **replacing** a prompt — your override can include the base version and add to it.

### Variable Substitution

Prompts support `{{variable_name}}` placeholders that are replaced at render time with values passed from the framework or plugin configuration.

### Conditional Blocks

Prompts support conditional rendering based on variables.

### Reading Prompts in Code

```python
# From within an Agent method:
content = self.read_prompt("fw.some_message.md", variable1="value1")

# From helpers:
from helpers.files import read_prompt_file
content = read_prompt_file("template.md", _directories=[...], var="value")
```

---

## Creating Skills

Skills are reusable instruction bundles that the agent loads on demand via the `skills_tool`. Each skill lives in a directory containing a `SKILL.md` file with YAML frontmatter.

| Location | Purpose |
|---|---|
| `/a0/skills/` | Core skills (shipped with framework) |
| `/a0/usr/skills/` | User-created skills (survives updates) |

The agent interacts with skills through JSON tool calls:

```json
{"tool_name": "skills_tool:list", "tool_args": {}}
{"tool_name": "skills_tool:load", "tool_args": {"skill_name": "my-skill"}}
```

> For the complete skill creation wizard — including SKILL.md format, frontmatter fields, directory structure, best practices, and examples — load the `create-skill` skill.

---

## Working with Projects

Projects provide isolated workspaces with custom configuration.

> Projects are typically created and managed via the Web UI. The `.a0proj/` directory and `project.json` are auto-generated when you create a project through the UI.

### Project Structure

```
/a0/usr/projects/<project-name>/
+-- .a0proj/
|   +-- project.json          # Project configuration
|   +-- agents.json           # Per-project agent overrides
|   +-- variables.env         # Non-sensitive variables
|   +-- secrets.env           # Encrypted secrets
|   +-- memory/               # Project-specific memory
|       +-- index.faiss
|       +-- index.pkl
|       +-- embedding.json
+-- <project-files>/          # Your project files (working directory)
```

### project.json Format

```json
{
    "title": "My Project",
    "description": "Project description",
    "instructions": "Markdown instructions for the agent when this project is active",
    "color": "#3a86ff",
    "git_url": "",
    "memory": "own",
    "file_structure": {
        "enabled": true,
        "max_depth": 5,
        "max_files": 20,
        "max_folders": 20,
        "max_lines": 250,
        "gitignore": ".a0proj/\nvenv/\n**/__pycache__/\n**/node_modules/\n**/.git/\n"
    }
}
```

| Field | Purpose |
|---|---|
| `title` | Display name |
| `description` | Brief description |
| `instructions` | Markdown injected into agent system prompt when project is active |
| `color` | UI accent color (hex) |
| `git_url` | Optional Git repository URL |
| `memory` | `"own"` for project-specific memory, or shared |
| `file_structure` | Controls the working directory tree shown to the agent |

---

## Plugin System Overview

Plugins are the **primary extension mechanism** in Agent Zero. A plugin can bundle tools, extensions, prompts, API endpoints, helpers, and UI components into a self-contained package.

> For all plugin tasks — creating, reviewing, managing, contributing, or debugging plugins — load the `a0-plugin-router` skill, which routes to the appropriate specialist skill.

### Core Plugins

The framework ships with these core plugins in `/a0/plugins/`:

| Plugin | Purpose |
|---|---|
| `_code_execution` | Terminal, Python, Node.js code execution |
| `_memory` | Persistent vector memory system |
| `_text_editor` | File read/write/patch with line numbers |
| `_model_config` | LLM model selection and configuration |
| `_browser_agent` | Browser automation and web interaction |
| `_infection_check` | Prompt injection safety checks |
| `_error_retry` | Retry on critical exceptions |
| `_email_integration` | Email communication via IMAP/SMTP |
| `_telegram_integration` | Telegram bot integration |
| `_chat_branching` | Branch chats from any message |
| `_promptinclude` | Persistent behavioral rules (*.promptinclude.md) |
| `_plugin_installer` | Install plugins from ZIP/Git/Hub |
| `_plugin_scan` | Security scanning for plugins |
| `_plugin_validator` | Plugin manifest and code validation |

---

## Common Patterns Reference

### Accessing Agent Context

```python
# Shared across all agents in a conversation
context = self.agent.context
data = context.data  # dict-like shared state

# Store data
data["my_key"] = my_value

# Retrieve data
value = data.get("my_key", default)
```

### Using File Helpers

```python
from helpers import files

# File operations
content = files.read_file("path/to/file")
files.write_file("path/to/file", content)
exists = files.exists("path/to/file")

# Read and render a prompt file
content = files.read_prompt_file("template.md", _directories=[...], var="value")
```

### Console Output

```python
from helpers.print_style import PrintStyle

PrintStyle.hint("Informational message")
PrintStyle.warning("Warning message")
PrintStyle.error("Error message")
PrintStyle(font_color="#85C1E9").print("Custom styled output")
```

### Error Handling

```python
from helpers.tool import Response

try:
    result = await risky_operation()
except Exception as e:
    PrintStyle.error(f"Operation failed: {e}")
    return Response(message=f"Error: {e}", break_loop=False)
```

---

## Development Workflow

When building features for Agent Zero:

### 1. Choose Your Extension Point

| Want to... | Use |
|---|---|
| Add a new agent capability | **Tool** (in a plugin) |
| Hook into agent lifecycle | **Extension** (in a plugin) |
| Add Web UI functionality | **API endpoint** + **WebUI extension** |
| Create a specialized agent | **Agent profile** |
| Bundle reusable instructions | **Skill** |
| Package everything together | **Plugin** (recommended) |

### 2. Develop in User Space

- New plugins -> `/a0/usr/plugins/<name>/`
- New profiles -> `/a0/usr/agents/<name>/`
- New skills -> `/a0/usr/skills/<name>/`
- New extensions -> `/a0/usr/extensions/python/<hook_point>/`

### 3. Test and Iterate

- **Local dev**: Run `python run_ui.py` (default port 50001 at `http://localhost:50001`)
- **Docker**: Restart the container or use the UI restart button; check logs with `docker logs -f <container_name>`
- Test with minimal input first
- Verify in the Web UI

### 4. Contributing

For contribution guidelines, see `/a0/docs/contribution.md`. For plugin contributions to the community Plugin Index, load the `a0-contribute-plugin` skill.

---

## Best Practices

### DO
- Use the **plugin system** for new features (see `a0-create-plugin` skill)
- Follow existing code patterns and conventions
- Write clear docstrings and comments
- Handle errors gracefully in tools and extensions
- Create prompt fragments for every tool (`agent.system.tool.<name>.md`)
- Develop in `/a0/usr/` directories to survive updates
- Test with the `_example` profile as a reference
- Use `from helpers.*` imports (not `from python.helpers.*`)

### DON'T
- Modify files in `/a0/plugins/` or `/a0/tools/` directly (use usr/ space)
- Hardcode paths or configuration values
- Skip creating prompt files for tools
- Ignore the plugin system (it's the intended extension mechanism)
- Mix sync and async code carelessly
- Access internal structures when helpers exist

---

## Quick Reference: Key Files

| File | Purpose |
|---|---|
| `/a0/agent.py` | Core `Agent`, `AgentContext`, `AgentConfig` classes |
| `/a0/helpers/tool.py` | `Tool` + `Response` base classes |
| `/a0/helpers/extension.py` | `Extension` base + `@extensible` decorator |
| `/a0/helpers/api.py` | `ApiHandler` base class |
| `/a0/helpers/files.py` | File ops + prompt reading |
| `/a0/helpers/plugins.py` | Plugin system manager |
| `/a0/helpers/print_style.py` | Console output formatting |
| `/a0/agents/_example/` | Reference example profile with tool + extension |
| `/a0/prompts/agent.system.main.md` | Main system prompt entry point |