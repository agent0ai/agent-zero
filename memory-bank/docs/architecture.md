# Architecture

> **Navigation:** [Index](./index.md) | [Agent Profiles](./agent-profiles.md) | [Tools](./tools.md) | [Extensions](./extensions.md) | [Prompt System](./prompt-system.md) | [Memory & Skills](./memory-and-skills.md) | [Configuration](./configuration.md)

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Web UI (port 80)                         │
│              Flask + Uvicorn + SocketIO (run_ui.py)             │
└────────────────────────────┬────────────────────────────────────┘
                             │ WebSocket / REST
┌────────────────────────────▼────────────────────────────────────┐
│                      AgentContext                               │
│   (shared: log, history, UI connection, job queue, chat data)  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Agent (agent.py)                       │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐  │  │
│  │  │  Prompts │  │  Memory  │  │  Tools   │  │ Extens. │  │  │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬────┘  │  │
│  │       │              │              │              │        │  │
│  │  ┌────▼──────────────▼──────────────▼──────────────▼────┐ │  │
│  │  │                  monologue() loop                     │ │  │
│  │  │  1. extensions → 2. system prompt → 3. LLM call →   │ │  │
│  │  │  4. parse tool → 5. execute tool → 6. add history →  │ │  │
│  │  │  7. repeat until response_tool called                 │ │  │
│  │  └───────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  Subordinate agents (same structure, parent = superior agent)  │
└─────────────────────────────────────────────────────────────────┘
                             │
            ┌────────────────┼─────────────────┐
            ▼                ▼                 ▼
     Code execution    FAISS memory       LiteLLM
    (local shell /    (SentenceTransf.)  (25+ providers)
       SSH/Docker)
```

---

## Agent Message Loop

The core of the system is `Agent.monologue()` in `agent.py`. Every time a user sends a message, it enters this loop and runs until `response_tool` is called with `break_loop=True`.

### Step-by-step

```
User message arrives
        │
        ▼
[message_loop_start extensions]
  └── _10_iteration_no.py — tracks iteration count
        │
        ▼
[message_loop_prompts_before extensions]
  └── _90_organize_history_wait.py
        │
        ▼
[system_prompt extensions]
  └── _10_system_prompt.py — assembles full system prompt:
        main prompt + tools + MCP tools + skills + secrets + project
  └── _20_behaviour_prompt.py — appends behaviour rules
        │
        ▼
[message_loop_prompts_after extensions]
  ├── _50_recall_memories.py — injects relevant memories
  ├── _60_include_current_datetime.py
  ├── _65_include_loaded_skills.py
  ├── _70_include_agent_info.py
  ├── _75_include_workdir_extras.py
  ├── _80_include_engagement_context.py  ← hacker profile only
  └── _91_recall_wait.py
        │
        ▼
[before_main_llm_call extensions]
  └── _10_log_for_stream.py
        │
        ▼
LLM call (streaming)
  ├── [reasoning_stream extensions] — if model has reasoning tokens
  └── [response_stream extensions]  — live response to UI
        │
        ▼
Parse JSON from LLM output
  └── extract: thoughts, headline, tool_name, tool_args
        │
        ▼
[tool_execute_before extensions]
  ├── _05_scope_enforcement.py  ← hacker profile only
  ├── _10_replace_last_tool_output.py
  └── _10_unmask_secrets.py
        │
        ▼
Dispatch tool (tool_name → python/tools/<name>.py)
  └── tool.before_execution() → tool.execute() → tool.after_execution()
        │
        ▼
[tool_execute_after extensions]
  └── _10_mask_secrets.py
        │
        ▼
[hist_add_tool_result extensions]
  └── _90_save_tool_call_file.py
        │
        ▼
Add tool result to agent history
        │
        ▼
    break_loop?
    ├── YES → [message_loop_end extensions]
    │              ├── _10_organize_history.py
    │              └── _90_save_chat.py
    │          → [monologue_end extensions]
    │              ├── _50_memorize_fragments.py
    │              ├── _51_memorize_solutions.py
    │              ├── _55_auto_save_findings.py  ← hacker only
    │              └── _90_waiting_for_input_msg.py
    │          → return response to user
    │
    └── NO  → loop back to system_prompt assembly
```

**Iteration limit:** If the agent loops too many times without calling `response`, the framework nudges it with `fw.msg_nudge.md`.

---

## Extension System

Extensions are Python classes that plug into lifecycle hooks. They are auto-discovered from two sources in priority order:

```
1. agents/<profile>/extensions/<hook>/*.py   (profile-specific, higher priority)
2. python/extensions/<hook>/*.py              (framework default, lower priority)
```

**Override mechanism:** If a profile extension has the same filename as a framework extension, the profile version wins. This is how `agents/hacker/extensions/` overrides specific framework behaviors without modifying framework files.

**Execution order:** Within a hook directory, files execute in alphabetical order. The numeric prefix (`_10_`, `_20_`, `_50_`) controls order. The hacker scope enforcement uses `_05_` to run before all framework `_10_` extensions.

**All 25 hook categories:**

| Hook | When it fires | Key use |
|------|--------------|---------|
| `agent_init` | Agent object created | Load profile settings, show initial message |
| `monologue_start` | Before each user message processing | Init memory |
| `monologue_end` | After response returned to user | Memorize fragments, auto-save findings |
| `message_loop_start` | Each iteration start | Track iteration number |
| `message_loop_end` | Loop ends (break_loop=True) | Organize history, save chat |
| `message_loop_prompts_before` | Before prompt assembly | History organization |
| `message_loop_prompts_after` | After prompt assembly | Inject memory, datetime, engagement context |
| `system_prompt` | System prompt building | Assemble main prompt + tools + skills |
| `before_main_llm_call` | Before LLM API call | Set up streaming log |
| `reasoning_stream` | Reasoning token arrives | Log to UI |
| `reasoning_stream_chunk` | Per reasoning chunk | Mask secrets |
| `reasoning_stream_end` | Reasoning stream done | Final masking |
| `response_stream` | Response token arrives | Live UI display |
| `response_stream_chunk` | Per response chunk | Mask secrets |
| `response_stream_end` | Response stream done | Finalize log |
| `hist_add_before` | Before adding to history | Mask content |
| `hist_add_tool_result` | Tool result added to history | Save to file if long |
| `tool_execute_before` | Before any tool runs | Scope enforcement, unmask secrets |
| `tool_execute_after` | After any tool runs | Mask secrets in output |
| `user_message_ui` | User sends message via UI | Check for updates |
| `util_model_call_before` | Before utility LLM call | Mask secrets |
| `banners` | UI startup | Connection warnings, API key alerts |
| `error_format` | Error encountered | Mask sensitive error data |
| `process_chain_end` | Processing chain complete | Process message queue |

See [extensions.md](./extensions.md) for the full extension reference.

---

## Tool Dispatch

When the LLM outputs a JSON response with `tool_name`, the framework:

1. Looks up the class in `python/tools/<tool_name>.py`
2. Also checks profile-specific `agents/<profile>/tools/<tool_name>.py` if present
3. Instantiates the class: `Tool(agent, name, method, args, message, loop_data)`
4. Calls `before_execution()` → `execute(**tool_args)` → `after_execution(response)`
5. `execute()` must return `Response(message=str, break_loop=bool)`
6. If `break_loop=True`, the monologue loop terminates

**Tool discovery:** `python/tools/` is scanned at startup. All classes inheriting from `Tool` are registered by filename (minus `.py`). Profile-specific tools in `agents/<profile>/tools/` are also discovered if present.

See [tools.md](./tools.md) for all tools.

---

## Prompt Assembly

The system prompt is assembled fresh on every message loop iteration.

### Assembly chain

```
agent.read_prompt("agent.system.main.md")
    │
    ├── {{ include "agent.system.main.role.md" }}
    │       → agents/<profile>/prompts/agent.system.main.role.md  (if exists)
    │       → prompts/agent.system.main.role.md                   (fallback)
    │
    ├── {{ include "agent.system.main.environment.md" }}
    ├── {{ include "agent.system.main.communication.md" }}
    ├── {{ include "agent.system.main.solving.md" }}
    └── {{ include "agent.system.main.tips.md" }}

+ agent.read_prompt("agent.system.tools.md")    ← tool docs
+ MCP tools prompt (if MCP servers configured)
+ Skills prompt (available skills list)
+ Secrets + variables
+ Project context

+ loop_data.extras_persistent   ← persistent per session (e.g. engagement context)
+ loop_data.extras_temporary    ← refreshed each iteration (e.g. recalled memories)
```

### Profile override resolution

For every `{{ include "filename.md" }}`, the framework searches:
```
1. agents/<profile>/prompts/filename.md   (profile override wins)
2. prompts/filename.md                    (global default)
```

This means a profile only needs to place a file with the same name to override any global prompt. The `hacker` profile overrides `role.md` and `environment.md`, and adds `solving.md` and `communication.md`.

See [prompt-system.md](./prompt-system.md) for all 102 prompt files.

---

## Multi-Agent Communication

Agents form a parent-child hierarchy. The `call_subordinate` tool spawns child agents.

```
Agent 0 (profile: hacker, number: 0)
    │
    ├── call_subordinate(profile="recon")
    │       └── Agent 1 (profile: recon, number: 1)
    │               └── runs monologue, returns result
    │
    └── call_subordinate(profile="exploit-dev")
            └── Agent 2 (profile: exploit-dev, number: 2)
```

**Key properties:**
- Subordinates share the same `AgentContext` (same log, same UI connection)
- Subordinates have their own `history` and `memory_subdir`
- A subordinate's response appears as a tool result in the parent's history
- `Agent.number` increments with depth (0 = top-level user-facing agent)
- Only `Agent.number == 0` shows the initial greeting message

**Agent-to-Agent (A2A):** For direct peer messaging between agents, the `a2a_chat` tool provides a separate communication channel independent of the subordinate hierarchy.

See [agent-profiles.md](./agent-profiles.md) for profiles that can be delegated to.

---

## LLM Integration

Agent Zero uses LiteLLM to abstract 25+ LLM providers. Four distinct model roles:

| Role | Purpose | Default |
|------|---------|---------|
| **Chat model** | Main agent reasoning + tool calls | `anthropic/claude-sonnet-4.6` via openrouter |
| **Utility model** | Memory summarization, query generation, topic renaming | `google/gemini-3-flash-preview` via openrouter |
| **Embedding model** | FAISS vector embeddings for memory search | `sentence-transformers/all-MiniLM-L6-v2` via huggingface |
| **Browser model** | Vision-capable model for browser screenshot analysis | `anthropic/claude-sonnet-4.6` via openrouter |

Each model has independent provider, name, API base, context length, rate limit, and kwargs configuration.

See [configuration.md](./configuration.md) for the full model settings reference.

---

## Data Persistence

| What | Where | Format |
|------|-------|--------|
| Chat history | `usr/chats/<chat_id>.json` | JSON |
| Vector memory | `usr/memory/<subdir>/` | FAISS index + metadata JSON |
| Agent settings | `usr/settings.json` | JSON |
| Engagement workspace | `usr/workdir/engagements/<target>/` | Directory tree |
| Findings | `usr/workdir/engagements/<target>/findings.json` | JSON array |
| Reports | `usr/workdir/engagements/<target>/reports/` | md / html / pdf |
| Skills | `usr/skills/*.md` | Markdown with YAML frontmatter |
| Knowledge | `usr/knowledge/` | Text / PDF / Markdown |
| Behaviour rules | `usr/memory/` (area=behaviour) | Vector memory entry |
