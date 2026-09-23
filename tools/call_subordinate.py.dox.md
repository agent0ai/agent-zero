# call_subordinate.py DOX

## Purpose

- Own the `call_subordinate.py` agent tool.
- This module delegates work to a subordinate Agent Zero profile and returns its result.
- Keep this file-level DOX profile synchronized with `call_subordinate.py` because this directory is intentionally flat.

## Ownership

- `call_subordinate.py` owns the runtime implementation.
- `call_subordinate.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `Delegation` (`Tool`)
  - `async execute(self, message=..., reset=..., context_id=..., **kwargs)`
  - `get_log_object(self)`
- Top-level functions:
- `_subordinate_profile_labels(agent: Agent) -> dict[str, str]`
- `_validate_subordinate_profile(agent: Agent, profile: str) -> str`
- `_scoped_model_config_paths(*, project: str = "", profile: str = "") -> list[str]`
- `_read_scoped_preset(path: str) -> str`
- `explicit_scoped_preset(*, project: str = "", profile: str = "") -> str`
- `_has_explicit_scoped_preset(*, project: str = "", profile: str = "") -> bool`
- `get_or_create_subordinate(...) -> Agent`
- `run_subordinate(...) -> str`

## Runtime Contracts

- Tool modules must define `helpers.tool.Tool` subclasses and return `helpers.tool.Response` from `execute(...)`.
- Update this file whenever tool arguments, output shape, `break_loop` behavior, intervention handling, prompt instructions, or side effects change.
- `Delegation` is a `Tool`.
- `Delegation` defines `execute(...)`.
- Observed side-effect areas: filesystem writes, settings/state persistence.
- `profile`/`agent_profile` values are validated against available profile keys before use; unknown profiles raise `RepairableException` so the agent can retry with a real profile.
- Direct and parallel calls use the same creation, continuation, message, history, and persistence functions in this module.
- Every fresh child is `Agent(parent.number + 1, ...)` in its own persisted child-chat context, so sibling A1 agents can each create their own A2 descendants without sharing streaming state.
- `reset=true` creates a fresh child. `reset=false` continues the caller's default child or the exact child named by `context_id`.
- Child context IDs are accepted only when their persisted parent context, parent agent number, and child depth match the caller.
- Supplying a different profile for an existing child without creating a fresh child raises `RepairableException` instead of silently changing its profile.
- Active parallel children cannot be continued concurrently; await or cancel their job first.
- Child contexts inherit the caller's project, are saved before execution and again on exit, and remain reusable after model/API failures.
- A fresh child inherits the caller's `chat_model_override` only when its own scope (project or agent profile) does not select an explicit `model_preset`. An explicit scoped `model_preset` always wins; the global plugin preset never counts as an explicit scoped selection.
- Explicit scoped presets are read from the raw scoped `_model_config/config.json` files (project/profile, project, user profile, bundled profile) instead of `get_configured_preset_name`, which falls back to `Default` and cannot distinguish an unset selection from an explicit one.
- The direct tool result includes `context_id`; parallel job snapshots expose the same stable child ID separately from their per-invocation job ID.
- Existing same-context linear subordinates remain reusable for saved-chat compatibility, but new children use child contexts and a private per-parent registry.
- Imported dependency areas include: `agent`, `extensions.python.hist_add_tool_result`, `helpers`, `helpers.errors`, `helpers.tool`.

## Key Concepts

- Important called helpers/classes observed in the source: `AgentContext.all`, `projects.get_context_project_name`, `projects.activate_project`, `subagents.get_available_agents_dict`, `RepairableException`, `initialize_agent`, `message_queue.log_user_message`, `persist_chat.save_tmp_chat`, `UserMessage`, `subordinate.monologue`, and `subordinate.history.new_topic`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Keep tool output concise, model-readable, and safe for history persistence.
- Coordinate argument or behavior changes with prompt tool instructions and skill guidance.
- Respect intervention flow for long-running, external, or user-visible operations.

## Verification

- Run targeted tool and prompt-contract tests for changed behavior; smoke-test agent execution when no focused test exists.
- Related tests observed by source search:
  - `tests/test_default_prompt_budget.py`
  - `tests/test_subagent_profiles.py`
  - `tests/test_parallel_tool.py`

## Child DOX Index

No child DOX files.
