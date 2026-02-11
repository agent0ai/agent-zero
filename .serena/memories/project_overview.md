# Agent Zero - Project Overview

## Purpose
Agent Zero is a personal, organic agentic AI framework that grows and learns with the user. It is a general-purpose AI assistant that uses the computer as a tool—writing code, executing terminal commands, browsing the web, managing memory, and cooperating with subordinate agent instances.

## Tech Stack
- **Language**: Python 3.12+ (backend), vanilla JS + Alpine.js (frontend)
- **Web Framework**: Flask (sync routes) + uvicorn (ASGI) + python-socketio (WebSocket)
- **LLM Integration**: LiteLLM (multi-provider), LangChain Core
- **Embeddings**: sentence-transformers, FAISS (vector DB)
- **Browser Automation**: Playwright, browser-use
- **Search**: DuckDuckGo, SearXNG, Perplexity
- **Document Processing**: unstructured, pypdf, pymupdf, newspaper3k
- **MCP**: fastmcp for server, mcp SDK for client
- **Scheduling**: crontab
- **Docker**: Custom base image + DockerfileLocal for local dev
- **Testing**: pytest, pytest-asyncio, pytest-mock

## Development Tooling
- **Task runner**: mise (`mise.toml`, 67 tasks) — manages Python, uv, ruff, biome, git-cliff, pkl, hk
- **Package manager**: uv (`pyproject.toml` source of truth, `uv.lock` committed)
- **Python linter/formatter**: Ruff (configured in `pyproject.toml`)
- **CSS/JS linter**: Biome (configured in `biome.json`)
- **Git hooks**: hk (`hk.pkl`) — pre-commit (ruff, biome, security, hygiene), commit-msg (conventional commits)
- **Changelog**: git-cliff (`cliff.toml`) — conventional commit parsing, Keep a Changelog format
- **Codebase analysis**: DriftDetect (`driftdetect@0.9.48`) — pattern scanning, Python analysis, Cortex memory, quality gates
- **CI/CD**: GitHub Actions (4 workflows: ci, drift, release, hooks-check)

## Architecture
- `agent.py` — Core Agent and AgentContext classes
- `models.py` — LLM model configuration using LiteLLM
- `initialize.py` — Agent initialization and config management
- `run_ui.py` — Flask/uvicorn web server entry point
- `python/tools/` — 19 agent tools (code execution, memory, search, browser, etc.)
- `python/helpers/` — 83 utility modules (files, docker, SSH, memory, MCP, etc.)
- `python/api/` — ~75 REST API endpoint handlers (auto-discovered from folder)
- `python/websocket_handlers/` — 4 WebSocket event handlers (namespace-based discovery)
- `python/extensions/` — 41 extensions across 24 lifecycle hook points
- `prompts/` — ~100 system prompts and message templates (Markdown/Python)
- `webui/` — Frontend HTML/CSS/JS (Alpine.js + vanilla JS)
- `knowledge/` — Knowledge base files for RAG
- `skills/` — SKILL.md standard skills (portable agent capabilities)
- `tests/` — 28 pytest test files
- `docker/` — Docker build scripts (base image + run scripts)
- `docs/` — 21 documentation files (includes reference/environment-variables.md)
- `conf/` — Runtime configuration (model_providers.yaml)
- `docs/reference/` — Reference documentation (environment-variables.md)
- `.drift/` — DriftDetect analysis artifacts (patterns, indexes, views, audit)
- `.github/workflows/` — CI/CD workflows

## Key Design Patterns
- **Extension system**: Lifecycle hooks in `python/extensions/` directories (e.g., `message_loop_start`, `tool_execute_before`)
- **Auto-discovery**: Tools, API handlers, and WebSocket handlers are auto-loaded from their folders
- **Multi-agent**: Agents can spawn subordinate agents; the first agent's superior is the human user
- **Memory**: Persistent vector-DB-based memory with FAISS
- **Prompt-driven**: Behavior is defined by prompts in `prompts/` folder, fully customizable

## GitHub
- **Remote**: `jrmatherly/agent-zero` (fork of `agent0ai/agent-zero`)
- **Container Registry**: GHCR (`ghcr.io/jrmatherly/agent-zero`, `ghcr.io/jrmatherly/agent-zero-base`)
- **CI/CD Workflows**:
  - `ci.yml` — Lint (Ruff + Biome), format check, test (parallel jobs on push/PR to main)
  - `drift.yml` — Codebase pattern analysis (push to main, manual dispatch, weekly)
  - `release.yml` — git-cliff changelog + GitHub release on `v*` tag push
  - `hooks-check.yml` — hk pre-commit validation on PRs
