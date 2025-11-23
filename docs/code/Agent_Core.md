---
tags: [component, core, python]
---

# Agent Core

The `Agent` class in `agent.py` is the heart of the system.

## Responsibilities

1.  **Message Loop**: Manages the conversation loop (`monologue` method).
2.  **Context Management**: Handles `AgentContext` and `LoopData`.
3.  **LLM Interaction**: Calls `models.py` to generate responses.
4.  **Tool Execution**: Dispatches tool calls via [[Code Execution]] and others.
5.  **Extension Hooks**: Calls [[Extensions]] at various points.

## Key Classes

- `Agent`: The main class.
- `AgentContext`: Maintains state, logs, and configuration.
- `LoopData`: Holds transient data for the current execution loop.

## Relations

- Uses [[Prompts System]] to construct system prompts.
- Uses [[Memory System]] to retrieve context.
- Delegates to [[Tools]] for actions.
- Interacts with [[Web UI]] via logs and `PrintStyle`.

