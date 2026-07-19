# Orchestrator Helpers - AGENTS.md

## Purpose

- Provide the status adapter framework and registry for terminal/headless coding agents.
- Keep adapter logic focused on discovery, configuration, authentication state, and safe credential cleanup.

## Ownership

- Owns `registry.py`, package initialization, and the `adapters/` subtree.
- Does not own shell command execution, long-running process management, or task output parsing.

## Local Contracts

- `registry.py` is the only place that orders and exposes registered adapters.
- A0 Headless must remain first in `list_adapters()` unless product direction changes.
- Registry imports must use `plugins._orchestrator...` for bundled plugin imports.
- `adapter_config()` must tolerate missing or malformed plugin config and return an empty dict.
- Add adapters by creating a `TerminalAgentAdapter` subclass, registering an instance in `registry.py`, adding defaults in `default_config.yaml`, and updating the skill, README, and tests.

## Work Guidance

- Keep helpers boring and inspectable. If command orchestration is needed, put instructions in the skill rather than adding a runner.
- Adapter metadata should be readable enough for both the UI and agent skill documentation to stay in sync.

## Verification

- Run the adapter contract checks:
  ```bash
  docker exec 8dc967046cda bash -lc 'cd /a0 && /opt/venv-a0/bin/python plugins/_orchestrator/tests/test_status_adapters.py'
  ```

## Child DOX Index

| Child | Scope |
| --- | --- |
| [adapters/AGENTS.md](adapters/AGENTS.md) | Per-agent adapter contracts, auth detection, and safe disconnect rules. |
