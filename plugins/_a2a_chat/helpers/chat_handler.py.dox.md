# chat_handler.py DOX

## Purpose

- Handle calls declared by the `a2a-chat` skill, send messages to an A2A peer, and extract its reply.

## Ownership

- `A2AChatTool` owns the conversation cache, remote dispatch, and logging for `a2a_chat`. The plugin's skill registration constructs it when the loaded skill is allowed.

## Runtime Contracts

- Cache peer context IDs in `agent.data["_a2a_sessions"]`. Root and explicit `/a2a` URLs share a cache key. An explicit reset starts a fresh remote conversation.
- Extract the latest assistant history text before considering status text and artifacts. Use framework prompts for failures.

## Work Guidance

- Keep tool output concise, model-readable, and safe for history persistence.
- Coordinate argument changes with the skill declaration.
- Respect intervention flow for long-running, external, or user-visible operations.

## Verification

- Run `tests/test_a2a_chat_tool.py` and `tests/test_tool_action_contracts.py`.

## Child DOX Index

No child DOX files.
