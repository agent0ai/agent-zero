# Apollos AI - Project Overview

## Purpose
Apollos AI is a personal, organic agentic AI framework that grows and learns with the user. It is a general-purpose AI assistant that uses the computer as a tool—writing code, executing terminal commands, browsing the web, managing memory, and cooperating with subordinate agent instances.

## Tech Stack
- **Language**: Python 3.12+ (backend), vanilla JS + Alpine.js (frontend)
- **Web Framework**: Flask (sync routes) + uvicorn (ASGI) + python-socketio (WebSocket)
- **LLM Integration**: LiteLLM (multi-provider), LangChain Core
- **Embeddings**: sentence-transformers (local default), FAISS (vector DB), LiteLLM (remote providers)
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
- **CI/CD**: GitHub Actions (6 workflows: ci, drift, release, hooks-check, codeql, dependency-review) + Dependabot (uv + github-actions)

## Architecture
- `agent.py` — Core Agent and AgentContext classes
- `models.py` — LLM model configuration using LiteLLM
- `initialize.py` — Agent initialization and config management
- `run_ui.py` — Flask/uvicorn web server entry point
- `python/tools/` — 19 agent tools (code execution, memory, search, browser, etc.)
- `python/helpers/` — 84 utility modules (files, docker, SSH, memory, MCP, branding, etc.)
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
- **Memory**: Persistent vector-DB-based memory with FAISS (configurable embeddings: local or remote via LiteLLM)
- **Branding**: Centralized `python/helpers/branding.py` with 4 env vars; frontend Alpine.js store; prompt `{{brand_name}}` injection
- **Prompt-driven**: Behavior is defined by prompts in `prompts/` folder, fully customizable

## GitHub
- **Remote**: `jrmatherly/apollos-ai` (fork of `agent0ai/agent-zero`)
- **Container Registry**: GHCR (`ghcr.io/jrmatherly/apollos-ai`, `ghcr.io/jrmatherly/apollos-ai-base`)
- **CI/CD Workflows**:
  - `ci.yml` — Lint + format + test (parallel jobs); paths-ignore, concurrency, uv cache
  - `drift.yml` — Codebase pattern analysis (push to main, manual dispatch, weekly)
  - `release.yml` — git-cliff changelog + GitHub release on `v*` tag push
  - `hooks-check.yml` — hk pre-commit validation on PRs
  - `codeql.yml` — CodeQL security analysis (Python) on push/PR + weekly
  - `dependency-review.yml` — Dependency review + requirements.txt sync on PRs
  - `dependabot.yml` — Weekly uv + GitHub Actions dependency updates
  - Issue templates (YAML forms), PR template
