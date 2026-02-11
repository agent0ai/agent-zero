# Project Index: Apollos AI

Generated: 2026-02-11

## Project Overview

Personal organic agentic AI framework that grows and learns with the user.
Fork of [agent0ai/agent-zero](https://github.com/agent0ai/agent-zero), maintained at [jrmatherly/apollos-ai](https://github.com/jrmatherly/apollos-ai).

- **Language**: Python 3.12+ (backend), vanilla JS + Alpine.js (frontend)
- **Server**: Flask + uvicorn + python-socketio (ASGI)
- **LLM**: LiteLLM multi-provider (via LangChain wrappers)
- **Memory**: FAISS vector DB + sentence-transformers embeddings
- **License**: MIT

## Project Structure

```text
apollos-ai/
├── agent.py              # Core Agent class (monologue loop)
├── models.py             # LiteLLM multi-provider model config
├── initialize.py         # Agent initialization from settings
├── run_ui.py             # Main entry point (Flask+uvicorn+socketio)
├── preload.py            # Pre-initialization routines
├── prepare.py            # Environment preparation
├── run_tunnel.py         # Cloudflare tunnel management
├── pyproject.toml        # Dependencies & project config (uv)
├── uv.lock               # Reproducible dependency lockfile
├── mise.toml             # Task runner + tool manager (67 tasks)
├── hk.pkl                # Git hooks config (pre-commit, commit-msg)
├── cliff.toml            # Changelog generation (conventional commits)
├── biome.json            # CSS/JS linter config
├── .drift/               # DriftDetect codebase analysis artifacts
│   ├── config.json       # Drift project config
│   ├── manifest.json     # Analysis manifest
│   ├── patterns/approved/# 14 approved pattern categories
│   ├── indexes/          # Category + file indexes
│   ├── views/            # Status cache + pattern index
│   ├── audit/            # Quality audit snapshots
│   ├── dna/              # Codebase DNA profiles
│   └── error-handling/   # Error topology analysis
├── .github/workflows/    # CI/CD (ci, drift, release, hooks-check)
├── python/
│   ├── api/              # 74 REST endpoint handlers (ApiHandler)
│   ├── tools/            # 19 active tools (Tool subclasses)
│   ├── helpers/          # 83 utility modules
│   ├── extensions/       # 41 lifecycle hook extensions (26 hook points)
│   └── websocket_handlers/  # 4 namespace-based WS handlers
├── prompts/              # 102 prompt templates (99 .md + 3 .py)
├── webui/                # Frontend (59 JS + 94 HTML + 19 CSS)
│   ├── components/       # Alpine.js component stores + HTML
│   ├── js/               # Core JS utilities
│   ├── css/              # Stylesheets
│   └── vendor/           # Ace editor, Alpine.js, Socket.IO, etc.
├── agents/               # 6 agent profiles (default, apollos, developer, hacker, researcher, _example)
├── skills/               # Skill definitions (create-skill template)
├── knowledge/            # Knowledge base (main + solutions)
├── tests/                # 28 test files (pytest + pytest-asyncio)
├── docker/               # Docker build (base + run stages)
├── docs/                 # 20 documentation files
├── conf/                 # Runtime config (model_providers.yaml)
├── CLAUDE.md             # AI agent guidance
├── QUICKSTART.md         # Quickstart guide
└── STYLING-PLAYBOOK.md   # Drift DNA-generated styling guide
```

## Entry Points

- **UI Server**: `run_ui.py` — Flask + uvicorn + Socket.IO ASGI app
- **Tunnel**: `run_tunnel.py` — Cloudflare tunnel for remote access
- **Agent Core**: `agent.py` — Agent class with monologue loop
- **Init**: `initialize.py` — Agent config assembly from settings
- **Models**: `models.py` — LiteLLM model configuration (chat, utility, embedding, browser)

## Core Modules

### agent.py — Agent & AgentContext
- `Agent`: Monologue loop (prompt → LLM → parse JSON → tool exec → repeat)
- `AgentContext`: Thread-safe session lifecycle with locking
- Loop terminates when `response` tool is called

### models.py — Model Configuration
- `ModelConfig`: Dataclass for LiteLLM provider settings
- `ChatGenerationResult`: Streaming response processor
- Supports: chat, utility, embedding, browser model types

### initialize.py — Agent Initialization
- Builds agent config from UI settings
- Assembles model configs, runs migrations, initializes MCP

### run_ui.py — Server (560 lines)
- Flask app with ASGI (a2wsgi) + uvicorn
- Auto-discovers API handlers from `python/api/`
- Socket.IO namespace routing via `websocket_namespace_discovery`
- Auth: session + API key + CSRF + loopback-only modes
- Mounts: MCP server (`/mcp`), A2A server (`/.well-known/agent.json`)

## Tools (19 active)

| Tool | Purpose |
|------|---------|
| `code_execution_tool` | Execute code (Python, Node.js, terminal) in Docker sandbox |
| `call_subordinate` | Spawn sub-agents for delegated tasks |
| `response` | Return final response to user (ends loop) |
| `memory_save` | Save to FAISS vector memory |
| `memory_load` | Query FAISS vector memory |
| `memory_delete` | Delete specific memories |
| `memory_forget` | Bulk forget by criteria |
| `search_engine` | Web search (SearXNG/DuckDuckGo/Perplexity) |
| `browser_agent` | Browser automation (Playwright/browser-use) |
| `document_query` | Query uploaded documents |
| `input` | Request user input mid-task |
| `notify_user` | Send push/email notifications |
| `scheduler` | Cron-based task scheduling |
| `skills_tool` | Execute installed skills |
| `a2a_chat` | Agent-to-agent communication |
| `behaviour_adjustment` | Modify agent behavior dynamically |
| `vision_load` | Load images for vision analysis |
| `wait` | Pause execution |
| `unknown` | Fallback for unrecognized tool calls |

## API Handlers (74 endpoints)

Key endpoint groups:
- **Chat**: `message`, `message_async`, `chat_create`, `chat_load`, `chat_reset`, `chat_remove`, `chat_export`
- **Settings**: `settings_get`, `settings_set`
- **Memory**: `memory_dashboard`
- **Files**: `get_work_dir_files`, `upload_work_dir_files`, `edit_work_dir_file`, `delete_work_dir_file`, `download_work_dir_file`
- **MCP**: `mcp_servers_status`, `mcp_servers_apply`, `mcp_server_get_detail`, `mcp_server_get_log`
- **Scheduler**: `scheduler_tasks_list`, `scheduler_task_create/update/delete/run`, `scheduler_tick`
- **Backup**: `backup_create`, `backup_restore`, `backup_inspect`, `backup_test`
- **Knowledge**: `knowledge_reindex`, `knowledge_path_get`, `import_knowledge`
- **Skills**: `skills`, `skills_import`, `skills_import_preview`
- **Notifications**: `notification_create`, `notifications_history`, `notifications_mark_read`, `notifications_clear`
- **Auth**: `csrf_token`, `logout`
- **System**: `health`, `poll`, `restart`, `nudge`, `pause`, `rfc`, `banners`, `agents`, `subagents`

## Extension Lifecycle Hooks (26 points)

```text
agent_init → message_loop_start → message_loop_prompts_before →
message_loop_prompts_after → monologue_start → system_prompt →
before_main_llm_call → reasoning_stream → reasoning_stream_chunk →
reasoning_stream_end → response_stream → response_stream_chunk →
response_stream_end → tool_execute_before → tool_execute_after →
hist_add_before → hist_add_tool_result → monologue_end →
message_loop_end → process_chain_end → user_message_ui →
banners → error_format → util_model_call_before →
message_loop_prompts_before → message_loop_prompts_after
```

Extensions sorted by filename prefix (`_10_`, `_20_`, etc.) within each hook.
User overrides: `usr/extensions/` (same filename = override).

## Helpers (83 modules)

Key modules:
- **LLM**: `call_llm`, `rate_limiter`, `tokens`, `providers`
- **Memory**: `memory`, `vector_db`, `memory_consolidation`
- **Execution**: `process`, `shell_local`, `shell_ssh`, `docker`, `runtime`
- **Web**: `api`, `websocket`, `websocket_manager`, `websocket_namespace_discovery`
- **Browser**: `browser`, `browser_use`, `playwright`, `browser_use_monkeypatch`
- **Files**: `files`, `file_browser`, `file_tree`
- **Security**: `security`, `secrets`, `crypto`, `login`
- **State**: `context`, `history`, `messages`, `persist_chat`, `settings`
- **MCP**: `mcp_handler`, `mcp_server`
- **Other**: `notification`, `task_scheduler`, `skills`, `projects`, `backup`, `git`

## Development Tooling

### mise (Task Runner + Tool Manager)
- `mise.toml` — 67 tasks, manages Python 3.12, uv, ruff, biome, git-cliff, pkl, hk
- Common: `mise run r` (UI), `mise run t` (tests), `mise run lint`, `mise run ci`
- Drift: 38 `drift:*` tasks (scan, patterns, memory, quality gates)
- Deps: `mise run deps:add <pkg>` (adds + regenerates requirements.txt)

### Git Hooks (hk)
- `hk.pkl` — Pre-commit: Ruff lint, Biome CSS, security checks, hygiene
- Commit-msg: Conventional commit format enforcement

### Changelog (git-cliff)
- `cliff.toml` — Conventional commit parsing, Keep a Changelog format
- `mise run changelog` / `mise run changelog:latest`

### DriftDetect (Codebase Analysis)
- `.drift/` — Pattern scanning, Python analysis, Cortex memory, quality gates
- Installed via npm (`driftdetect@0.9.48`), supports Python via tree-sitter
- Key: `mise run drift:scan`, `drift:py`, `drift:memory`, `drift:check`, `drift:gate`

### CI/CD (GitHub Actions)
- `.github/workflows/ci.yml` — Lint (Ruff + Biome) + format check + test (parallel jobs)
- `.github/workflows/drift.yml` — Codebase analysis (push/manual/weekly)
- `.github/workflows/release.yml` — git-cliff changelog + GitHub release on `v*` tags
- `.github/workflows/hooks-check.yml` — hk validation on PRs

## Configuration

- `pyproject.toml` — All Python dependencies + project metadata (managed by uv)
- `uv.lock` — Reproducible lockfile (committed)
- `requirements.txt` — Auto-generated by `uv export` for Docker compatibility
- `conf/model_providers.yaml` — LLM provider model definitions
- `biome.json` — Biome CSS/JS linter settings
- `jsconfig.json` — JS path config
- `docker/run/docker-compose.yml` — Docker Compose config
- `docker/run/Dockerfile` / `docker/base/Dockerfile` — Multi-stage Docker build

## Documentation

- `docs/quickstart.md` — Getting started guide
- `docs/setup/installation.md` — Full installation instructions
- `docs/setup/dev-setup.md` — Developer environment setup
- `docs/setup/vps-deployment.md` — VPS deployment guide
- `docs/developer/architecture.md` — Architecture overview
- `docs/developer/extensions.md` — Extension system docs
- `docs/developer/websockets.md` — WebSocket documentation
- `docs/developer/mcp-configuration.md` — MCP server config
- `docs/developer/notifications.md` — Notification system
- `docs/developer/connectivity.md` — Connectivity docs
- `docs/developer/contributing-skills.md` — Skill development guide
- `docs/guides/usage.md` — Usage guide
- `docs/guides/projects.md` — Projects feature
- `docs/guides/mcp-setup.md` — MCP setup
- `docs/guides/a2a-setup.md` — Agent-to-Agent setup
- `docs/guides/api-integration.md` — API integration
- `docs/guides/troubleshooting.md` — Troubleshooting
- `docs/guides/contribution.md` — Contributing guide
- `docs/setup/dependency-management.md` — uv + pyproject.toml workflow

## Tests (28 files)

- WebSocket: 12 test files (namespace discovery, CSRF, handlers, manager, integration)
- State: 3 test files (monitor, sync, snapshot)
- Chat: 1 test (persist_chat_log_ids)
- Settings: 1 test (developer_sections)
- Auth: 1 test (http_auth_csrf)
- Config: 1 test (run_ui_config)
- Utilities: chunk_parser, email_parser, rate_limiter, file_tree, fasta2a_client
- Harness: websocket_namespace_test_utils (shared test utilities)

Run: `pytest tests/`

## Key Dependencies

| Package | Purpose |
|---------|---------|
| `flask[async]` 3.0.3 | Web framework |
| `uvicorn` >=0.38.0 | ASGI server |
| `python-socketio` >=5.14.2 | WebSocket support |
| `litellm` (via langchain) | Multi-provider LLM |
| `langchain-core` 0.3.49 | LLM abstractions |
| `faiss-cpu` 1.11.0 | Vector similarity search |
| `sentence-transformers` 3.0.1 | Text embeddings |
| `fastmcp` 2.13.1 | MCP server |
| `fasta2a` 0.5.0 | Agent-to-Agent protocol |
| `browser-use` 0.5.11 | Browser automation |
| `playwright` 1.52.0 | Browser control |
| `docker` 7.1.0 | Docker SDK |
| `pydantic` 2.11.7 | Data validation |
| `duckduckgo-search` 6.1.12 | Web search |
| `openai-whisper` 20250625 | Speech-to-text |
| `kokoro` >=0.9.2 | Text-to-speech |

## Agent Profiles

| Profile | Description |
|---------|-------------|
| `default` | Base agent with standard capabilities |
| `apollos` | Core Apollos AI personality |
| `developer` | Software development focused |
| `hacker` | Security/hacking oriented |
| `researcher` | Research and analysis focused |
| `_example` | Template for custom profiles |

## Quick Start

1. `mise install` — Install all tools (Python, uv, ruff, biome, etc.)
2. `mise run setup` — First-time setup (deps, playwright, hooks)
3. `mise run r` — Start UI server (or `python run_ui.py`)
4. Configure API keys in UI settings
5. `mise run t` — Run tests (or `uv run pytest tests/`)

## Conventions

- Python: `snake_case` functions, `PascalCase` classes, `str | None` unions
- Tools: extend `Tool`, implement `async execute(**kwargs) -> Response`
- API: extend `ApiHandler`, implement `async process(input, request) -> dict`
- Extensions: extend `Extension`, implement `async execute(**kwargs)`, prefix-sorted
- Disabled files: `._py` suffix
- Prompt templates: `{{ include }}` and `{{variable}}` syntax
- Commits: Conventional Commits format (enforced by hk commit-msg hook)
- GitHub remote: `jrmatherly/apollos-ai` (fork of `agent0ai/agent-zero`)
