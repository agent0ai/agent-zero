# Terminal Agent Adapters - AGENTS.md

## Purpose

- Represent each supported external terminal agent as status/auth metadata for the plugin UI and APIs.
- Keep every adapter compatible with the shared `TerminalAgentAdapter` contract.

## Ownership

- Owns `base.py` plus adapter modules for A0 Headless, Codex CLI, Claude Code, Cursor CLI, Gemini CLI, Grok Build, Hermes Agent, OpenCode, and future status adapters.
- Owns credential-path detection and safe disconnect behavior only when the adapter can identify the exact credential store.

## Local Contracts

- Subclasses must define `id`, `title`, `binary`, `install_hint`, `description`, and `auth_status()`.
- `auth_status()` returns a dict containing at least `connected`, `mode`, and `auth_path`; optional `error` must be display-safe.
- `install_hint` is informational. It must not become executable API behavior.
- `resolve_binary()` should respect configured absolute paths and fall back to the adapter's default binary.
- `is_installed()` checks executability only. It must not install, mutate, or prompt.
- Do not add command execution hooks such as `build_command`, `install_command`, `parse_session_id`, or `format_output`.
- `data_dir()` is only for plugin-owned private state such as Codex device-login auth. Do not store user-entered provider keys in source or broad config files.

## Work Guidance

- A0 Headless:
  - Host resolution is config `a0.host`, then `AGENT_ZERO_HOST`, then `http://localhost:80` inside the Agent Zero container.
  - The Docker fallback binary is `/opt/venv/bin/a0` when plain `a0` is unavailable.
  - Status means the host socket is reachable; login/target choice is handled by the skill.
- Codex CLI:
  - Detect plugin-owned `data/codex/auth.json` before external `CODEX_HOME` or `~/.codex/auth.json`.
  - Keep device-code OAuth compatible with the Agent Zero `_oauth` reference.
  - External disconnect may call `codex logout`; plugin-owned disconnect deletes only the plugin auth file.
- Claude Code:
  - Treat `ANTHROPIC_API_KEY` as environment auth.
  - Detect the CLI credentials file but never read or return credential contents.
  - Do not model the first-run TUI as a status API flow.
- Cursor CLI:
  - Treat `CURSOR_API_KEY` as environment auth.
  - Detect known files under `~/.cursor/` without returning secret contents.
  - Do not model the interactive terminal UI as a status API flow.
- Grok Build:
  - Treat `XAI_API_KEY` as environment auth.
  - Detect `~/.grok/config.toml`, `~/.grok/auth.json`, and `~/.grok/auth/` without returning secret contents.
  - Do not model the full-screen TUI as a status API flow.
- Gemini CLI:
  - Detect `GEMINI_API_KEY`, `GOOGLE_API_KEY`, service-account/ADC files, and current or legacy Gemini credential files without returning secret contents.
  - Do not model Gemini's interactive sign-in TUI as a status API flow.
- Hermes Agent and OpenCode:
  - Detect known provider environment variables and known auth files.
  - Secret detection should answer yes/no without returning secret values.

## Verification

- Run adapter tests:
  ```bash
  docker exec 8dc967046cda bash -lc 'cd /a0 && /opt/venv-a0/bin/python plugins/_orchestrator/tests/test_status_adapters.py'
  ```
- For syntax-only adapter edits:
  ```bash
  docker exec 8dc967046cda bash -lc 'cd /a0 && /opt/venv-a0/bin/python -m py_compile plugins/_orchestrator/helpers/adapters/*.py'
  ```

## Child DOX Index

This folder has no child DOX files.
