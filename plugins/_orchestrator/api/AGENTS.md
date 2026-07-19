# Orchestrator API - AGENTS.md

## Purpose

- Expose small plugin HTTP handlers used by the Orchestrator settings screen.
- Report registered adapter status and manage only supported, safe auth operations.

## Ownership

- Owns `status.py`, `start_device_login.py`, `poll_device_login.py`, `disconnect.py`, and package initialization for plugin APIs.
- Does not own execution of terminal agents, installation of CLIs, or generic credential collection.

## Local Contracts

- API handlers derive from `helpers.api.ApiHandler`.
- Read plugin settings through `helpers.plugins.get_plugin_config("_orchestrator")`.
- Use `plugins._orchestrator.helpers.registry` for adapter lookup and per-adapter config extraction.
- Return JSON dictionaries with `ok` and enough context for the WebUI to show a useful error. Do not let adapter exceptions escape to the user as framework failures.
- `status` may include `install_hint` for display/help only; it must not trigger installation.
- Device-login endpoints must reject adapters that do not explicitly support device login.
- `disconnect` may remove only known credential stores or invoke a known safe CLI logout. It must not delete broad home directories or provider config trees.

## Work Guidance

- Keep response shapes stable for `webui/orchestrator-store.js`.
- When adding adapter auth behavior, update `status.py` only if the shared response needs a new field.
- Never return token values, API keys, refresh tokens, or raw credential JSON.

## Verification

- Run the plugin self-check after API changes:
  ```bash
  docker exec 8dc967046cda bash -lc 'cd /a0 && /opt/venv-a0/bin/python plugins/_orchestrator/tests/test_status_adapters.py'
  ```
- For import-only API changes, use the Agent Zero framework runtime:
  ```bash
  docker exec 8dc967046cda bash -lc 'cd /a0 && /opt/venv-a0/bin/python -m py_compile plugins/_orchestrator/api/*.py'
  ```

## Child DOX Index

This folder has no child DOX files.
