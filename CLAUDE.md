# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Agent Zero is a personal organic agentic AI framework (Python backend, Alpine.js frontend). Fork of `jrmatherly/agent-zero`, remote at `jrmatherly/agent-zero`.

## Commands

All tooling is managed by **mise** (`mise.toml`). Use `mise run <task>` for everything.

```bash
mise run r                 # Start UI server (alias for run)
mise run t                 # Run tests (alias for test)
mise run lint              # Lint all (Ruff + Biome)
mise run lint:python       # Lint Python only
mise run lint:css          # Lint CSS only
mise run format:check      # Check formatting (CI mode)
mise run format            # Auto-format all
mise run ci                # Full CI: lint + format check + test
mise run setup             # First-time: deps + playwright + hooks
mise run install           # Install Python deps (uv sync)
mise run hooks:check       # Run hk pre-commit checks manually
mise run deps:add <pkg>    # Add dependency + regenerate requirements.txt
```

Single test: `uv run pytest tests/test_websocket_manager.py -v`

Tests use `pytest-asyncio` with `asyncio_mode = "auto"` — async test functions are auto-detected.

## Architecture

**Entry point**: `run_ui.py` → Flask + uvicorn (ASGI) + python-socketio

**Core loop** (`agent.py`): The Agent operates in a monologue loop — build prompt → call LLM → parse JSON → execute tool → repeat. Loop ends when the `response` tool is called.

**Auto-discovery pattern**: Tools (`python/tools/`), API handlers (`python/api/`), and WebSocket handlers (`python/websocket_handlers/`) are auto-loaded by scanning their directories. Drop a file in, it's active.

**Extension system** (`python/extensions/`): 24 lifecycle hook directories (e.g., `message_loop_start/`, `tool_execute_before/`). Extensions are sorted by filename prefix (`_10_`, `_20_`). User overrides go in `usr/extensions/` with the same filename.

**Models** (`models.py`): LiteLLM multi-provider config. Four model types: chat, utility, embedding, browser. Configured via UI settings → `initialize.py` → `AgentConfig`.

**Prompts** (`prompts/`): Markdown templates with `{{ include }}` for composition and `{{variable}}` for substitution.

**Memory**: FAISS vector DB with sentence-transformers embeddings. Used by `memory_save`/`memory_load` tools and recall extensions.

## Conventions

- **Python**: `snake_case` functions, `PascalCase` classes, `str | None` unions (not `Optional`)
- **New tool**: Extend `Tool` in `python/tools/`, implement `async execute(**kwargs) -> Response`
- **New API endpoint**: Extend `ApiHandler` in `python/api/`, implement `async process(input, request) -> dict`
- **New extension**: Extend `Extension` in the appropriate `python/extensions/<hook>/` dir, prefix-sorted filename
- **Disabled files**: `._py` suffix = archived/disabled
- **Commits**: Conventional Commits enforced by hk hook (`feat:`, `fix:`, `refactor:`, `chore:`, `docs:`, `test:`, `ci:`, `style:`, `perf:`, `security:`)

## Dependencies

- **Source of truth**: `pyproject.toml` (managed by uv)
- **Lockfile**: `uv.lock` (committed)
- **Docker compat**: `requirements.txt` — auto-generated, never edit manually
- **Add a dep**: `mise run deps:add <pkg>` (adds to pyproject.toml + regenerates requirements.txt)
- **Version override**: `[tool.uv] override-dependencies` in pyproject.toml for conflict resolution

## CI/CD

Four GitHub Actions workflows in `.github/workflows/`:
- **ci.yml**: Lint + format check + test (parallel jobs) on push/PR to main
- **drift.yml**: DriftDetect codebase analysis on source changes, manual dispatch, weekly
- **release.yml**: git-cliff changelog + GitHub release on `v*` tag push
- **hooks-check.yml**: hk validation on PRs to main

All CI workflows use `jdx/mise-action@v3` as the single tool installer.

## DriftDetect

`.drift/` contains codebase pattern analysis artifacts. The `patterns/approved/` directory and config are committed; `memory/`, `cache/`, `lake/`, `history/` are gitignored. Run `mise run drift:scan` to analyze, `mise run drift:gate` for quality gates.
