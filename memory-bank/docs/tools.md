# Tools

> **Navigation:** [Index](./index.md) | [Architecture](./architecture.md) | [Agent Profiles](./agent-profiles.md) | [Extensions](./extensions.md) | [Prompt System](./prompt-system.md) | [Configuration](./configuration.md)

---

## Tool System Overview

A **tool** is a Python class that the LLM can invoke by name. When the LLM outputs a JSON response with `tool_name` and `tool_args`, the framework dispatches to the matching class, executes it, and returns the result to the agent's history.

**Discovery:** The framework scans `python/tools/` at startup. All `.py` files containing a class that inherits from `Tool` are registered by filename (without `.py`). Profile-specific tools in `agents/<profile>/tools/` are also discovered if present. Files ending in `._py` are disabled and not loaded.

**Count:** 24 active tools (5 new pentest tools, 19 framework tools).

---

## Tool Base Class

**File:** `python/helpers/tool.py`

```python
class Tool:
    def __init__(self, agent: Agent, name: str, method: str | None,
                 args: dict[str, str], message: str,
                 loop_data: LoopData | None, **kwargs)

    @abstractmethod
    async def execute(self, **kwargs) -> Response:
        """Core logic — must be implemented."""

    async def before_execution(self, **kwargs):
        """Called before execute(). Default: logs tool name + args."""

    async def after_execution(self, response: Response, **kwargs):
        """Called after execute(). Default: adds result to agent history."""

    def set_progress(self, content: str | None):
        """Set progress indicator text in UI."""

    def add_progress(self, content: str | None):
        """Append to progress indicator text."""
```

**Response dataclass:**

```python
@dataclass
class Response:
    message: str                         # Text returned to agent history
    break_loop: bool                     # True = terminate message loop
    additional: dict[str, Any] | None = None  # Optional metadata
```

Every tool's `execute()` must return a `Response`. If `break_loop=True`, the `monologue()` loop stops and the response is returned to the user.

---

## Pentest Tools

These 5 tools were added as part of the `agent-zero-sec` project. They live in `python/tools/` but their documentation prompts live in `agents/hacker/prompts/` so only the hacker profile's system prompt includes their usage instructions.

### engagement_init

**File:** `python/tools/engagement_init.py`
**Prompt:** `agents/hacker/prompts/agent.system.tool.engagement_init.md`

Initializes and manages penetration test engagement workspaces.

| Action | Parameters | Description |
|--------|-----------|-------------|
| `init` | `target`, `scope`, `roe` | Create workspace directory tree, write scope/RoE files |
| `list` | — | List all engagement directories under `engagements/` |
| `status` | — | Show active engagement details (loads from memory) |

**Workspace layout created by `init`:**

```
usr/workdir/engagements/<target>/
├── scope.txt          # One IP/CIDR/domain per line
├── roe.txt            # Rules of engagement
├── findings.json      # Empty findings array []
├── engagement.json    # Metadata: target, created, scope_count
├── loot/              # Extracted credentials, hashes, files
├── screenshots/       # Evidence screenshots
├── scans/             # Raw tool output (nmap XML, etc.)
└── reports/           # Generated reports
```

After `init`, saves a summary to FAISS memory so it can be recalled across sessions. Uses `settings.get_settings()["workdir_path"]` for the base path.

---

### findings_tracker

**File:** `python/tools/findings_tracker.py`
**Prompt:** `agents/hacker/prompts/agent.system.tool.findings_tracker.md`

CRUD operations for structured vulnerability findings.

| Action | Parameters | Description |
|--------|-----------|-------------|
| `add_finding` | See schema below | Add new vulnerability finding |
| `list_findings` | `severity` (optional filter) | List all findings, sorted by severity |
| `get_finding` | `id` | Get single finding details |
| `update_finding` | `id`, + fields to update | Patch a finding |
| `export_findings` | — | Return all findings as JSON (for report_generator) |

**Finding schema:**

```json
{
  "id": "auto-generated UUID",
  "title": "SQL Injection in login form",
  "severity": "critical|high|medium|low|informational",
  "cvss_score": 9.8,
  "host": "10.10.10.5",
  "port": 80,
  "service": "http",
  "cve": "CVE-2023-XXXXX",
  "description": "...",
  "steps_to_reproduce": "...",
  "evidence": "...",
  "remediation": "...",
  "status": "open|confirmed|resolved",
  "created": "ISO timestamp",
  "updated": "ISO timestamp"
}
```

**Severity sort order:** `critical (0) → high (1) → medium (2) → low (3) → informational (4)`

Findings are stored at `engagements/<target>/findings.json` and read/written on each call (no in-memory state).

---

### scope_check

**File:** `python/tools/scope_check.py`
**Prompt:** `agents/hacker/prompts/agent.system.tool.scope_check.md`

Validates whether a target is within the authorized engagement scope.

| Action | Parameters | Description |
|--------|-----------|-------------|
| `check` | `value` (IP, domain, or URL) | Check if value is in scope |
| `show` | — | Display all scope entries from scope.txt |

**Matching logic** (in priority order):

1. Strips URL scheme and path to extract host
2. If IP: checks against individual IPs and CIDR ranges (via `ipaddress` module)
3. If domain: checks exact match, wildcard `*.domain`, parent domain

**Exported functions** (reused by scope enforcement extension):

```python
def is_in_scope(value: str, scope_entries: list[str]) -> tuple[bool, str]:
    """Returns (in_scope, matched_rule)"""

def load_scope_entries(path: str) -> list[str]:
    """Load scope.txt entries, strip comments and blank lines"""
```

See [extensions.md#_05_scope_enforcement](./extensions.md#_05_scope_enforcementpy) for how the extension calls these functions.

---

### report_generator

**File:** `python/tools/report_generator.py`
**Prompt:** `agents/hacker/prompts/agent.system.tool.report_generator.md`

Generates professional penetration test reports from `findings.json`.

| Action | Parameters | Description |
|--------|-----------|-------------|
| `generate` | `format`, `title`, `client`, `tester` | Produce full report |
| `preview` | — | Executive summary only |

**`format` options:**

| Format | Output | Notes |
|--------|--------|-------|
| `markdown` | `.md` file | Always available |
| `html` | `.html` file | CSS-styled, dark theme |
| `pdf` | `.pdf` file | Via weasyprint; falls back to HTML if weasyprint unavailable |

**Report structure:**

1. Cover page (title, client, tester, date, classification)
2. Executive summary (risk profile, key findings count by severity)
3. Scope and methodology
4. Risk rating matrix (CVSS 3.1 scale)
5. Findings (sorted by CVSS score descending, each with description, PoC steps, evidence, remediation)
6. Appendix (tool list, raw scan references)

Reports are saved to `engagements/<target>/reports/`.

---

### cve_lookup

**File:** `python/tools/cve_lookup.py`
**Prompt:** `agents/hacker/prompts/agent.system.tool.cve_lookup.md`

Research CVEs and find exploitation resources.

| Action | Parameters | Description |
|--------|-----------|-------------|
| `lookup_cve` | `cve_id` | Get full CVE details from NVD |
| `search_product` | `product`, `version` (optional) | Search CVEs by product name |

**Data sources:**

1. **NVD API v2.0** — `https://services.nvd.nist.gov/rest/json/cves/2.0` (primary)
2. **SearXNG** — self-hosted search engine (fallback if NVD API unavailable)

**Output includes:** CVSS score, CVSS vector string, CWE, descriptions, published/modified dates, references, plus follow-up commands to run (`searchsploit`, `msfconsole search`, GitHub search URL).

**HTTP client:** `aiohttp` (async). No NVD API key required; add `nvd_api_key` to `usr/secrets.env` for higher rate limits.

---

## Standard Framework Tools

### response

**File:** `python/tools/response.py`
**Profile override:** `agents/agent0/tools/response.py` (slightly different formatting)

Terminates the message loop and returns the final answer to the user. The LLM calls this when it has finished its task. `break_loop=True`.

| Parameter | Description |
|-----------|-------------|
| `text` / `message` | The response content |

---

### call_subordinate

**File:** `python/tools/call_subordinate.py`

Spawns a subordinate agent with a given profile and message. The subordinate runs its own full `monologue()` loop and returns its result as a tool result in the parent's history.

| Parameter | Description |
|-----------|-------------|
| `message` | Task description for the subordinate |
| `reset` | `"true"` to destroy and recreate the subordinate |
| `agent_profile` | Profile name (`recon`, `exploit-dev`, `reporter`, etc.) |

**Key behavior:**
- Subordinates share the same `AgentContext` (log, UI connection)
- Subordinates have their own `history` and `memory_subdir`
- `agent.number` increments with depth (top-level = 0)
- After the subordinate finishes, the topic is "sealed" for compression

See [agent-profiles.md](./agent-profiles.md) for delegation examples.

---

### code_execution_tool

**File:** `python/tools/code_execution_tool.py`

Execute code and shell commands. The primary tool for running recon tools, exploits, and post-exploitation commands.

| Runtime | Description |
|---------|-------------|
| `python` | Persistent IPython session |
| `nodejs` | Node.js execution |
| `terminal` | Bash shell (persistent session) |
| `output` | Retrieve last output without executing |
| `reset` | Kill and restart a session |

| Parameter | Description |
|-----------|-------------|
| `runtime` | One of the runtimes above |
| `session` | Session number (0–N). Default 0 |
| `code` | Code or command to execute |

**Key behaviors:**
- Sessions are persistent — shell state carries over between calls
- Output is streamed to the UI in real time
- Dialog detection: pauses when Y/N prompts are detected
- Prompt detection: returns when shell prompt is recognized
- Timeout settings: `first_output_timeout` (30s), `between_output_timeout` (15s), `max_exec_timeout` (180s)
- Output truncated at ~1MB via `truncate_text_agent`
- Execution target: configured via `shell_interface` setting (`local` or `ssh`)

---

### input

**File:** `python/tools/input.py`

Forward keyboard input to a running code execution session (e.g., answer a Y/N prompt).

| Parameter | Description |
|-----------|-------------|
| `session` | Session number to send input to |
| `keyboard_input` | Text to send |

---

### memory_save

**File:** `python/tools/memory_save.py`

Save information to FAISS vector memory for later recall.

| Parameter | Description |
|-----------|-------------|
| `text` | Content to save |
| `area` | `main` / `fragments` / `solutions` (default: `main`) |
| `**kwargs` | Additional metadata fields |

Returns the assigned `memory_id`.

---

### memory_load

**File:** `python/tools/memory_load.py`

Search memory by semantic similarity.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `query` | — | Search query |
| `threshold` | 0.7 | Minimum similarity score |
| `limit` | 10 | Max results |
| `filter` | — | Metadata filter expression |

Returns top-k matching memory entries as formatted text.

---

### memory_delete

**File:** `python/tools/memory_delete.py`

Delete specific memory entries by ID.

| Parameter | Description |
|-----------|-------------|
| `ids` | Comma-separated memory IDs to delete |

---

### memory_forget

**File:** `python/tools/memory_forget.py`

Delete memory entries matching a semantic query.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `query` | — | Semantic query to match |
| `threshold` | 0.7 | Similarity threshold |
| `filter` | — | Metadata filter |

---

### search_engine

**File:** `python/tools/search_engine.py`

Web search via SearXNG (self-hosted). Returns 10 results (title, URL, content snippet).

| Parameter | Description |
|-----------|-------------|
| `query` | Search query |

**Note:** Used by `_05_scope_enforcement` to detect network-touching tools.

---

### browser_agent

**File:** `python/tools/browser_agent.py`

Playwright browser automation via the `browser-use` framework.

| Parameter | Description |
|-----------|-------------|
| `message` | Task description for the browser agent |
| `reset` | `true` to restart browser session |

**Key behavior:**
- Uses the configured `browser_model` (vision-capable LLM)
- Screenshots are captured and analyzed
- Secrets are masked from screenshots
- Timeout: 300 seconds (5 minutes)
- Returns: task result, page title, summary

---

### vision_load

**File:** `python/tools/vision_load.py`

Load and compress images for LLM vision input.

| Parameter | Description |
|-----------|-------------|
| `paths` | List of image file paths |

Compresses to max 768K pixels at 75% JPEG quality. Returns base64-encoded data. Estimated 1500 tokens per image.

---

### document_query

**File:** `python/tools/document_query.py`

Query documents (PDF, text, web URLs) using RAG.

| Parameter | Description |
|-----------|-------------|
| `document` | URI or list of URIs |
| `query` / `queries` | Question to answer against the document |

No `query` = returns full content. Multiple queries run sequentially.

---

### skills_tool

**File:** `python/tools/skills_tool.py`

Manage SKILL.md skills in context.

| Method | Description |
|--------|-------------|
| `list` | Show available skills with truncated descriptions (200 chars) |
| `load` | Load a skill into the system prompt context |

Max 5 skills loaded simultaneously.

See [memory-and-skills.md](./memory-and-skills.md#skills-system) for the SKILL.md format.

---

### a2a_chat

**File:** `python/tools/a2a_chat.py`

Agent-to-Agent communication via FastA2A protocol (peer messaging, not parent-child).

| Parameter | Description |
|-----------|-------------|
| `agent_url` | URL of the remote agent |
| `message` | Message to send |
| `attachments` | Optional file attachments |
| `reset` | `true` to start a new session |

Sessions are cached per agent URL.

---

### notify_user

**File:** `python/tools/notify_user.py`

Push a notification to the UI.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `message` | — | Notification content |
| `title` | — | Notification title |
| `detail` | — | Extended detail text |
| `type` | `INFO` | `INFO` / `WARNING` / `ERROR` / `SUCCESS` |
| `priority` | `HIGH` | Priority level |
| `timeout` | 30 | Auto-dismiss timeout (seconds) |

---

### behaviour_adjustment

**File:** `python/tools/behaviour_adjustment.py`

Dynamically update the agent's behavior rules.

| Parameter | Description |
|-----------|-------------|
| `adjustments` | Natural language description of desired rule changes |

Uses the utility LLM to merge adjustments into current `behaviour.md`. Stores the result in memory (area=`behaviour`).

---

### scheduler

**File:** `python/tools/scheduler.py`

Task scheduling system.

| Method | Description |
|--------|-------------|
| `list_tasks` | Show all scheduled/adhoc/planned tasks |
| `find_task_by_name` | Look up task by name |
| `show_task` | Get task details |
| `run_task` | Execute a task immediately |
| `delete_task` | Remove a task |
| `create_scheduled_task` | Create recurring task (cron-like) |
| `create_adhoc_task` | Create one-time task |
| `create_planned_task` | Create future-dated task |
| `wait_for_task` | Block until task completes |

---

### wait

**File:** `python/tools/wait.py`

Pause execution for a duration or until a timestamp.

| Parameter | Description |
|-----------|-------------|
| `seconds` / `minutes` / `hours` / `days` | Duration |
| `until` | ISO 8601 timestamp |

Target time cannot be in the past. Uses `managed_wait()` which is interruptible.

---

### unknown

**File:** `python/tools/unknown.py`

Fallback tool. Invoked when the LLM outputs an unrecognized `tool_name`. Returns an error message prompting the LLM to use a valid tool.

---

## Tool Prompt Documentation

Each tool has a corresponding markdown prompt file in `prompts/` that is included in the system prompt. The file describes the tool's interface, parameters, and examples for the LLM.

Naming convention: `agent.system.tool.<toolname>.md`

Profile overrides follow the same pattern: `agents/<profile>/prompts/agent.system.tool.<toolname>.md`

The hacker profile adds tool docs for all 5 pentest tools:

```
agents/hacker/prompts/
├── agent.system.tool.engagement_init.md
├── agent.system.tool.findings_tracker.md
├── agent.system.tool.scope_check.md
├── agent.system.tool.report_generator.md
└── agent.system.tool.cve_lookup.md
```

These files are only injected when the `hacker` profile is active, which prevents other agents from knowing about or attempting to use pentest-specific tools.

See [prompt-system.md](./prompt-system.md#tool-prompts) for the full list of tool prompt files.
