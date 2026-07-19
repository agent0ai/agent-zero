# Terminal Agent References - AGENTS.md

## Purpose

- Own per-agent command references for the `orchestrator` skill.
- Keep `SKILL.md` generic while preserving exact install, auth, smoke, and run commands for each supported terminal agent.

## Ownership

- Owns one markdown file per agent id, currently `a0.md`, `codex.md`, `claude.md`, `cursor.md`, `gemini.md`, `grok.md`, `hermes.md`, and `opencode.md`.
- Does not own adapter status code, settings UI, or global orchestration rules.

## Local Contracts

- Each reference must include when to use the agent, install/probe commands, auth/setup behavior, smoke command, and real-task command shape.
- Generic rules such as no bare CLI fallback, no secrets in chat, explicit workdir, and smoke-before-real stay in parent `SKILL.md`.
- Reference filenames must match adapter ids where possible.
- When adding a reference, update the parent `SKILL.md` reference index, README adding-agent steps, and tests.

## Work Guidance

- Keep each file operational and short. The agent should be able to copy the command block safely.
- Redact or avoid secrets; use environment variables and Agent Zero secret paths without printing values.

## Verification

- Run:
  ```bash
  docker exec 8dc967046cda bash -lc 'cd /a0 && /opt/venv-a0/bin/python plugins/_orchestrator/tests/test_status_adapters.py'
  ```

## Child DOX Index

This folder has no child DOX files.
