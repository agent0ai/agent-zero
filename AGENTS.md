# Agent Zero (Fork)

Custom fork of [agent0ai/agent-zero](https://github.com/agent0ai/agent-zero) — autonomous AI agent framework with Cognee-powered memory, MCP integration, and Home Assistant addon deployment.

## What is Agent Zero

Agent Zero is a **general-purpose personal AI assistant** that uses the computer as a tool. It is not pre-programmed for specific tasks — give it a task and it will write code, use the terminal, search the web, cooperate with subordinate agents, and memorize solutions for future use.

### Core Principles

- **Dynamic and organic** — not a predefined agentic framework; grows and learns as you use it
- **Fully transparent** — nothing is hidden; every prompt, tool, and message template is readable and customizable
- **Computer as a tool** — no single-purpose tools pre-programmed; the agent writes its own code and creates its own tools
- **Multi-agent cooperation** — agents create subordinate agents for subtasks, each with clean focused context
- **Prompt-driven behavior** — the entire framework is guided by prompts in the `prompts/` folder; change the prompt, change the framework

### Default Tools

| Tool | Purpose |
|------|---------|
| `code_execution_tool` | Execute Python/bash code in sandboxed environment |
| `browser_agent` | Browser automation via Playwright/browser-use |
| `search_engine` | Web search (DuckDuckGo, SearxNG, Perplexity) |
| `memory_save/load/delete/forget` | Persistent memory operations via Cognee |
| `document_query` | Query PDFs, CSVs, HTML, text files |
| `call_subordinate` | Create subordinate agent for subtasks |
| `scheduler` | Cron-based task scheduling |
| `skills_tool` | Discover and install Skills (SKILL.md standard) |
| `notify_user` | Send notifications to the user |
| `a2a_chat` | Agent-to-Agent protocol communication |
| `vision_load` | Image analysis |
| `behaviour_adjustment` | Runtime behaviour tuning |

### Skills System

Skills are portable, structured agent capabilities using the open **SKILL.md** standard (compatible with Claude Code, Cursor, Codex, GitHub Copilot). Skills are contextual expertise loaded dynamically when relevant. Can be installed via `/skill-install` chat command or through the UI.

### Extension Hooks

The behavior is fully extensible via `python/extensions/`. Available hook points:

- Agent lifecycle: `agent_init`, `banners`, `user_message_ui`
- Message loop: `message_loop_start`, `message_loop_end`, `message_loop_prompts_before`, `message_loop_prompts_after`
- LLM: `before_main_llm_call`, `util_model_call_before`
- Streaming: `reasoning_stream`, `response_stream` (+ `_chunk`, `_end` variants)
- Tools: `tool_execute_before`, `tool_execute_after`
- History: `hist_add_before`, `hist_add_tool_result`
- Monologue: `monologue_start`, `monologue_end`
- System: `system_prompt`, `error_format`, `process_chain_end`

### Multi-Agent Architecture

Every agent has a superior (human user for Agent 0) and can create subordinate agents. Subordinates can have dedicated prompts, tools, and system extensions configured via subagent profiles. Agent number tracking in backend enables multi-agent identification.

### LLM Providers

Powered by LiteLLM with support for: OpenRouter (default), OpenAI, Anthropic, Google Gemini, Ollama, LM Studio, Venice.ai, CometAPI, Z.AI, Moonshot AI, AWS Bedrock, Azure, HuggingFace, and custom endpoints. Providers configured via `providers.yaml`.

## Architecture

```
agent-zero/
├── agent.py              ← Core Agent class, message loop, tool execution
├── initialize.py         ← Agent initialization: settings, model config
├── models.py             ← Data models, LLM provider wiring (litellm)
├── run_ui.py             ← Flask + uvicorn server, WebSocket, API routes
├── prepare.py            ← One-time setup: runtime init, env prep
├── prompts/              ← All agent prompts and message templates (fully customizable)
├── python/
│   ├── api/              ← 75+ REST API endpoints (chat, backup, memory, MCP, scheduler, files, settings)
│   ├── extensions/       ← Hook points: message loop, prompts, streaming, tools, monologue, errors
│   ├── helpers/          ← Core utilities (memory, cognee, MCP, LLM calls, browser, tasks, websocket)
│   ├── tools/            ← Agent tools (code exec, browser, memory, search, scheduler, skills)
│   └── websocket_handlers/ ← WebSocket namespace handlers (state sync, hello)
├── tests/                ← Unit + integration tests (pytest, ~2400 tests, 76% coverage)
├── requirements.txt      ← Main dependencies
├── requirements2.txt     ← Override deps (litellm, openai, cognee) — installed after requirements.txt
└── requirements.dev.txt  ← Test dependencies (pytest, pytest-cov, pytest-timeout)
```

## Versioning & Release

- Current: **v0.9.8.17**
- Tags follow: `v0.9.8.N` increments
- The hassio addon version MUST match the fork tag

Release flow:
1. Push code to `main`
2. Rebuild Docker image `ghcr.io/nafania/agent-zero:latest`
3. Tag the commit: `git tag v0.9.8.N && git push origin v0.9.8.N`
4. Update `agent-zero-hassio/agent_zero/config.yaml` version to `"0.9.8.N"`
5. Commit and push hassio repo

## Addon Deployment (agent-zero-hassio)

The addon builds FROM `ghcr.io/nafania/agent-zero:latest` (see `build.yaml`).

**Persistent volume:** `/a0/usr` (mapped via `addon_config` in `config.yaml`). Everything outside `/a0/usr` is ephemeral — lost on container rebuild.

**Critical:** All databases, caches, and user data MUST be stored under `/a0/usr/`. Cognee SQLite is at `/a0/usr/cognee/cognee_system/`.

Environment configured via `config.yaml`: `HOME=/a0/usr`, XDG dirs, extension auto-install, SearxNG, ports (80→50001).

## Cognee Memory System

Cognee provides vector search, knowledge graphs, and document storage. Persistent memory allows agents to memorize solutions, code, facts, and instructions to solve tasks faster in future sessions.

| Component | Path | Purpose |
|-----------|------|---------|
| `cognee_init.py` | `python/helpers/` | Config, env vars, `init_cognee()` startup, `get_cognee()` getter |
| `memory.py` | `python/helpers/` | Memory class: parallel search, insert, bulk delete, knowledge preload |
| `cognee_background.py` | `python/helpers/` | Background cognify/memify pipeline on dirty datasets |
| `memory_dashboard.py` | `python/api/` | Dashboard API with in-memory cache (60s TTL) and server-side pagination |

Memory areas: `MAIN`, `FRAGMENTS`, `SOLUTIONS`. Per-agent subdirs (`default`, `projects/<name>`).

Knowledge files in `usr/knowledge/` are auto-imported into Cognee on first agent use. If Cognee DB is empty but knowledge index exists, full re-import is triggered automatically.

### Initialization

Cognee is initialized **once at startup** in `prepare.py` via `init_cognee()`. This sets env vars, imports cognee, creates DB tables, and starts the background worker. Runtime code uses `get_cognee()` which returns the cached module or raises `RuntimeError` if not initialized. No lazy init or retry wrappers in the runtime path.

**Env var order matters:** `SYSTEM_ROOT_DIRECTORY`, `DB_PROVIDER`, `DB_NAME` must be set before `import cognee`. See `cognee_init.py`.

### Search

Search types: `GRAPH_COMPLETION`, `CHUNKS_LEXICAL`, `RAG_COMPLETION`, `TRIPLET_COMPLETION`, and more. Multi-search enabled by default — queries multiple search types **in parallel** via `asyncio.gather` and deduplicates results. Each search type has a 15-second timeout; failed/timed-out types don't block others.

In auto-recall (`_50_recall_memories.py`), fast types (CHUNKS, CHUNKS_LEXICAL) run first, slow types (GRAPH_COMPLETION) run in background and merge results later.

### Dashboard

Memory dashboard caches listing results in-memory with 60s TTL. Cache is invalidated on insert/delete/update. Server-side pagination via `offset`/`limit` — only the requested page is returned, not all records.

### Background Worker

`CogneeBackgroundWorker` runs `cognify` + `memify` on dirty datasets, triggered by time interval or insert count threshold. Started at application startup from `prepare.py`.

## MCP Integration

- **Client** (`mcp_handler.py`): Connects to external MCP servers via stdio, SSE, or streamable HTTP. Handles tool discovery and execution. Supports both local (stdio) and remote (SSE/HTTP) servers.
- **Server** (`mcp_server.py`): Exposes Agent Zero as a FastMCP server with `send_message` tool. Other agents/clients can talk to Agent Zero via MCP protocol.
- **API endpoints**: `mcp_servers_status`, `mcp_servers_apply`, `mcp_server_get_detail`, `mcp_server_get_log`.
- **A2A Protocol**: Agent-to-Agent communication via `fasta2a` — Agent Zero can act as both A2A server and client.

## Projects System

Git-based projects with clone authentication for public/private repositories. Each project gets:
- Isolated workspace directory
- Project-scoped memory and knowledge
- Project-specific secrets and MCP/A2A config
- Custom instructions

## Fork Changes vs Upstream

Key additions over [agent0ai/agent-zero](https://github.com/agent0ai/agent-zero):
- Cognee memory persistence on addon volume (env vars before import)
- Cognee startup initialization (`init_cognee()` in `prepare.py`, no runtime lazy init)
- Parallel multi-search via `asyncio.gather` with per-type timeouts
- Dashboard in-memory cache (60s TTL) with server-side pagination
- Optimized bulk delete (single scan per area instead of per ID)
- Auto re-import knowledge when Cognee DB is empty
- Task self-recovery (ERROR and stuck RUNNING states)
- Skill installation via `/skill-install` chat command
- Structured RFC 3339 logging
- Accurate token counting via `litellm.token_counter`
- Truncation detection and retry for LLM streams
- Metrics persistence across container restarts
- Home Assistant addon packaging

## Testing

- **Framework:** pytest + pytest-asyncio + pytest-mock + pytest-cov + pytest-timeout
- **Markers:** `integration` (real services), `slow` (>5s), `regression` (fixed bugs)
- **CI:** GitHub Actions on push to `main`/`develop`, runs `pytest tests/ -m "not integration"`
- **Dependencies in CI:** `requirements.txt` + `requirements2.txt` + `requirements.dev.txt`
- **Coverage:** ~76% line coverage, ~2400 tests
- **Structure:** mirrors `python/` — `tests/helpers/`, `tests/api/`, `tests/extensions/`, `tests/tools/`, `tests/integration/`

## Upstream Sync

- Remote: `upstream` → `https://github.com/agent0ai/agent-zero.git`
- Merge upstream changes carefully — fork diverges in memory, MCP, and addon areas
- Upstream version: v0.9.8 (Skills, UI Redesign, Git projects)
