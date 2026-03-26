# Infection Check

Safety middleware that analyzes agent output for prompt injection and suspicious external influence before allowing tool execution.

## What It Does

This plugin collects streamed reasoning and response text, analyzes that content with a configurable audit model, and blocks tool execution until the safety check either passes, requests clarification, or terminates the agent.

## How It Works

1. **Collection** — During streaming, the plugin collects the agent's reasoning and response text via `reasoning_stream_chunk` and `response_stream_chunk` extensions.
2. **Analysis** — A security audit model analyzes the collected text against the configurable prompt.
3. **Gate** — Before any tool executes, `gate()` blocks until the check completes. If the background task already finished (thoughts mode), the result is reused instantly. Otherwise the task is rebuilt with full tool context (name + arguments) for maximum accuracy.
4. **Action** — Based on the verdict:
   - `<ok/>` — Tool execution proceeds silently.
   - `<terminate/>` — Agent is stopped immediately with a warning log and desktop notification.
   - `<clarify>` — The agent is asked to explain; a back-and-forth loop runs until resolved.

## Modes

| Mode | What is Analyzed | When Analysis Starts | Latency |
|---|---|---|---|
| **thoughts** (default) | Reasoning + thoughts | When `heading` or `tool_name` appear in response stream | Low — runs in parallel while tool args still stream |
| **complete** | Reasoning + full response | After the entire response stream ends | Higher — blocking wait before tool execution |

## Clarification Loop

When the check model returns `<clarify>`:

1. A warning log item is displayed with the safety concern.
2. The conversation history is cloned and the clarification questions appended.
3. The **main** model responds (streamed into the UI log).
4. The response is fed back to the check model for re-evaluation.
5. Repeats up to **Max Clarifications** times; exceeding the limit triggers termination.

## Termination Behavior

When the check results in `<terminate/>` (directly or after exhausting clarifications):

1. A warning is logged with the full chain-of-thought.
2. The last AI message in history is replaced with `[BLOCKED]`.
3. A desktop notification is sent.
4. Queued messages are scheduled to resume after the current task stops (since the normal `process_chain_end` extension does not fire after `HandledException`).
5. `HandledException` is raised to stop the agent.

## Configuration

| Setting | Default | Description |
|---|---|---|
| Mode | `thoughts` | `thoughts` or `complete` |
| Model | `utility` | `utility` (faster/cheaper) or `main` (more capable) |
| Max Clarifications | `3` | Clarification rounds before auto-terminate |
| History Size | `10` | Recent messages included as context |
| Prompt | *(built-in)* | Fully customizable security audit system prompt |

## Key Files

- **Checker logic**
  - `helpers/checker.py` implements stream collection, background analysis, gating, clarification, and termination.
- **Extensions**
  - `extensions/python/reasoning_stream_chunk/_50_infection_collect.py`
  - `extensions/python/response_stream_chunk/_50_infection_collect.py`
  - `extensions/python/response_stream/_50_infection_analyze.py`
  - `extensions/python/response_stream_end/_50_infection_analyze.py`
  - `extensions/python/tool_execute_before/_50_infection_check.py`

## Extension Points Used

| Extension Point | File | Purpose |
|---|---|---|
| `reasoning_stream_chunk` | `_50_infection_collect.py` | Accumulate reasoning text |
| `response_stream_chunk` | `_50_infection_collect.py` | Accumulate response text |
| `response_stream` | `_50_infection_analyze.py` | Detect thoughts complete → start background analysis |
| `response_stream_end` | `_50_infection_analyze.py` | Start analysis (complete mode / fallback) |
| `tool_execute_before` | `_50_infection_check.py` | Await check result → gate tool execution |

## Configuration Scope

- **Settings section**: `agent`
- **Per-project config**: `true`
- **Per-agent config**: `true`

## Plugin Metadata

- **Name**: `_infection_check`
- **Title**: `Infection Check`
- **Description**: Safety check for prompt injection from external sources.
