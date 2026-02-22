# Prompt System

> **Navigation:** [Index](./index.md) | [Architecture](./architecture.md) | [Agent Profiles](./agent-profiles.md) | [Tools](./tools.md) | [Extensions](./extensions.md) | [Configuration](./configuration.md)

---

## Overview

Every agent behavior is controlled by markdown prompt files — there is no hard-coded personality or instruction logic. The system prompt is assembled fresh on every message loop iteration by composing multiple files via `{{ include }}` directives.

**Total files:** 104+ markdown template files in `prompts/` plus profile overrides in `agents/<profile>/prompts/`.

---

## Include Directives

The root template `prompts/agent.system.main.md` composes the full system prompt:

```markdown
# Agent Zero System Manual

{{ include "agent.system.main.role.md" }}

{{ include "agent.system.main.environment.md" }}

{{ include "agent.system.main.communication.md" }}

{{ include "agent.system.main.solving.md" }}

{{ include "agent.system.main.tips.md" }}
```

**Resolution order for every `{{ include "filename.md" }}`:**

```
1. agents/<active-profile>/prompts/filename.md   ← profile override wins
2. prompts/filename.md                           ← global default fallback
```

This means any prompt file can be overridden by a profile without touching the original file. The `hacker` profile overrides 4 of the 5 main files.

---

## Variable Injection

Templates support `{{variable_name}}` substitution. Variables come from `.py` files with matching names — e.g., `agent.system.tools.md` has `agent.system.tools.py` which dynamically builds the tools list at runtime.

Common variables:
- `{{date_time}}` — current date/time (injected by `_60_include_current_datetime.py`)
- `{{tools}}` — rendered tool documentation
- `{{number}}` — agent depth (0 = top-level)
- `{{profile}}` — active profile name
- `{{extras}}` — `loop_data.extras_temporary` contents
- `{{rules}}` — behaviour rules from memory
- `{{memories}}` — recalled memories
- `{{project_path}}`, `{{project_name}}` — active project info

---

## Profile Override Map

The hacker profile overrides these files in `agents/hacker/prompts/`:

| File | Status | Change |
|------|--------|--------|
| `agent.system.main.role.md` | Override | Full penetration tester identity, 7-phase methodology |
| `agent.system.main.environment.md` | Override | Kali toolchain tables, engagement workspace layout |
| `agent.system.main.solving.md` | New | Pentest engagement loop, delegation rules |
| `agent.system.main.communication.md` | New | Per-action/finding/summary output formats |
| `agent.system.tool.engagement_init.md` | New | `engagement_init` tool documentation |
| `agent.system.tool.findings_tracker.md` | New | `findings_tracker` tool documentation |
| `agent.system.tool.scope_check.md` | New | `scope_check` tool documentation |
| `agent.system.tool.report_generator.md` | New | `report_generator` tool documentation |
| `agent.system.tool.cve_lookup.md` | New | `cve_lookup` tool documentation |

The 5 tool prompt files are only injected when the hacker profile is active, keeping pentest-specific tool docs out of other agents' system prompts.

---

## Core System Prompts

These files form the identity and behavior of the agent.

| File | Description |
|------|-------------|
| `agent.system.main.md` | Root template — composes all other sections via `{{ include }}` |
| `agent.system.main.role.md` | Agent identity, purpose, and capabilities |
| `agent.system.main.environment.md` | Runtime environment description (OS, paths, tooling) |
| `agent.system.main.communication.md` | JSON response format and output structure |
| `agent.system.main.solving.md` | Problem-solving methodology and approach |
| `agent.system.main.tips.md` | General operation tips and preferences |
| `agent.system.main.communication_additions.md` | Voice transcription handling, message reception notes |

---

## Tool Prompts

Each tool has a corresponding prompt file describing its interface to the LLM. These are collected and injected via `agent.system.tools.md`.

| File | Tool |
|------|------|
| `agent.system.tools.md` | Container — lists all available tools via `{{tools}}` variable |
| `agent.system.tool.code_exe.md` | `code_execution_tool` — runtimes, sessions, timeout behavior |
| `agent.system.tool.response.md` | `response` — when and how to send the final answer |
| `agent.system.tool.memory.md` | `memory_save`, `memory_load`, `memory_delete`, `memory_forget` |
| `agent.system.tool.call_sub.md` | `call_subordinate` — spawning sub-agents, profile selection |
| `agent.system.tool.search_engine.md` | `search_engine` — web search via SearXNG |
| `agent.system.tool.browser.md` | `browser_agent` — Playwright browser automation |
| `agent.system.tool.input.md` | `input` — keyboard input to running terminal sessions |
| `agent.system.tool.document_query.md` | `document_query` — RAG over documents |
| `agent.system.tool.behaviour.md` | `behaviour_adjustment` — update agent behavior rules |
| `agent.system.tool.skills.md` | `skills_tool` — list and load skill files |
| `agent.system.tool.wait.md` | `wait` — pause execution for a duration |
| `agent.system.tool.scheduler.md` | `scheduler` — task scheduling system |
| `agent.system.tool.notify_user.md` | `notify_user` — push UI notifications |
| `agent.system.tool.a2a_chat.md` | `a2a_chat` — agent-to-agent FastA2A messaging |
| `agent.system.tools_vision.md` | `vision_load` — image loading for vision models |
| `agent.system.mcp_tools.md` | MCP (Model Context Protocol) tools (if configured) |

**Hacker profile tool docs** (only active when profile=hacker):

| File | Tool |
|------|------|
| `agents/hacker/prompts/agent.system.tool.engagement_init.md` | `engagement_init` |
| `agents/hacker/prompts/agent.system.tool.findings_tracker.md` | `findings_tracker` |
| `agents/hacker/prompts/agent.system.tool.scope_check.md` | `scope_check` |
| `agents/hacker/prompts/agent.system.tool.report_generator.md` | `report_generator` |
| `agents/hacker/prompts/agent.system.tool.cve_lookup.md` | `cve_lookup` |

---

## Context & Extras Prompts

Injected dynamically into every iteration by extensions.

| File | Injected by | Content |
|------|-------------|---------|
| `agent.system.datetime.md` | `_60_include_current_datetime.py` | Current date/time via `{{date_time}}` |
| `agent.system.memories.md` | `_50_recall_memories.py` | Semantically recalled memories |
| `agent.system.solutions.md` | `_50_recall_memories.py` | Past solutions recalled from memory |
| `agent.extras.agent_info.md` | `_70_include_agent_info.py` | Agent number, profile, title, context |
| `agent.extras.workdir_structure.md` | `_75_include_workdir_extras.py` | Working directory file tree |
| `agent.context.extras.md` | Extension framework | Wrapper for `extras_temporary` content |
| `agent.system.skills.md` | `_65_include_loaded_skills.py` | List of available skills |
| `agent.system.skills.loaded.md` | `_65_include_loaded_skills.py` | Currently loaded skills content |

---

## Behavior Management Prompts

Used by the `behaviour_adjustment` tool and memory system to manage agent behavior rules.

| File | Description |
|------|-------------|
| `agent.system.behaviour.md` | Wrapper that injects `{{rules}}` — the current behaviour rules |
| `agent.system.behaviour_default.md` | Default behavior preferences (e.g., prefer Linux commands over Python) |
| `agent.system.response_tool_tips.md` | Tips on using `response` tool efficiently (`§§include()` for tool output references) |
| `behaviour.merge.msg.md` | Message for utility LLM: merge new instructions with existing rules |
| `behaviour.merge.sys.md` | System prompt for utility LLM: behavior rule merging task |
| `behaviour.search.sys.md` | System prompt for utility LLM: scan conversation for behavior commands |
| `behaviour.updated.md` | Confirmation message: "Behaviour has been updated." |

---

## Framework Messages (fw.*.md)

Feedback messages generated by the framework and injected into agent history. These are NOT part of the system prompt — they appear as tool results or system messages during execution.

### Code Execution Messages

| File | When used |
|------|-----------|
| `fw.code.info.md` | Wrap code execution output: `[SYSTEM: {{info}}]` |
| `fw.code.running.md` | Shell session still running (no output yet) |
| `fw.code.reset.md` | Terminal session has been reset |
| `fw.code.no_output.md` | Command produced no output |
| `fw.code.no_out_time.md` | Timeout with no output |
| `fw.code.max_time.md` | Maximum execution time reached |
| `fw.code.pause_time.md` | Execution paused (output timeout) |
| `fw.code.pause_dialog.md` | Execution paused — dialog/prompt detected |
| `fw.code.runtime_wrong.md` | Invalid runtime specified |

### Memory Messages

| File | When used |
|------|-----------|
| `fw.memory_saved.md` | Confirmation: `Memory saved with id {{memory_id}}` |
| `fw.memories_not_found.md` | No matching memories: `No memories found for: {{query}}` |
| `fw.memories_deleted.md` | Deletion count: `"memories_deleted": "{{memory_count}}"` |
| `fw.memory.hist_suc.sys.md` | System prompt for extracting solutions from history |
| `fw.memory.hist_sum.sys.md` | System prompt for summarizing conversation for indexing |

### Agent Communication Messages

| File | When used |
|------|-----------|
| `fw.ai_response.md` | Wrap LLM response for history |
| `fw.user_message.md` | Wrap user message for history |
| `fw.initial_message.md` | Agent startup greeting |
| `fw.msg_from_subordinate.md` | Relay subordinate message: `Message from {{name}}: {{message}}` |
| `fw.intervention.md` | System intervention (user paused agent) |
| `fw.error.md` | Error notification |
| `fw.msg_critical_error.md` | Critical error message |
| `fw.msg_misformat.md` | LLM output was not valid JSON — retry |
| `fw.msg_nudge.md` | Agent looping too long without response — gentle nudge |
| `fw.msg_repeat.md` | Request to try again |
| `fw.msg_summary.md` | Message summary |
| `fw.msg_timeout.md` | Timeout notification |
| `fw.msg_truncated.md` | Output was truncated |
| `fw.msg_cleanup.md` | Request to provide JSON summary of messages |
| `fw.warning.md` | Warning message |

### History Compression Messages

| File | When used |
|------|-----------|
| `fw.topic_summary.msg.md` | Request to summarize a topic segment |
| `fw.topic_summary.sys.md` | System prompt for topic summarization |
| `fw.bulk_summary.msg.md` | Request to summarize bulk history |
| `fw.bulk_summary.sys.md` | System prompt for bulk summarization |
| `fw.rename_chat.msg.md` | Request to suggest a chat name |
| `fw.rename_chat.sys.md` | System prompt for chat renaming |

### Document & Other Messages

| File | When used |
|------|-----------|
| `fw.document_query.optmimize_query.md` | Convert natural language to vector search query |
| `fw.document_query.system_prompt.md` | System prompt for document Q&A |
| `fw.knowledge_tool.response.md` | Knowledge tool results with source URLs |
| `fw.tool_not_found.md` | Unknown tool name invoked |
| `fw.tool_result.md` | Standard tool result wrapper |
| `fw.wait_complete.md` | Wait/timer completed |
| `fw.notify_user.notification_sent.md` | Notification sent confirmation |
| `fw.hint.call_sub.md` | Hint: use `§§include()` to avoid rewriting outputs |

---

## Memory & Query Prompts

Used by the utility LLM for memory operations.

| File | Description |
|------|-------------|
| `memory.keyword_extraction.sys.md` | System prompt: extract keywords for vector query |
| `memory.keyword_extraction.msg.md` | Message template for keyword extraction |
| `memory.consolidation.sys.md` | System prompt: merge similar memories |
| `memory.consolidation.msg.md` | Message template for consolidation |
| `memory.memories_filter.sys.md` | System prompt: filter irrelevant memories |
| `memory.memories_filter.msg.md` | Message template for filtering |
| `memory.memories_query.sys.md` | System prompt: generate optimal memory query |
| `memory.memories_query.msg.md` | Message template for query generation |
| `memory.memories_sum.sys.md` | System prompt: summarize memories for storage |
| `memory.solutions_query.sys.md` | System prompt: query past solutions |
| `memory.solutions_sum.sys.md` | System prompt: summarize solutions for storage |
| `memory.recall_delay_msg.md` | Message shown during delayed memory recall |

---

## Project System Prompts

| File | Description |
|------|-------------|
| `agent.system.projects.main.md` | Explains the projects system to the agent |
| `agent.system.projects.active.md` | Injected when a project is active: path, name, instructions |
| `agent.system.projects.inactive.md` | Injected when no project is active |

---

## Browser Agent Prompt

| File | Description |
|------|-------------|
| `browser_agent.system.md` | System instructions for the browser-use subordinate agent |

---

## Secrets & Security Prompts

| File | Description |
|------|-------------|
| `agent.system.secrets.md` | Explains secret placeholder system — API keys are masked as aliases, the framework substitutes actual values before tool execution |

---

## Dynamic Loaders (.py files)

Some prompt files have companion `.py` files that generate dynamic content. The `.py` file has the same name as the `.md` file with a Python extension.

| Python file | Generates for |
|-------------|--------------|
| `agent.system.tools.py` | `{{tools}}` variable — renders all tool documentation |
| `agent.system.mcp_tools.py` | MCP tools list from configured MCP servers |

These loaders are invoked during the `system_prompt` extension hook by `_10_system_prompt.py`.
