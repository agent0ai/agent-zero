# Agent Zero - AGENTS.md

[Generated using reconnaissance on 2026-02-22]

## Quick Reference
Tech Stack: Python 3.12+ | Flask | Alpine.js | LiteLLM | WebSocket (Socket.io)
Dev Server: python run_ui.py (runs on http://localhost:50001 by default)
Run Tests: pytest (standard) or pytest tests/test_name.py (file-scoped)
Documentation: README.md | docs/
Frontend Deep Dives: [Component System](docs/agents/AGENTS.components.md) | [Modal System](docs/agents/AGENTS.modals.md) | [Plugin Architecture](docs/agents/AGENTS.plugins.md)

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Core Commands](#core-commands)
3. [Docker Environment](#docker-environment)
4. [Project Structure](#project-structure)
5. [Development Patterns & Conventions](#development-patterns--conventions)
6. [Safety and Permissions](#safety-and-permissions)
7. [Code Examples](#code-examples)
8. [Git Workflow](#git-workflow)
9. [Release Notes](#release-notes)
10. [Troubleshooting](#troubleshooting)

---

## Project Overview

Agent Zero is a dynamic, organic agentic framework designed to grow and learn. It uses the operating system as a tool, featuring a multi-agent cooperation model where every agent can create subordinates to break down tasks.

Type: Full-Stack Agentic Framework (Python Backend + Alpine.js Frontend)
Status: Active Development
Primary Language(s): Python, JavaScript (ES Modules)

---

## Core Commands

### Setup
Do not combine these commands; run them individually:
```bash
pip install -r requirements.txt
pip install -r requirements2.txt
```
- Start WebUI: python run_ui.py

---

## Docker Environment

When running in Docker, Agent Zero uses two distinct Python runtimes to isolate the framework from the code being executed:

### 1. Framework Runtime (/opt/venv-a0)
- Version: Python 3.12.4
- Purpose: Runs the Agent Zero backend, API, and core logic.
- Packages: Contains all dependencies from requirements.txt.

### 2. Execution Runtime (/opt/venv)
- Version: Python 3.13
- Purpose: Default environment for the interactive terminal and the agent's code execution tool.
- Behavior: This is the environment active when you docker exec into the container. Packages installed by the agent via pip install during a task are stored here.

---

## Project Structure

```
/
├── agent.py              # Core Agent and AgentContext definitions
├── initialize.py         # Framework initialization logic
├── models.py             # LLM provider configurations
├── run_ui.py             # WebUI server entry point
├── api/                  # API Handlers (ApiHandler subclasses) + WsHandler subclasses (ws_*.py)
├── extensions/           # Backend lifecycle extensions
├── helpers/              # Shared Python utilities (plugins, files, etc.)
├── tools/                # Agent tools (Tool subclasses)
├── webui/
│   ├── components/       # Alpine.js components
│   ├── js/               # Core frontend logic (modals, stores, etc.)
│   └── index.html        # Main UI shell
├── usr/                  # User data directory (isolated from core)
│   ├── plugins/          # Custom user plugins
│   ├── settings.json     # User-specific configuration
│   └── workdir/          # Default agent workspace
├── plugins/              # Core system plugins
├── agents/               # Agent profiles (prompts and config)
├── prompts/              # System and message prompt templates
├── knowledge/
│   └── main/about/       # Agent self-knowledge (indexed into vector DB for runtime recall)
│       ├── identity.md           # Philosophy, principles, project context
│       ├── architecture.md       # Agent loop, memory pipeline, multi-agent, extensions
│       ├── capabilities.md       # Detailed capabilities and limitations
│       ├── configuration.md      # LLM roles, providers, profiles, plugins, settings
│       └── setup-and-deployment.md  # Docker deployment, updates, troubleshooting
└── tests/                # Pytest suite
```

Key Files:
- agent.py: Defines AgentContext and the main Agent class.
- helpers/plugins.py: Plugin discovery and configuration logic.
- webui/js/AlpineStore.js: Store factory for reactive frontend state.
- helpers/api.py: Base class for all API endpoints.
- scripts/openrouter_release_notes_system_prompt.md: Editable system prompt used to generate GitHub release notes during Docker publishing.
- knowledge/main/about/: Agent self-knowledge files, indexed into the vector DB for runtime recall. Not user-facing docs - written for the agent's internal reference.
- docs/agents/AGENTS.components.md: Deep dive into the frontend component architecture.
- docs/agents/AGENTS.modals.md: Guide to the stacked modal system.
- docs/agents/AGENTS.plugins.md: Comprehensive guide to the full-stack plugin system.

---

## Development Patterns & Conventions

### Backend (Python)
- Context Access: Use from agent import AgentContext, AgentContextType (not helpers.context).
- Communication: Use mq from helpers.messages to log proactive UI messages:
  mq.log_user_message(context.id, "Message", source="Plugin")
- API Handlers: Derive from ApiHandler in helpers/api.py.
- Extensions: Use the extension framework in helpers/extension.py for lifecycle hooks.
- Error Handling: Use RepairableException for errors the LLM might be able to fix.

### Frontend (Alpine.js)
- Store Gating: Always wrap store-dependent content in a template:
```html
<div x-data>
  <template x-if="$store.myStore">
    <div x-init="$store.myStore.onOpen()">...</div>
  </template>
</div>
```
- Store Registration: Use createStore from /js/AlpineStore.js.
- Modals: Use openModal(path) and closeModal() from /js/modals.js.

### Plugin Architecture
- Location: Always develop new plugins in usr/plugins/.
- Manifest: Every plugin requires a plugin.yaml with name, description, version, and optionally settings_sections, per_project_config, per_agent_config, and always_enabled.
- Discovery: Conventions based on folder names (api/, tools/, webui/, extensions/).
- Plugin-local Python imports: Prefer `usr.plugins.<plugin_name>...` for code that lives under `usr/plugins/`. Avoid `sys.path` hacks and avoid symlink-dependent `plugins.<plugin_name>...` imports for community plugins.
- Runtime hooks: Plugins may also expose hooks in hooks.py, callable by the framework through helpers.plugins.call_plugin_hook(...).
- Hook runtime: hooks.py executes inside the Agent Zero framework Python environment, so sys.executable -m pip installs dependencies into that same framework runtime.
- Environment targeting: If a plugin needs packages or binaries for the separate agent execution runtime or system environment, it must explicitly switch environments in a subprocess by targeting the correct interpreter, virtualenv, or package manager.
- Settings: Use get_plugin_config(plugin_name, agent=agent) to retrieve settings. Plugins can expose a UI for settings via webui/config.html. Plugin settings modals instantiate a local context from $store.pluginSettingsPrototype; bind plugin fields to config.* and use context.* for modal-level state and actions.
- Activation: Global and scoped activation rules are stored as .toggle-1 (ON) and .toggle-0 (OFF). Scoped rules are handled via the plugin "Switch" modal.
- Cleanup rule: Plugins should not permanently modify the system in ways that outlive the plugin. Deleting a plugin should not leave behind symlinks, unmanaged services, or stray files outside plugin-owned paths unless the user explicitly requested that behavior.

### Releases
- Docker publishing automation lives in `.github/workflows/docker-publish.yml`.
- Releasable tags follow `v{X}.{Y}` and only tags `>= v1.0` are considered by the workflow.
- The latest eligible tag on `main` also creates or updates a GitHub release after the Docker image push succeeds.
- GitHub release notes are generated on the fly in `.github/scripts/docker_release_plan.py` by comparing the new tag against the previous published GitHub release tag, collecting commit subjects and descriptions in that range, and sending them to OpenRouter.
- The OpenRouter call uses `OPENROUTER_API_KEY` and `OPENROUTER_MODEL_NAME` from the workflow environment, with the system prompt stored in `scripts/openrouter_release_notes_system_prompt.md`.
- Prioritize user-visible features, important fixes, infra or packaging changes, and breaking notes. Skip low-signal churn.
- If the generated summary has no meaningful content, the release body falls back to `No release notes.`

### Lifecycle Synchronization
| Action | Backend Extension | Frontend Lifecycle |
|---|---|---|
| Initialization | agent_init | init() in Store |
| Mounting | N/A | x-create directive |
| Processing | monologue_start/end | UI loading state |
| Cleanup | context_deleted | x-destroy directive |

---

## Safety and Permissions

### Allowed Without Asking
- Read any file in the repository.
- Update code files in usr/.

### Ask Before Executing
- pip install (new dependencies).
- Deleting core files outside of usr/ or tmp/.
- Modifying agent.py or initialize.py.
- Making git commits or pushes.

### Never Do
- Commit, hardcode or leak secrets or .env files.
- Bypass CSRF or authentication checks.
- Hardcode API keys.

---

## Code Examples

### API Handler (Good)
```python
from helpers.api import ApiHandler, Request, Response

class MyHandler(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        # Business logic here
        return {"ok": True, "data": "result"}
```

### Alpine Store (Good)
```javascript
import { createStore } from "/js/AlpineStore.js";

export const store = createStore("myStore", {
    items: [],
    init() { /* global setup */ },
    onOpen() { /* mount setup */ },
    cleanup() { /* unmount cleanup */ }
});
```

### Tool Definition (Good)
```python
from helpers.tool import Tool, Response

class MyTool(Tool):
    async def execute(self, **kwargs):
        # Tool logic
        return Response(message="Success", break_loop=False)
```

---

## Git Workflow

- Docker publish automation lives in `.github/workflows/docker-publish.yml`.
- Release tags handled by automation must match `vX.Y` and be `>= v1.0`.
- Allowed release branches are configured at the top of the workflow. `main` publishes `<tag>` and `latest`; other allowed branches publish only the branch tag.
- Manual dispatch accepts an optional tag. Without a tag it backfills missing Docker Hub tags. With a tag it rebuilds that exact target and only refreshes `latest` and the GitHub release when that tag is still the newest eligible tag on `main`.

---

## Release Notes

- The latest eligible `main` tag generates its GitHub release notes during Docker publish instead of reading committed Markdown files.
- The release-note prompt is editable in `scripts/openrouter_release_notes_system_prompt.md`.
- The commit range starts at the previous published GitHub release tag, not merely the previous semantic tag in the repository.

## Troubleshooting

### Dependency Conflicts
If pip install fails, try running in a clean virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements2.txt
```

### WebSocket Connection Failures
- Check if X-CSRF-Token is being sent.
- Ensure the runtime ID in the session matches the current server instance.

---

*Last updated: 2026-03-25*
*Maintained by: Agent Zero Core Team*
