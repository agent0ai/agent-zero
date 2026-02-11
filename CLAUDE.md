# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Agent Zero (branded as configurable via `BRAND_NAME` env var, default "Apollos AI") is a personal organic agentic AI framework (Python backend, Alpine.js frontend). Fork of `agent0ai/agent-zero`, remote at `jrmatherly/agent-zero`.

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

**Memory**: FAISS vector DB with configurable embeddings (default: sentence-transformers local; supports remote providers via LiteLLM). Used by `memory_save`/`memory_load` tools and recall extensions.

**Branding**: Centralized in `python/helpers/branding.py` with 4 env vars (`BRAND_NAME`, `BRAND_SLUG`, `BRAND_URL`, `BRAND_GITHUB_URL`). Frontend gets values via `/branding_get` API → Alpine.js store (`webui/js/branding-store.js`). Prompt templates use `{{brand_name}}` variable injection.

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

Six GitHub Actions workflows in `.github/workflows/`:
- **ci.yml**: Lint + format check + test (parallel jobs) on push/PR to main; paths-ignore skips docs-only changes; concurrency groups cancel stale runs; uv cache on test job
- **drift.yml**: DriftDetect codebase analysis on source changes, manual dispatch, weekly
- **release.yml**: git-cliff changelog + GitHub release on `v*` tag push
- **hooks-check.yml**: hk validation on PRs to main
- **codeql.yml**: CodeQL security analysis (Python) on push/PR to main + weekly schedule
- **dependency-review.yml**: Dependency vulnerability review + requirements.txt sync check on PRs

Additional GitHub configuration:
- **dependabot.yml**: Weekly automated dependency updates for uv (Python) and GitHub Actions
- **ISSUE_TEMPLATE/**: Structured bug report and feature request forms (YAML)
- **pull_request_template.md**: PR checklist template

All CI workflows use `jdx/mise-action@v3` for tool installation; security workflows use dedicated actions.

## Environment Variables

- **Reference**: `docs/reference/environment-variables.md` — complete catalog of all env vars
- **Example file**: `usr/.env.example` — annotated template (copy to `usr/.env`)
- **API keys**: `{PROVIDER}_API_KEY` pattern, matching provider IDs in `conf/model_providers.yaml`
- **Settings overrides**: `A0_SET_{setting_name}` prefix overrides any UI setting
- **Base URLs**: `{PROVIDER}_API_BASE` overrides YAML defaults

## DriftDetect

`.drift/` contains codebase pattern analysis artifacts. The `patterns/approved/` directory and config are committed; `memory/`, `cache/`, `lake/`, `history/` are gitignored. Run `mise run drift:scan` to analyze, `mise run drift:gate` for quality gates.
