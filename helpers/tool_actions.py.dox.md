# tool_actions.py DOX

## Purpose

- Own the finite action contracts for bundled tools used by permission enforcement, Agent Editor, and model discovery.

## Ownership

- `BUNDLED_ACTIONS` records canonical actions, selector arguments, defaults, and equivalent aliases. It contains no tool imports or model calls.
- `action_policy_id` appends `:<action>` to the canonical tool ID; memory retains its four existing `memory_<action>` IDs.
- `requested_actions` resolves actual call arguments, including browser batch members, execution reset flags, and parallel start/wait/collect behavior.

## Local Contracts

- Apply a contract only to its resolved bundled implementation path. Profile/custom tools and MCP tools keep their own contracts and whole-tool policies.
- Canonical actions and aliases must match the owning tool's dispatch. Update this registry and its tests when changing a bundled tool's actions.
- Check every operation in a compound call before execution. Parallel workers also enforce each nested tool's policy independently.
- These controls govern tool operations, not all effects reachable through other capabilities. Shell execution, browser JavaScript, and computer input retain their existing authority when allowed.

## Verification

- Run `tests/test_tool_action_policy.py`, `tests/test_tool_policy.py`, tool action contract tests, and the affected tool's tests.
