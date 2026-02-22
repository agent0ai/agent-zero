# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Agent Zero is a personal agentic AI framework with a hierarchical multi-agent architecture. Agents can spawn subordinates, use tools, maintain persistent memory, and be extended via a plugin system. This is the security-focused variant (`agent-zero-sec`) with a `hacker` agent profile for penetration testing and security tasks.

## Running the Application

**Docker (primary deployment):**
```bash
docker pull agent0ai/agent-zero
docker run -p 50001:80 agent0ai/agent-zero
# Access at http://localhost:50001
```

**Local (inside Docker container):**
```bash
python run_ui.py --port=8080 --host=0.0.0.0
```

The entry point is `run_ui.py`, which starts a Flask/Uvicorn server with SocketIO for real-time streaming.

## Running Tests

The test suite uses pytest. Inside the Docker venv (`/opt/venv-a0`), or with a local venv:
```bash
# Run all tests
pytest tests/

# Run a single test file
pytest tests/test_websocket_handlers.py

# Run a single test
pytest tests/test_websocket_handlers.py::test_name -v
```

## Architecture

### Core Files

- **`agent.py`** — Core agent logic: `AgentContext` (manages execution state, logging, UI connection) and `Agent` (message loop, tool dispatch, LLM calls). `AgentConfig` is a dataclass holding all config.
- **`models.py`** — LLM provider abstraction via LiteLLM. `ModelConfig` wraps provider/name/limits. Supports 25+ providers configured in `conf/model_providers.yaml`.
- **`run_ui.py`** — Flask + Uvicorn + SocketIO web server. 74 REST API endpoints in `python/api/`, WebSocket handlers in `python/websocket_handlers/`.
- **`initialize.py`** — Builds `AgentConfig` from `usr/settings.json`, merging runtime args and environment overrides.

### Agent Message Loop

The core flow in `agent.py` (`Agent.monologue()`):
1. Extensions at `message_loop_start` / `monologue_start` hooks fire
2. System prompt assembled from `prompts/` files (Jinja-like `{{ include }}` / `{{var}}`)
3. LLM called with streaming; extensions intercept at `before_main_llm_call`, `reasoning_stream`, `response_stream`
4. Tool invocations in LLM output are parsed and dispatched to `python/tools/`
5. Tool results added to history; loop continues until `response_tool` is called
6. Extensions at `message_loop_end` / `monologue_end` fire

### Extension System (`python/extensions/`)

Extensions are Python files in named subdirectories corresponding to lifecycle hooks. They are auto-discovered and executed in filename order (e.g., `_10_`, `_20_`). Agent-specific profiles can override defaults by placing files under `agents/<profile>/extensions/`.

Hook categories: `agent_init`, `monologue_start/end`, `message_loop_start/end`, `message_loop_prompts_before/after`, `before_main_llm_call`, `system_prompt`, `reasoning_stream*`, `response_stream*`, `hist_add_before`, `hist_add_tool_result`, `tool_execute_before/after`, `user_message_ui`, `banners`, `error_format`, `util_model_call_before`, `process_chain_end`.

### Tools System (`python/tools/`)

Each tool is a class inheriting from `Tool` with `before_execution()`, `execute()`, `after_execution()`. Key tools:
- `code_execution_tool.py` — executes Python/Shell/Node.js (via SSH or Docker)
- `call_subordinate.py` — spawns subordinate agents
- `knowledge_tool._py` — web search + vector DB RAG (disabled file extension `._py`)
- `memory_*.py` — save/load/delete/forget from vector memory
- `browser_agent.py` — Playwright browser automation
- `response.py` — terminates the agent loop and returns output

Files ending in `._py` are disabled tools (not loaded).

### Prompt System (`prompts/`)

104+ Markdown template files. `agent.system.main.md` is the root, using `{{ include "file.md" }}` directives. Variables are injected from `.py` files with matching names (e.g., `agent.system.tools.md` has `agent.system.tools.py` as its dynamic loader). Agent profiles can override any prompt by placing a file at `agents/<profile>/prompts/<same-filename>.md`.

### Memory System

Hybrid automatic + manual memory using FAISS vector indices with SentenceTransformer embeddings (stored in `memory/`). A separate utility LLM (configured in settings) handles summarization and memory consolidation. Memory is organized by category: user info, fragments, solutions, metadata.

### Settings Hierarchy

Settings cascade from lowest to highest priority:
1. Hardcoded defaults in `python/helpers/settings.py`
2. `usr/settings.json` (written by the Settings UI)
3. `agents/<profile>/settings.json` (agent-specific overrides)
4. Runtime CLI args (`--key=value` passed to `run_ui.py`)
5. Environment variables with `A0_SET_*` prefix

API keys come from `.env` or `usr/secrets.env`.

### Agent Profiles (`agents/`)

Each profile directory can contain: `agent.json` (metadata), `settings.json` (overrides), `prompts/` (prompt overrides), `extensions/` (extension overrides). Built-in profiles: `agent0` (main user-facing), `hacker` (security/pentest), `developer`, `researcher`, `default`.

### Projects System (`usr/projects/`)

Isolated workspaces per chat session. Each project at `usr/projects/{name}/.a0proj/` has its own memory, knowledge, instructions, and `secrets.env` / `variables.env` to prevent cross-client context bleed.

### Skills System (`skills/`, `usr/skills/`)

Skills follow the open SKILL.md standard with YAML frontmatter (`name`, `description`, `trigger_patterns`, etc.). They are vector-indexed and loaded contextually (not always in system prompt). Custom skills go in `usr/skills/`.
