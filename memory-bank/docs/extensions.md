# Extensions

> **Navigation:** [Index](./index.md) | [Architecture](./architecture.md) | [Agent Profiles](./agent-profiles.md) | [Tools](./tools.md) | [Prompt System](./prompt-system.md) | [Configuration](./configuration.md)

---

## Extension System Overview

Extensions are Python classes that plug into lifecycle hooks of the agent message loop. They allow adding behavior without modifying core framework code.

**Discovery:** Two directories are scanned in priority order:

```
1. agents/<profile>/extensions/<hook_name>/*.py   (profile-specific, higher priority)
2. python/extensions/<hook_name>/*.py              (framework default, lower priority)
```

**Override rule:** If a profile extension and a framework extension share the same filename, only the profile version runs.

**Execution order:** Within a hook directory, files execute in alphabetical order. The numeric prefix (`_05_`, `_10_`, `_20_`, `_50_`) controls execution sequence.

**Count:** 39+ extensions across 25 hook categories (4 additional in the hacker profile).

---

## Extension Base Class

**File:** `python/helpers/extension.py`

```python
class Extension:
    def __init__(self, agent: "Agent | None", **kwargs):
        self.agent: "Agent"
        self.kwargs: dict

    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """Core extension logic — must implement."""
```

Extensions are invoked by the framework via:

```python
await call_extensions(extension_point, agent=agent, **kwargs)
```

`**kwargs` varies by hook — see each hook section below for what is passed.

---

## LoopData Reference

Most extensions receive `loop_data: LoopData` as a kwarg. This object accumulates context for the current message loop iteration.

```python
class LoopData:
    # Prompt injection
    extras_persistent: dict[str, str]  # Survives entire session (set once in agent_init)
    extras_temporary: dict[str, str]   # Refreshed each loop iteration

    # Current iteration state
    iteration: int
    system: list[str]                  # System prompt parts
    user: list[str]                    # User message additions
    history: list[Message]

    # Tool execution state
    last_tool_output: str | None
```

**`extras_persistent` vs `extras_temporary`:**
- `extras_persistent` — Set once (e.g., in `agent_init`) and appended to every system prompt for the whole session. Used for engagement context that doesn't change.
- `extras_temporary` — Cleared and rebuilt each loop iteration. Used for recalled memories, current datetime, per-iteration engagement status.

---

## All 25 Hook Categories

### agent_init

Fires once when an `Agent` object is created.

**Framework extensions:**

| File | Purpose |
|------|---------|
| `_10_initial_message.py` | Show greeting message for top-level agent (agent.number == 0) |
| `_15_load_profile_settings.py` | Load profile-specific `settings.json` and merge into agent config |

**Hacker profile extensions:**

| File | Purpose |
|------|---------|
| [`_20_load_engagement.py`](#_20_load_engagementpy) | Scan engagements/, load most recent into `extras_persistent` |

---

### banners

Fires at UI startup to display warnings and status information.

| File | Purpose |
|------|---------|
| `_10_unsecured_connection.py` | Warn if running without HTTPS |
| `_20_missing_api_key.py` | Warn if no API keys are configured |
| `_30_system_resources.py` | Display CPU/RAM/disk status |

---

### monologue_start

Fires at the beginning of processing each user message.

| File | Purpose |
|------|---------|
| `_10_memory_init.py` | Initialize FAISS memory index for this agent |
| `_60_rename_chat.py` | Auto-rename chat topic using utility LLM if still "New Chat" |

---

### monologue_end

Fires after the response has been returned to the user.

| File | Purpose |
|------|---------|
| `_50_memorize_fragments.py` | Extract interesting facts from the conversation and save to memory (area=fragments) |
| `_51_memorize_solutions.py` | Extract problem/solution pairs and save to memory (area=solutions) |
| `_90_waiting_for_input_msg.py` | Send "waiting for input" indicator to UI |

**Hacker profile extensions:**

| File | Purpose |
|------|---------|
| [`_55_auto_save_findings.py`](#_55_auto_save_findingspy) | Scan last 5 messages for vulnerability indicators, remind to log findings |

---

### message_loop_start

Fires at the beginning of each iteration within a monologue (before system prompt assembly).

| File | Purpose |
|------|---------|
| `_10_iteration_no.py` | Increment `loop_data.iteration` counter |

---

### message_loop_end

Fires when `break_loop=True` — the monologue is ending.

| File | Purpose |
|------|---------|
| `_10_organize_history.py` | Compress old history entries to save context window |
| `_90_save_chat.py` | Persist full chat history to `usr/chats/<chat_id>.json` |

---

### message_loop_prompts_before

Fires before system prompt assembly. Used to reorganize history before the prompt is built.

| File | Purpose |
|------|---------|
| `_90_organize_history_wait.py` | Prepare history entries (handle wait states, organize sequences) |

---

### message_loop_prompts_after

Fires after system prompt assembly. Used to inject additional context.

| File | Purpose |
|------|---------|
| `_50_recall_memories.py` | Semantic search of FAISS memory for relevant entries; injects into `extras_temporary` |
| `_60_include_current_datetime.py` | Inject current date/time into `extras_temporary` |
| `_65_include_loaded_skills.py` | Inject currently loaded skills into `extras_temporary` |
| `_70_include_agent_info.py` | Inject agent profile info (name, description, context) into `extras_temporary` |
| `_75_include_workdir_extras.py` | Inject working directory structure into `extras_temporary` |

**Hacker profile extensions:**

| File | Purpose |
|------|---------|
| [`_80_include_engagement_context.py`](#_80_include_engagement_contextpy) | Inject compact engagement status into `extras_temporary` |

---

### system_prompt

Fires when the system prompt is being assembled.

| File | Purpose |
|------|---------|
| `_10_system_prompt.py` | Assemble full system prompt: main role + tool docs + MCP tools + skills + secrets + project context |
| `_20_behaviour_prompt.py` | Append current behaviour rules (from memory area=behaviour) |

---

### before_main_llm_call

Fires immediately before the LLM API call.

| File | Purpose |
|------|---------|
| `_10_log_for_stream.py` | Initialize log entry for streaming output display |

---

### reasoning_stream / reasoning_stream_chunk / reasoning_stream_end

Fires for models that return reasoning/thinking tokens (e.g., extended thinking mode).

| File | Purpose |
|------|---------|
| `_10_log_from_stream.py` | Stream reasoning tokens to UI log |
| (chunk) `_10_mask_secrets.py` | Mask API keys and secrets from reasoning output |
| (end) `_10_finalize.py` | Finalize reasoning log entry |

---

### response_stream / response_stream_chunk / response_stream_end

Fires as response tokens arrive from the LLM.

| File | Purpose |
|------|---------|
| `_10_log_from_stream.py` | Stream response tokens to UI |
| `_15_replace_include_alias.py` | Replace `{{ include }}` alias patterns in response |
| `_20_live_response.py` | Push live partial response to UI in real time |
| (chunk) `_10_mask_secrets.py` | Mask secrets from response stream |
| (end) `_10_finalize_response.py` | Finalize response log |

---

### tool_execute_before

Fires before every tool invocation. Extensions can inspect and modify tool arguments.

| File | Purpose |
|------|---------|
| `_10_unmask_secrets.py` | Substitute secret placeholders with actual values before tool runs |
| `_10_replace_last_tool_output.py` | Inject `$last_output` reference with actual previous tool output |

**Hacker profile extensions:**

| File | Purpose |
|------|---------|
| [`_05_scope_enforcement.py`](#_05_scope_enforcementpy) | Extract IPs/domains from tool args, warn if out-of-scope (runs before `_10_` files) |

---

### tool_execute_after

Fires after every tool invocation.

| File | Purpose |
|------|---------|
| `_10_mask_secrets.py` | Replace secret values with masked placeholders in tool output |

---

### hist_add_before

Fires before a message is added to agent history.

| File | Purpose |
|------|---------|
| `_10_mask_content.py` | Mask secrets in history content |

---

### hist_add_tool_result

Fires when a tool result is added to history.

| File | Purpose |
|------|---------|
| `_90_save_tool_call_file.py` | If tool output exceeds threshold, save to file and reference by path (prevents context overflow) |

---

### user_message_ui

Fires when a user sends a message via the web UI.

| File | Purpose |
|------|---------|
| `_10_update_check.py` | Check for framework updates (rate-limited) |

---

### util_model_call_before

Fires before utility LLM calls (memory summarization, keyword extraction, etc.).

| File | Purpose |
|------|---------|
| `_10_mask_secrets.py` | Mask secrets before sending to utility model |

---

### error_format

Fires when an error occurs, to format the error message.

| File | Purpose |
|------|---------|
| `_10_mask_errors.py` | Mask sensitive data from error messages before logging/display |

---

### process_chain_end

Fires when a processing chain completes.

| File | Purpose |
|------|---------|
| `_50_process_queue.py` | Process any queued messages or tasks |

---

## Hacker Profile Extensions

These 4 extensions are specific to the `hacker` profile. They live in `agents/hacker/extensions/` and only run when the hacker profile is active.

### _20_load_engagement.py

**Hook:** `agent_init`
**File:** `agents/hacker/extensions/agent_init/_20_load_engagement.py`

On hacker agent initialization, scans `engagements/` by modification time, finds the most recently modified workspace, and loads a session summary into `extras_persistent`.

**Summary injected into `extras_persistent["engagement_context"]`:**
- Target name
- Workspace path
- First 5 scope entries
- Finding counts by severity (critical/high/medium/low/info)
- RoE preview (first 3 lines)

Because `extras_persistent` is appended to every system prompt for the entire session, the hacker agent always has its engagement context available without needing to recall memory manually.

---

### _05_scope_enforcement.py

**Hook:** `tool_execute_before`
**File:** `agents/hacker/extensions/tool_execute_before/_05_scope_enforcement.py`

Runs before ALL tool executions (numeric prefix `_05_` ensures it runs before framework's `_10_` extensions).

**Logic:**
1. Extracts all IPs, CIDR ranges, domains, and URLs from tool arguments using regex
2. Loads the active engagement's `scope.txt`
3. Checks each extracted value against scope entries using `scope_check.is_in_scope()`
4. Ignores localhost addresses (127.0.0.1, ::1, 0.0.0.0, localhost)
5. If any out-of-scope targets found: logs a warning to UI + injects `extras_temporary["scope_warning"]`

**Design decision:** Warns rather than hard-blocks. Hard-blocking would break legitimate cases (NVD API responses containing target IPs, searchsploit output, etc.). The warning appears in the system prompt and the agent can make an informed decision.

**Imports from:** `python/tools/scope_check.py` (reuses `is_in_scope()` and `load_scope_entries()`)

---

### _80_include_engagement_context.py

**Hook:** `message_loop_prompts_after`
**File:** `agents/hacker/extensions/message_loop_prompts_after/_80_include_engagement_context.py`

Per-iteration refresh of engagement status. Unlike `_20_load_engagement.py` which fires once at `agent_init`, this extension runs on every message loop iteration.

**Data injected into `extras_temporary`:**
- Current target name
- Scope preview (first 3 entries + total count)
- Finding summary (counts by severity)
- Active workspace path

This keeps the agent aware of current engagement state, including finding counts that update as new findings are added during the engagement.

---

### _55_auto_save_findings.py

**Hook:** `monologue_end`
**File:** `agents/hacker/extensions/monologue_end/_55_auto_save_findings.py`

Scans the last 5 conversation history entries for vulnerability indicators after each response.

**Trigger patterns (12 regex patterns):**
- `CVE-\d{4}-\d{4,7}` — CVE identifier
- `vulnerable` — vulnerability mention
- `exploited` — exploitation success
- `RCE` — remote code execution
- `privilege escalation` / `privesc`
- `SQLi` / `SQL injection`
- `credentials found` / `credentials obtained`
- `password cracked`
- `shell obtained` / `shell access`
- `access granted`
- `uid=0` — root shell indicator
- `whoami.*root` — root confirmation

**If patterns matched AND `findings_tracker` was NOT called in the same loop:** Injects a reminder into `extras_temporary["finding_reminder"]` prompting the agent to log the finding using `findings_tracker`.

**If `findings_tracker` was already called:** No reminder (prevents spam).

---

## Writing a Custom Extension

### Minimal extension template

```python
from python.helpers.extension import Extension

class MyExtension(Extension):
    async def execute(self, loop_data=None, **kwargs):
        # Access the agent
        agent = self.agent

        # Inject into system prompt (temporary = per-iteration)
        if loop_data:
            loop_data.extras_temporary["my_key"] = "My injected content"

        # Access agent settings
        settings = agent.config.settings

        # Log to UI
        agent.context.log.log(
            type="info",
            heading="My Extension",
            content="Did something"
        )
```

### Placement

- Save the file to `agents/<profile>/extensions/<hook_name>/_NN_my_extension.py`
- The `_NN_` prefix controls execution order (lower = earlier)
- Use `_05_` to run before framework `_10_` extensions
- Use `_80_` or higher to run after all framework extensions

### Accessing context

```python
# Agent config/settings
agent.config          # AgentConfig dataclass
agent.config.settings # dict of all settings

# Engagement workspace (hacker profile)
workdir = agent.config.settings.get("workdir_path", "usr/workdir")
engagements_dir = os.path.join(workdir, "engagements")

# FAISS memory
from python.helpers.memory import Memory
memory = await Memory.get(agent)
await memory.insert_text("text to save", {"area": "main"})

# UI logging
agent.context.log.log(type="info", heading="Title", content="Message")
```

See [architecture.md#extension-system](./architecture.md#extension-system) for how extensions are discovered and loaded.
