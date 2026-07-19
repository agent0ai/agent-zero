# Agent Zero DOX

## Purpose

- Own project-wide engineering rules and the top-level DOX index.
- Keep detailed contracts in the closest applicable child `AGENTS.md`.

## Project

- Stack: Python 3.12+ framework, Python 3.13 agent execution runtime, Flask, Alpine.js, LiteLLM, and Socket.IO.
- Start the WebUI with `python run_ui.py`; discover its URL from startup output, Docker mappings, or explicit configuration rather than assuming a port.
- Run the full test suite with `pytest` or a focused file with `pytest tests/test_name.py`.
- Human-facing documentation lives in `README.md` and `docs/`.

## Root Ownership

- `agent.py` owns `Agent`, `AgentContext`, and loop data.
- `initialize.py` owns framework initialization.
- `models.py` owns model-provider configuration and LiteLLM integration.
- `run_ui.py` is the WebUI entry point.
- `DockerfileLocal` must remain compatible with the contracts under `docker/`.
- Runtime or user state under `usr/` and `tmp/` is intentionally outside tracked DOX unless the user explicitly asks otherwise.

## Project-Wide Contracts

- Import `AgentContext` and `AgentContextType` from `agent`, not `helpers.context`.
- Never commit secrets, `.env` files, API keys, tokens, or private user data.
- Preserve authentication and CSRF protections.
- Use Linux paths and commands in examples.
- When a live Dockerized Agent Zero target is explicitly named, verify that exact runtime instead of assuming a fixed localhost port.
- Copy live core-plugin changes back into tracked source under `plugins/`.
- Develop new custom plugins under ignored `usr/plugins/`; tracked bundled plugins live under `plugins/`.
- Use the framework runtime for backend and plugin-hook verification, not the separate agent execution runtime.

## Permissions

Allowed without asking:

- Read repository files.
- Update files under `usr/`.

Ask before:

- Installing dependencies.
- Deleting core files outside `usr/` or `tmp/`.
- Modifying `agent.py` or `initialize.py`.
- Creating commits or pushing branches.

## DOX Workflow

- `AGENTS.md` files are binding contracts for their subtrees.
- Before editing, read this file and every `AGENTS.md` on the path to each target; the closest contract controls local details without weakening parent rules.
- Keep work understandable from the applicable DOX chain. Put project-wide rules here and concrete ownership, workflows, inputs, outputs, side effects, and verification in child docs.
- Create a child `AGENTS.md` only for a durable boundary with distinct ownership or workflow.
- Child docs should use: Purpose, Ownership, Local Contracts, Work Guidance, Verification, and Child DOX Index.
- After every meaningful change, re-check the affected paths, update the closest owning docs and indexes, remove stale guidance, and run relevant verification.
- Do not document ignored `usr/` or `tmp/` changes unless explicitly requested.
- Keep DOX concise, current, operational, and free of diary entries or duplicated parent guidance.

## Child DOX Index

| Child | Scope |
| --- | --- |
| [.github/AGENTS.md](.github/AGENTS.md) | GitHub Actions workflows and release automation scripts. |
| [agents/AGENTS.md](agents/AGENTS.md) | Bundled agent profiles, profile-local prompts, and tools. |
| [api/AGENTS.md](api/AGENTS.md) | HTTP API and WebSocket handler entry points. |
| [conf/AGENTS.md](conf/AGENTS.md) | Repository-shipped configuration defaults and templates. |
| [docker/AGENTS.md](docker/AGENTS.md) | Docker build contexts, images, compose files, and runtime layout. |
| [docs/AGENTS.md](docs/AGENTS.md) | Human-facing documentation and screenshots. |
| [extensions/AGENTS.md](extensions/AGENTS.md) | Backend and WebUI lifecycle extensions. |
| [helpers/AGENTS.md](helpers/AGENTS.md) | Shared backend utilities and runtime services. |
| [knowledge/AGENTS.md](knowledge/AGENTS.md) | Built-in agent self-knowledge. |
| [lib/AGENTS.md](lib/AGENTS.md) | Lightweight browser-side helpers outside the WebUI bundle. |
| [plugins/AGENTS.md](plugins/AGENTS.md) | Bundled system plugins and custom-plugin architecture. |
| [prompts/AGENTS.md](prompts/AGENTS.md) | Core prompt templates. |
| [scripts/AGENTS.md](scripts/AGENTS.md) | Repository maintenance scripts and automation inputs. |
| [skills/AGENTS.md](skills/AGENTS.md) | Bundled Agent Zero skills. |
| [tests/AGENTS.md](tests/AGENTS.md) | Pytest regression and contract tests. |
| [tools/AGENTS.md](tools/AGENTS.md) | Core agent tool implementations. |
| [webui/AGENTS.md](webui/AGENTS.md) | Alpine.js WebUI shell, components, JavaScript, CSS, and assets. |

Intentionally unindexed local or generated roots:

| Path | Reason |
| --- | --- |
| `.conda/`, `.venv/` | Local Python environments. |
| `.pytest_cache/`, `__pycache__/` | Generated test and bytecode caches. |
| `.vscode/`, `.windsurf/` | Editor-local configuration and assistant metadata. |
| `tmp/` | Ignored runtime caches, uploads, and generated work. |
| `usr/` | Ignored local user data, settings, plugins, chats, and workdirs. |
| `python/` | Generated or legacy runtime mirror; current source is in root modules and tracked source directories. |
