# Tool Access Plugin DOX

## Purpose

- Own the always-enabled project/profile tool-policy configuration and execution gate.

## Ownership

- `helpers/tool_policy.py` owns shared resolution and catalog behavior.
- `hooks.py` normalizes scoped configuration.
- `extensions/python/tool_execute_before/` rejects blocked execution.

## Local Contracts

- This plugin has no independent settings UI; the Agent Editor writes sparse
  profile `config.json` files, projects may own project or project-profile
  configs through the standard plugin scope paths, and the runtime remains
  authoritative.
- Required final-response capability is never disabled.

## Verification

- Run `tests/test_tool_policy.py`.

## Child DOX Index

No child DOX files.
