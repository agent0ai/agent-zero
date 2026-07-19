# Orchestrator Skills - AGENTS.md

## Purpose

- Own the plugin's load-on-demand skill collection.
- Keep external-agent orchestration instructions available only when the user asks for terminal/headless agent delegation.

## Ownership

- Owns skill folders under `skills/`, currently `orchestrator/`.
- Does not own Python adapter code, settings UI, or credential storage.

## Local Contracts

- Skills must use Agent Zero's ordinary shell/code execution tools, either container `code_execution_tool` or A0 Connector `code_execution_remote`, not a plugin-specific terminal agent tool.
- Skill instructions plus their local reference files must be self-contained enough for the agent to run install checks, login/setup, smoke prompts, real tasks, and verification.
- Generic orchestration belongs in `SKILL.md`; per-agent details belong in the nearest `references/` file.
- Non-A0 agents first choose host-vs-container execution. Unknown preferences must be asked once and saved with memory when available.
- Host-machine agents use A0 CLI remote execution; container agents use the human-in-the-loop setup loop.
- A0 Headless remains the setup exception and must ask for same-instance vs another/spun-up instance when the target is ambiguous.
- The skill must instruct agents not to paste or request secrets in chat when safer browser/device/login-prompt paths exist.
- The skill must instruct agents not to use Computer Use to operate coding-agent terminals or TUIs.

## Work Guidance

- Keep the SKILL.md text operational, not encyclopedic.
- Add or update per-agent reference files when CLI-specific commands or auth behavior change.
- When CLI flags change, update the exact command blocks and the regression tests that assert important phrases.
- If a loaded chat keeps old behavior, start a fresh chat or reload `orchestrator`.

## Verification

- Run the skill text contract test:
  ```bash
  docker exec 8dc967046cda bash -lc 'cd /a0 && /opt/venv-a0/bin/python plugins/_orchestrator/tests/test_status_adapters.py'
  ```

## Child DOX Index

| Child | Scope |
| --- | --- |
| [orchestrator/AGENTS.md](orchestrator/AGENTS.md) | The `orchestrator` skill manifest and delegation workflow body. |
