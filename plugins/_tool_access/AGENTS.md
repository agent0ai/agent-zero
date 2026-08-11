# Tool Access Plugin DOX

## Purpose

- Own the always-enabled project/profile tool-policy configuration and execution gate.

## Ownership

- `helpers/tool_policy.py` owns shared resolution and catalog behavior.
- `hooks.py` normalizes scoped configuration.
- `extensions/python/tool_execute_before/` rejects blocked execution.

## Local Contracts

- This plugin has no independent settings form; the generic plugin settings
  shell exposes its scoped configuration index, while Agent Editor writes
  sparse profile `config.json` files and the runtime remains authoritative.
- Custom configuration stores independent `default` and `mcp_default`
  fallbacks; explicit canonical IDs remain shared in `allowed` and `blocked`.
- Required final-response capability is never disabled.

## Verification

- Run `tests/test_tool_policy.py`.

## Child DOX Index

No child DOX files.
