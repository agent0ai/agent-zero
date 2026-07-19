# Orchestrator WebUI - AGENTS.md

## Purpose

- Provide the Settings > External Services configuration screen for Orchestrator.
- Show command defaults, detailed auth state, Codex device login, and safe disconnect actions.

## Ownership

- Owns `config.html` and `orchestrator-store.js`.
- Does not own core settings components, global OAuth UI, or terminal execution.

## Local Contracts

- Use the Agent Zero plugin settings modal pattern: local `config`, `$store.pluginSettingsPrototype`, and a gated Alpine store.
- Register the Alpine store with `createStore("orchestratorStore", ...)`.
- Use `callJsonApi()` for plugin API calls and A0 notification toasts for errors/info/success.
- Refresh is a compact icon action consistent with Agent Zero settings UI.
- Summary cards do not render connected/needs-login/not-installed pills; detailed auth state belongs inside the expanded card.
- Only show `Connect` for adapters with `supports_device_login`; currently that is Codex.
- Only show `Disconnect` when the API says `can_disconnect`.
- Never render secret values. Auth text may show source type or credential path only when it is safe and already adapter-provided.

## Work Guidance

- Keep each agent row readable before expansion: title, id, description, action buttons, expand icon.
- Put detailed fields inside the expanded panel and prefer a simple two-column grid that collapses to one column on mobile.
- If a new config field is added in the UI, add a default in `default_config.yaml` and align README/skill guidance when relevant.
- Browser-test visual changes in the live settings modal when possible.

## Verification

- JavaScript syntax:
  ```bash
  node --check plugins/_orchestrator/webui/orchestrator-store.js
  ```
- Status API smoke after WebUI/API coupling changes:
  ```bash
  docker exec 8dc967046cda bash -lc 'cd /a0 && /opt/venv-a0/bin/python plugins/_orchestrator/tests/test_status_adapters.py'
  ```

## Child DOX Index

This folder has no child DOX files.
